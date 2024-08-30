"""
Database code
"""

import sqlite3
from datetime import date

from language_practice.config import Config, Entry, WordRepetition


class SqliteHandle:
    """
    Handler for sqlite operations.
    """

    FLASHCARDS_SCHEMA = "file_name TEXT PRIMARY KEY, lang TEXT"
    WORD_SCHEMA = (
        "word TEXT PRIMARY KEY, definition TEXT, gender TEXT, aspect TEXT, "
        "usage TEXT, part_of_speech TEXT, easiness_factor REAL, num_correct INTEGER, "
        "in_n_days INTEGER, date_of_next TEXT, review NUMERIC, file_name TEXT"
    )

    def __init__(self, db: str):
        self.conn = sqlite3.connect(db)
        self.cursor = self.conn.cursor()

        self.create_table_idempotent("flashcard_sets", SqliteHandle.FLASHCARDS_SCHEMA)

    def create_table_idempotent(self, name: str, schema: str):
        """
        Create a table only if it doesn't exist
        """
        self.cursor.execute(f"CREATE TABLE IF NOT EXISTS '{name}' ({schema});")

    def recreate_table(self, name: str, schema: str):
        """
        Recreate a table even if it exists
        """
        self.drop_table(name)
        self.cursor.execute(f"CREATE TABLE '{name}' ({schema});")

    def delete(self, name: str, search: str):
        """
        Delete entry.
        """
        self.cursor.execute(f"DELETE FROM '{name}' WHERE {search};")

    def drop_table(self, name: str):
        """
        Drop table.
        """
        res = self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        if (name,) in res.fetchall():
            self.cursor.execute(f"DROP TABLE '{name}';")

    def insert_into(self, name: str, columns: str, values: str):
        """
        Insert into table.
        """
        self.cursor.execute(f"INSERT INTO '{name}' ({columns}) VALUES({values});")

    #  pylint: disable=too-many-nested-blocks
    #  pylint: disable=too-many-statements
    #  pylint: disable=too-many-branches
    #  pylint: disable=too-many-locals
    def import_set(
        self, file_name: str, config: Config, scraped: dict[str, list[list[list[str]]]]
    ):
        """
        Import set into database.
        """
        lang = config.get_lang()
        columns = ["file_name"]
        values = [f"'{file_name}'"]
        if lang is not None:
            columns.append("lang")
            values.append(f"'{lang}'")
        self.insert_into("flashcard_sets", ", ".join(columns), ", ".join(values))
        self.create_table_idempotent(
            "words",
            SqliteHandle.WORD_SCHEMA,
        )
        for entry in iter(config):
            word = entry.get_word()
            definition = entry.get_definition()
            gender = entry.get_gender()
            aspect = entry.get_aspect()
            usage = entry.get_usage()
            part_of_speech = entry.get_part_of_speech()
            charts = entry.get_charts()
            repetition = entry.get_repetition()
            easiness_factor = repetition.get_easiness_factor()
            num_correct = repetition.get_num_correct()
            in_n_days = repetition.get_in_n_days()
            date_of_next = repetition.get_date_of_next()
            review = 1 if repetition.get_review() else 0
            if charts is None:
                charts = scraped.get(entry.get_word(), None)
            else:
                charts = [charts]

            if charts is not None:
                for i, chart in enumerate(charts):
                    max_len = max(map(len, chart))
                    schema = ", ".join(
                        [f"{chr(i + 97)} TEXT" for i in range(0, max_len)]
                    )
                    self.recreate_table(f"{word}-{i}", schema)
                    for row in chart:
                        columns = []
                        values = []
                        for j in range(0, max_len):
                            try:
                                val = row[j]
                                val = val.replace("'", "''")
                            except IndexError:
                                pass
                            else:
                                columns.append(chr(j + 97))
                                values.append(f"'{val}'")
                        self.insert_into(
                            f"{word}-{i}", ", ".join(columns), ", ".join(values)
                        )

            columns = [
                "word",
                "definition",
                "easiness_factor",
                "num_correct",
                "in_n_days",
                "date_of_next",
                "review",
                "file_name",
            ]
            values = [
                f"'{word}'",
                f"'{definition}'",
                f"{easiness_factor}",
                f"{num_correct}",
                f"{in_n_days}",
                f"'{date_of_next}'",
                f"{review}",
                f"'{file_name}'",
            ]
            if gender is not None:
                columns.append("gender")
                values.append(f"'{gender}'")
            if aspect is not None:
                columns.append("aspect")
                values.append(f"'{aspect}'")
            if usage is not None:
                columns.append("usage")
                values.append(f"'{usage}'")
            if part_of_speech is not None:
                columns.append("part_of_speech")
                values.append(f"'{part_of_speech}'")
            self.insert_into("words", ", ".join(columns), ", ".join(values))

    def delete_set(self, file_name: str):
        """
        Delete a set from the database.
        """
        words = self.cursor.execute(
            f"SELECT word FROM 'words' WHERE file_name = '{file_name}';"
        ).fetchall()
        res = self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        names = res.fetchall()
        names_to_drop = [
            name[0] for name in names for word in words if name[0].startswith(word)
        ]
        for name in names_to_drop:
            self.drop_table(name)
        self.drop_table(file_name)
        self.delete("words", f"file_name = '{file_name}'")
        self.delete("flashcard_sets", f"file_name = '{file_name}'")

    def load_config(self, file_name: str) -> Config:
        """
        Load config from database.
        """
        res = self.cursor.execute(
            f"SELECT lang FROM flashcard_sets WHERE file_name = '{file_name}';"
        )
        lang = res.fetchall()[0]

        res = self.cursor.execute(
            f"SELECT word, definition, gender, aspect, usage, part_of_speech, "
            f"easiness_factor, num_correct, in_n_days, date_of_next, review "
            f"FROM 'words' WHERE file_name = '{file_name}';"
        )
        entries = res.fetchall()

        res = self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        table_names = res.fetchall()

        loaded_entries = []
        for entry in entries:
            (
                word,
                definition,
                gender,
                aspect,
                usage,
                part_of_speech,
                easiness_factor,
                num_correct,
                in_n_days,
                date_of_next,
                review,
            ) = entry
            date_of_next = date.fromisoformat(date_of_next)
            review = review != 0

            charts = []
            names_to_get = [name[0] for name in table_names if name[0].startswith(word)]
            for name in names_to_get:
                res = self.cursor.execute(f"SELECT * FROM '{name}';")
                chart = res.fetchall()
                charts.append(chart)

            if date.today() >= date_of_next or review:
                loaded_entries.append(
                    Entry(
                        word,
                        definition,
                        gender,
                        aspect,
                        usage,
                        part_of_speech,
                        charts,
                        WordRepetition(
                            easiness_factor,
                            num_correct,
                            in_n_days,
                            date_of_next,
                            review,
                        ),
                    )
                )

        return Config(lang, loaded_entries)

    def update_config(self, word: str, repetition: WordRepetition):
        """
        Update config for word.
        """
        easiness_factor = repetition.get_easiness_factor()
        num_correct = repetition.get_num_correct()
        in_n_days = repetition.get_in_n_days()
        date_of_next = str(repetition.get_date_of_next())
        review = 1 if repetition.get_review() else 0
        self.cursor.execute(
            f"UPDATE words SET easiness_factor = {easiness_factor}, num_correct = "
            f"{num_correct}, in_n_days = {in_n_days}, date_of_next = '{date_of_next}', "
            f"review = {review} WHERE word = '{word}';"
        )

    def get_all_sets(self) -> list[str]:
        """
        Get all flashcard sets from database.
        """
        res = self.cursor.execute("SELECT * FROM flashcard_sets;")
        return [entry[0] for entry in res.fetchall()]

    def close(self):
        """
        Close connection to database.
        """
        self.conn.commit()
        self.cursor.close()
        self.conn.close()
