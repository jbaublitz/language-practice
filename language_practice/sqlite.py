"""
Database code
"""

import uuid
import sqlite3
from datetime import date

from language_practice.config import Config, Entry, WordRepetition


class SqliteHandle:
    """
    Handler for sqlite operations.
    """

    FLASHCARDS_TABLE_NAME = "flashcard_sets"
    FLASHCARDS_SCHEMA = (
        "id INTEGER PRIMARY KEY AUTOINCREMENT, file_name TEXT, lang TEXT"
    )
    WORD_TABLE_NAME = "words"
    WORD_SCHEMA = (
        "word TEXT PRIMARY KEY NOT NULL, definition TEXT NOT NULL, gender TEXT, "
        "aspect TEXT, usage TEXT, part_of_speech TEXT, easiness_factor REAL, "
        "num_correct INTEGER, in_n_days INTEGER, date_of_next TEXT, review NUMERIC, "
        "flashcard_set_id INTEGER, table_uuids TEXT"
    )

    def __init__(self, db: str):
        self.conn = sqlite3.connect(db)
        self.cursor = self.conn.cursor()

        self.create_table_idempotent(
            SqliteHandle.FLASHCARDS_TABLE_NAME, SqliteHandle.FLASHCARDS_SCHEMA
        )

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
        self.cursor.execute(
            f"INSERT OR IGNORE INTO '{name}' ({columns}) VALUES({values});"
        )

    def update(self, name: str, set_statements: str, condition: str):
        """
        Insert into table.
        """
        self.cursor.execute(f"UPDATE '{name}' SET {set_statements} WHERE {condition};")

    def get_id_from_file_name(self, file_name: str) -> int | None:
        """
        Checks whether the flashcard set already exists.
        """
        table_name = SqliteHandle.FLASHCARDS_TABLE_NAME
        res = self.cursor.execute(
            f"SELECT id FROM {table_name} WHERE file_name = '{file_name}';"
        )
        set_id = res.fetchone()
        if set_id is not None:
            set_id = set_id[0]
        return set_id

    #  pylint: disable=too-many-locals
    def update_set(
        self, set_id: int, config: Config, scraped: dict[str, list[list[list[str]]]]
    ):
        """
        Update an existing flashcard set.
        """
        lang = config.get_lang()
        self.update(
            SqliteHandle.FLASHCARDS_TABLE_NAME, f"lang = '{lang}'", f"id = {set_id}"
        )

        table_name = SqliteHandle.WORD_TABLE_NAME
        res = self.cursor.execute(
            f"SELECT word FROM {table_name} WHERE flashcard_set_id = {set_id}"
        )
        current_words = set(map(lambda word: word[0], res.fetchall()))
        config_word_dct = {entry.get_word(): entry for entry in config}
        config_words = set(config_word_dct.keys())

        words_to_add = config_words - current_words
        for word in words_to_add:
            self.insert_word(set_id, config_word_dct[word], scraped.get(word, None))

        words_to_update = current_words & config_words
        for word in words_to_update:
            self.update_word(config_word_dct[word], scraped.get(word, None))

        words_to_delete = current_words - config_words
        for word in words_to_delete:
            self.delete(SqliteHandle.WORD_TABLE_NAME, f"word = '{word}'")
            res = self.cursor.execute(
                f"SELECT table_uuids FROM '{SqliteHandle.WORD_TABLE_NAME}' WHERE word='{word}';"
            )
            table_uuids = res.fetchone()
            if table_uuids is not None:
                for table_uuid in table_uuids[0].split(","):
                    self.drop_table(table_uuid)

    #  pylint: disable=too-many-branches
    #  pylint: disable=too-many-statements
    def insert_word(
        self, set_id: int, entry: Entry, scraped: list[list[list[str]]] | None
    ):
        """
        Insert a new word into the table.
        """
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
            final_charts = scraped
        else:
            final_charts = [charts]

        table_uuids = []
        if final_charts is not None:
            for chart in final_charts:
                table_uuid = str(uuid.uuid4())
                table_uuids.append(table_uuid)
                max_len = max(map(len, chart))
                schema = ", ".join([f"{chr(i + 97)} TEXT" for i in range(0, max_len)])
                self.recreate_table(f"{table_uuid}", schema)
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
                    self.insert_into(table_uuid, ", ".join(columns), ", ".join(values))

        word = word.replace("'", "''")

        columns = [
            "word",
            "definition",
            "easiness_factor",
            "num_correct",
            "in_n_days",
            "date_of_next",
            "review",
            "flashcard_set_id",
        ]
        values = [
            f"'{word}'",
            f"'{definition}'",
            f"{easiness_factor}",
            f"{num_correct}",
            f"{in_n_days}",
            f"'{date_of_next}'",
            f"{review}",
            f"'{set_id}'",
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
        if len(table_uuids) > 0:
            columns.append("table_uuids")
            table_uuid_str = ",".join(table_uuids)
            values.append(f"'{table_uuid_str}'")
        self.insert_into("words", ", ".join(columns), ", ".join(values))

    #  pylint: disable=too-many-branches
    def update_word(self, entry: Entry, scraped: list[list[list[str]]] | None):
        """
        Update existing word in the table.
        """
        word = entry.get_word()
        definition = entry.get_definition()
        gender = entry.get_gender()
        aspect = entry.get_aspect()
        usage = entry.get_usage()
        part_of_speech = entry.get_part_of_speech()
        charts = entry.get_charts()
        if charts is None:
            final_charts = scraped
        else:
            final_charts = [charts]

        res = self.cursor.execute(
            f"SELECT table_uuids FROM '{SqliteHandle.WORD_TABLE_NAME}' where word = '{word}';"
        )
        table_uuids = res.fetchone()
        if table_uuids is not None:
            for table_uuid in table_uuids[0].split(","):
                self.drop_table(table_uuid)

        table_uuids = []
        if final_charts is not None:
            table_uuids = []
            for chart in final_charts:
                table_uuid = str(uuid.uuid4())
                table_uuids.append(table_uuid)
                max_len = max(map(len, chart))
                schema = ", ".join([f"{chr(i + 97)} TEXT" for i in range(0, max_len)])
                self.recreate_table(f"{table_uuid}", schema)
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
                    self.insert_into(table_uuid, ", ".join(columns), ", ".join(values))

        word = word.replace("'", "''")

        set_statements = [
            f"word = '{word}'",
            f"definition = '{definition}'",
        ]
        if gender is not None:
            set_statements.append(f"gender = '{gender}'")
        if aspect is not None:
            set_statements.append(f"aspect = '{aspect}'")
        if usage is not None:
            set_statements.append(f"usage = '{usage}'")
        if part_of_speech is not None:
            set_statements.append(f"part_of_speech = '{part_of_speech}'")
        if len(table_uuids) > 0:
            table_uuid_str = ",".join(table_uuids)
            set_statements.append(f"table_uuids = '{table_uuid_str}'")

        self.update(
            SqliteHandle.WORD_TABLE_NAME, ", ".join(set_statements), f"word = '{word}'"
        )

    def create_new_set(
        self, file_name: str, config: Config, scraped: dict[str, list[list[list[str]]]]
    ):
        """
        Create a new flashcard set.
        """
        lang = config.get_lang()
        columns = ["file_name"]
        values = [f"'{file_name}'"]
        if lang is not None:
            columns.append("lang")
            values.append(f"'{lang}'")
        self.insert_into("flashcard_sets", ", ".join(columns), ", ".join(values))
        set_id = self.cursor.lastrowid
        self.create_table_idempotent(
            SqliteHandle.WORD_TABLE_NAME,
            SqliteHandle.WORD_SCHEMA,
        )
        if set_id is not None:
            for entry in iter(config):
                self.insert_word(set_id, entry, scraped.get(entry.get_word(), None))

    #  pylint: disable=too-many-nested-blocks
    #  pylint: disable=too-many-statements
    #  pylint: disable=too-many-branches
    #  pylint: disable=too-many-locals
    def import_set(
        self, file_name: str, config: Config, scraped: dict[str, list[list[list[str]]]]
    ) -> bool:
        """
        Import set into database.
        """
        set_id = self.get_id_from_file_name(file_name)
        if set_id is None:
            self.create_new_set(file_name, config, scraped)
            return True

        self.update_set(set_id, config, scraped)
        return False

    def delete_set(self, set_id: int):
        """
        Delete a set from the database.
        """
        res = self.cursor.execute(
            f"SELECT table_uuids FROM '{SqliteHandle.WORD_TABLE_NAME}' WHERE "
            f"flashcard_set_id = {set_id};"
        )
        for uuids in res:
            if uuids[0] is not None:
                for table_uuid in uuids[0].split(","):
                    self.drop_table(table_uuid)
        self.delete("words", f"flashcard_set_id = {set_id}")
        self.delete("flashcard_sets", f"id = {set_id}")

    def load_config(self, file_name: str) -> Config:
        """
        Load config from database.
        """
        set_id = self.get_id_from_file_name(file_name)
        res = self.cursor.execute(
            f"SELECT lang FROM flashcard_sets WHERE file_name = '{file_name}';"
        )
        lang = res.fetchall()[0]

        res = self.cursor.execute(
            f"SELECT word, definition, gender, aspect, usage, part_of_speech, "
            f"easiness_factor, num_correct, in_n_days, date_of_next, review, "
            f"table_uuids FROM 'words' WHERE flashcard_set_id = '{set_id}';"
        )
        entries = res.fetchall()

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
                table_uuids,
            ) = entry
            date_of_next = date.fromisoformat(date_of_next)
            review = review != 0

            charts = []
            if table_uuids is not None:
                for name in table_uuids.split(","):
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
        word = word.replace("'", "''")
        self.update(
            SqliteHandle.WORD_TABLE_NAME,
            f"easiness_factor = {easiness_factor}, num_correct = {num_correct}, "
            f"in_n_days = {in_n_days}, date_of_next = '{date_of_next}', "
            f"review = {review}",
            f"word = '{word}'",
        )

    def get_all_sets(self) -> list[str]:
        """
        Get all flashcard sets from database.
        """
        res = self.cursor.execute("SELECT file_name FROM flashcard_sets;")
        return [entry[0] for entry in res.fetchall()]

    def close(self):
        """
        Close connection to database.
        """
        self.conn.commit()
        self.cursor.close()
        self.conn.close()
