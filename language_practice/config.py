"""
Handles TOML parsing from the configuration file.
"""

from datetime import date
from tomllib import load
from typing import Any, Self

from language_practice.repetition import WordRepetition


#  pylint: disable=too-many-instance-attributes
class Entry:
    """
    A single entry in the TOML file.
    """

    #  pylint: disable=too-many-arguments
    #  pylint: disable=too-many-positional-arguments
    def __init__(
        self,
        word: str,
        definition: str,
        gender: str | None,
        aspect: str | None,
        usage: str | None,
        part_of_speech: str | None,
        charts: list[list[str]] | None,
        repetition: WordRepetition,
    ):
        self.word = word
        self.definition = definition
        self.gender = gender
        self.aspect = aspect
        self.usage = usage
        self.part_of_speech = part_of_speech
        self.charts = charts
        self.repetition = repetition

    def get_word(self) -> str:
        """
        Get word.
        """
        return self.word

    def get_definition(self) -> str:
        """
        Get definition.
        """
        return self.definition

    def get_gender(self) -> str | None:
        """
        Get gender.
        """
        return self.gender

    def get_aspect(self) -> str | None:
        """
        Get aspect.
        """
        return self.aspect

    def get_usage(self) -> str | None:
        """
        Get usage.
        """
        return self.usage

    def get_part_of_speech(self) -> str | None:
        """
        Get part of speech.
        """
        return self.part_of_speech

    def get_charts(self) -> list[list[str]] | None:
        """
        Get charts.
        """
        return self.charts

    def get_repetition(self) -> WordRepetition:
        """
        Get repetition data structure.
        """
        return self.repetition


class Config:
    """
    Generic config data structure.
    """

    def __init__(self, lang: str | None, entries: list[Entry]):
        self.lang = lang
        self.words = entries

    def __iter__(self):
        return iter(self.words)

    def __len__(self) -> int:
        return len(self.words)

    def get_lang(self) -> str | None:
        """
        Get the language associated with this word file, if any.
        """
        return self.lang

    def get_words(self) -> list[Entry]:
        """
        Get a list of all words in the TOML file.
        """
        return self.words

    def extend(self, config: Self):
        """
        Extend a TOML config with another TOML config.
        """
        if self.lang != config.lang:
            raise RuntimeError(
                f"Attempted to join a TOML config with lang {self.lang} with"
                f"one with lang {config.lang}"
            )

        self.words += config.words
        return self


class GraphicalConfig(Config):
    """
    All entries in the graphical config.
    """

    def __init__(self, lang: str | None, dcts: list[dict[str, Any]]):
        try:
            words = [
                Entry(
                    dct["word"],
                    dct["definition"],
                    dct.get("gender", None),
                    dct.get("aspect", None),
                    dct.get("usage", None),
                    dct.get("part_of_speech", None),
                    dct.get("charts", None),
                    WordRepetition(2.5, 0, 0, date.today(), False),
                )
                for dct in dcts
            ]
            super().__init__(lang, words)
        except KeyError as err:
            raise RuntimeError(f"Key {err} not found") from err


class TomlConfig(Config):
    """
    All entries in the TOML file.
    """

    def __init__(self, file_path: str):
        try:
            with open(file_path, "rb") as file_handle:
                toml = load(file_handle)
                lang = toml.get("lang", None)
                if lang is not None and lang not in ["fr", "uk", "ru"]:
                    raise RuntimeError(
                        f"Language {lang} is not supported; if you would like it to "
                        "be, please open a feature request!"
                    )
                words = [
                    Entry(
                        dct["word"],
                        dct["definition"],
                        dct.get("gender", None),
                        dct.get("aspect", None),
                        dct.get("usage", None),
                        dct.get("part_of_speech", None),
                        dct.get("charts", None),
                        WordRepetition(2.5, 0, 0, date.today(), False),
                    )
                    for dct in toml["words"]
                ]
                super().__init__(lang, words)
        except KeyError as err:
            raise RuntimeError(f"Key {err} not found") from err
