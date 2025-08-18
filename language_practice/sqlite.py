"""
Database code
"""

import sqlite3
from datetime import date
from typing import Any

from language_practice.config import Config, Entry, WordRepetition


class SqliteHandle:
    """
    Handler for sqlite operations.
    """

    FLASHCARDS_TABLE_NAME = "flashcard_sets"
    FLASHCARDS_SCHEMA = "id INTEGER PRIMARY KEY AUTOINCREMENT, file_name TEXT"
    WORD_TABLE_NAME = "words"
    WORD_SCHEMA = (
        "id INTEGER PRIMARY KEY AUTOINCREMENT, word TEXT NOT NULL, "
        "definition TEXT NOT NULL, gender TEXT, aspect TEXT, usage TEXT, "
        "part_of_speech TEXT, easiness_factor REAL, num_correct INTEGER, "
        "in_n_days INTEGER, date_of_next TEXT, review NUMERIC, "
        "flashcard_set_id INTEGER, num_chart_tables INTEGER, lang TEXT"
    )

    def __init__(self, db: str):
        self.db = db
        self.conn = sqlite3.connect(self.db)
        self.cursor = self.conn.cursor()

        self.__create_table(
            SqliteHandle.FLASHCARDS_TABLE_NAME, SqliteHandle.FLASHCARDS_SCHEMA
        )

    def db_path(self):
        """
        Get the path to the database.
        """
        return self.db

    def __create_table(self, name: str, schema: str):
        """
        Create a table only if it doesn't exist
        """
        self.cursor.execute(f"CREATE TABLE IF NOT EXISTS '{name}' ({schema});")

    def __recreate_table(self, name: str, schema: str):
        """
        Recreate a table even if it exists
        """
        self.__drop_table(name)
        self.cursor.execute(f"CREATE TABLE '{name}' ({schema});")

    def __drop_table(self, name: str):
        """
        Drop table.
        """
        res = self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        if (name,) in res.fetchall():
            self.cursor.execute(f"DROP TABLE '{name}';")

    def get_id_from_file_name(self, file_name: str) -> int | None:
        """
        Checks whether the flashcard set already exists.
        """
        table_name = SqliteHandle.FLASHCARDS_TABLE_NAME
        res = self.cursor.execute(
            f"SELECT id FROM {table_name} WHERE file_name = ?",
            (file_name,),
        )
        set_id = res.fetchone()
        if set_id is not None:
            set_id = set_id[0]
        return set_id

    #  pylint: disable=too-many-branches
    #  pylint: disable=too-many-statements
    #  pylint: disable=too-many-locals
    def __insert_word(
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
        lang = entry.get_lang()
        repetition = entry.get_repetition()
        easiness_factor = repetition.get_easiness_factor()
        num_correct = repetition.get_num_correct()
        in_n_days = repetition.get_in_n_days()
        date_of_next = repetition.get_date_of_next()
        review = 1 if repetition.get_review() else 0
        if charts is None:
            final_charts = scraped
        else:
            final_charts = charts

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
        insert_values: list[Any] = [
            word,
            definition,
            easiness_factor,
            num_correct,
            in_n_days,
            date_of_next,
            review,
            set_id,
        ]
        if gender is not None:
            columns.append("gender")
            insert_values.append(gender)
        if aspect is not None:
            columns.append("aspect")
            insert_values.append(aspect)
        if usage is not None:
            columns.append("usage")
            insert_values.append(usage)
        if part_of_speech is not None:
            columns.append("part_of_speech")
            insert_values.append(part_of_speech)
        if final_charts is None:
            columns.append("num_chart_tables")
            insert_values.append(0)
        else:
            columns.append("num_chart_tables")
            insert_values.append(len(final_charts))
        if lang is not None:
            columns.append("lang")
            insert_values.append(lang)
        column_names = ", ".join(columns)
        value_places = ", ".join(["?" for _ in range(len(insert_values))])
        self.cursor.execute(
            f"INSERT INTO words ({column_names}) VALUES({value_places})",
            insert_values,
        )

        sql_id = self.cursor.lastrowid

        if final_charts is not None:
            for idx, chart in enumerate(final_charts):
                max_len = max(map(len, chart))
                if max_len > 26:
                    raise RuntimeError(
                        "Inflection tables are only only supported up to a column size of 26"
                    )
                schema = ", ".join([f"{chr(i + 97)} TEXT" for i in range(max_len)])
                self.__recreate_table(f"{sql_id}-{idx}", schema)
                for row in chart:
                    columns = []
                    values = []
                    for j in range(0, max_len):
                        try:
                            val = row[j]
                        except IndexError:
                            pass
                        else:
                            columns.append(chr(j + 97))
                            values.append(val)
                    column_names = ", ".join(columns)
                    value_places = ", ".join(["?" for _ in range(len(values))])
                    self.cursor.execute(
                        f"INSERT INTO '{sql_id}-{idx}' ({column_names}) "
                        f"VALUES({value_places})",
                        values,
                    )

    def __create_new_set(
        self, file_name: str, config: Config, scraped: dict[str, list[list[list[str]]]]
    ):
        """
        Create a new flashcard set.
        """
        columns = ["file_name"]
        values = [file_name]
        column_names = ", ".join(columns)
        value_places = ", ".join(["?" for _ in range(len(values))])
        self.cursor.execute(
            f"INSERT INTO flashcard_sets ({column_names}) VALUES({value_places})",
            values,
        )
        set_id = self.cursor.lastrowid
        self.__create_table(
            SqliteHandle.WORD_TABLE_NAME,
            SqliteHandle.WORD_SCHEMA,
        )
        if set_id is not None:
            for entry in iter(config):
                self.__insert_word(set_id, entry, scraped.get(entry.get_word(), None))

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
        set_id = self.get_id_from_file_name(file_name)
        if set_id is not None:
            raise SetExistsException(file_name)

        self.__create_new_set(file_name, config, scraped)
        self.conn.commit()

    def delete_set(self, set_id: int):
        """
        Delete a set from the database.
        """
        res = self.cursor.execute(
            f"SELECT id, num_chart_tables FROM '{SqliteHandle.WORD_TABLE_NAME}' WHERE "
            "flashcard_set_id = ?",
            (set_id,),
        )
        for sql_id, num_tables in res.fetchall():
            for i in range(num_tables):
                self.__drop_table(f"{sql_id}-{i}")
        self.cursor.execute(
            f"DELETE FROM {SqliteHandle.WORD_TABLE_NAME} WHERE flashcard_set_id = ?",
            (set_id,),
        )
        self.cursor.execute(
            f"DELETE FROM {SqliteHandle.FLASHCARDS_TABLE_NAME} WHERE id = ?", (set_id,)
        )
        self.conn.commit()

    def search(self, text: str) -> list[tuple[int, str, str, str]]:
        """
        Fuzzy match against all words, definitions, and usages that contain the given
        string.
        """
        like = f"%{text}%"
        res = self.cursor.execute(
            "SELECT id, word, definition, usage FROM words WHERE word LIKE ? OR "
            "definition LIKE ? OR usage LIKE ?",
            (like, like, like),
        )
        return res.fetchall()

    def __load_entry(self, entry, load_only_scheduled: bool) -> Entry | None:
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
            num_chart_tables,
            lang,
            sql_id,
        ) = entry
        date_of_next = date.fromisoformat(date_of_next)
        review = review != 0

        charts = []
        if num_chart_tables > 0:
            for idx in range(0, num_chart_tables):
                res = self.cursor.execute(f"SELECT * FROM '{sql_id}-{idx}';")
                chart = res.fetchall()
                charts.append(chart)

        if load_only_scheduled and not (date.today() >= date_of_next or review):
            return None

        return Entry(
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
            lang,
            sql_id,
        )

    def load_config(self, file_name: str) -> Config:
        """
        Load config from database.
        """
        set_id = self.get_id_from_file_name(file_name)

        res = self.cursor.execute(
            "SELECT word, definition, gender, aspect, usage, part_of_speech, "
            "easiness_factor, num_correct, in_n_days, date_of_next, review, "
            "num_chart_tables, lang, id FROM 'words' WHERE flashcard_set_id = ?",
            (set_id,),
        )
        entries = res.fetchall()

        loaded_entries = []
        for entry in entries:
            entry = self.__load_entry(entry, True)
            if entry is not None:
                loaded_entries.append(entry)

        return Config(file_name, loaded_entries)

    def export_config(self, file_name: str) -> Config:
        """
        Load config from database.
        """
        set_id = self.get_id_from_file_name(file_name)

        res = self.cursor.execute(
            "SELECT word, definition, gender, aspect, usage, part_of_speech, "
            "easiness_factor, num_correct, in_n_days, date_of_next, review, "
            "num_chart_tables, lang, id FROM 'words' WHERE flashcard_set_id = ?",
            (set_id,),
        )
        entries = res.fetchall()

        loaded_entries = []
        for entry in entries:
            entry = self.__load_entry(entry, False)
            if entry is not None:
                if entry.charts is not None:
                    entry.charts = [
                        [
                            [item if item is not None else "" for item in row]
                            for row in chart
                        ]
                        for chart in entry.charts
                    ]
                loaded_entries.append(entry)

        return Config(file_name, loaded_entries)

    def load_single_entry(self, entry_id: int) -> Entry:
        """
        Load entry from database.
        """
        res = self.cursor.execute(
            "SELECT word, definition, gender, aspect, usage, part_of_speech, "
            "easiness_factor, num_correct, in_n_days, date_of_next, review, "
            "num_chart_tables, lang, id FROM 'words' WHERE id = ?",
            (entry_id,),
        )
        entry = self.__load_entry(res.fetchone(), False)
        assert entry is not None
        return entry

    def update_single_entry(self, entry: Entry):
        """
        Update a single entry.
        """
        word = entry.get_word()
        definition = entry.get_definition()
        usage = entry.get_usage()
        gender = entry.get_gender()
        aspect = entry.get_aspect()
        part_of_speech = entry.get_part_of_speech()
        idx = entry.get_sql_id()

        update_statements = ["word = ?", "definition = ?"]
        args = [word, definition]
        update_statements.append("usage = ?")
        args.append(usage)
        update_statements.append("gender = ?")
        args.append(gender)
        update_statements.append("aspect = ?")
        args.append(aspect)
        update_statements.append("part_of_speech = ?")
        args.append(part_of_speech)

        sets = ", ".join(update_statements)
        self.cursor.execute(
            f"UPDATE {SqliteHandle.WORD_TABLE_NAME} SET {sets} WHERE id = ?",
            args + [idx],
        )
        self.conn.commit()

    def update_config(self, idx: int, repetition: WordRepetition):
        """
        Update config for word.
        """
        easiness_factor = repetition.get_easiness_factor()
        num_correct = repetition.get_num_correct()
        in_n_days = repetition.get_in_n_days()
        date_of_next = str(repetition.get_date_of_next())
        review = 1 if repetition.get_review() else 0
        self.cursor.execute(
            f"UPDATE {SqliteHandle.WORD_TABLE_NAME} SET easiness_factor = ?, "
            "num_correct = ?, in_n_days = ?, date_of_next = ?, review = ? "
            "WHERE id = ?",
            (easiness_factor, num_correct, in_n_days, date_of_next, review, idx),
        )
        self.conn.commit()

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


class SetExistsException(Exception):
    """
    An exception that is throw if the set being imported already exists.
    """

    def __init__(self, set_name: str):
        super().__init__(f"Set with set name {set_name} already exists")
