"""
Handles TOML parsing from the configuration file.
"""

import os
from datetime import date
from tomllib import load
from typing import Any, Self

import tomli_w

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
        lang: str | None,
    ):
        self.word = word
        self.definition = definition
        self.gender = gender
        self.aspect = aspect
        self.usage = usage
        self.part_of_speech = part_of_speech
        self.charts = charts
        self.repetition = repetition
        self.lang = lang

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

    def get_lang(self) -> str | None:
        """
        Get the language associated with this word file, if any.
        """
        return self.lang


class Config:
    """
    Generic config data structure.
    """

    def __init__(self, set_name: str, entries: list[Entry]):
        self.set_name = set_name
        self.words = entries

    def __iter__(self):
        return iter(self.words)

    def __len__(self) -> int:
        return len(self.words)

    def get_words(self) -> list[Entry]:
        """
        Get a list of all words in the TOML file.
        """
        return self.words

    def extend(self, config: Self):
        """
        Extend a TOML config with another TOML config.
        """
        self.words += config.words
        return self

    def validate_lang(self) -> str | None:
        """
        Returns the language for the config or, if the language is not consistent,
        raise an exception.
        """
        lang = set(config.get_lang() for config in self.words)
        if len(lang) > 1:
            raise RuntimeError(
                "All entries in a config are required to have the same language"
            )
        return lang.pop()

    def export(self, export_dest: str):
        """
        Export the config to a TOML file.
        """
        dct: dict[str, Any] = {"words": []}
        lang = self.validate_lang()
        if lang is not None:
            dct["lang"] = lang

        for entry in self.words:
            parsed_dct = {
                k: v
                for k, v in entry.__dict__.items()
                if k not in ("lang", "repetition") and v is not None
            }
            dct["words"].append(parsed_dct)

        with open(os.path.join(export_dest, self.set_name), "w", encoding="utf8") as f:
            f.write(tomli_w.dumps(dct))


class GraphicalConfig(Config):
    """
    All entries in the graphical config.
    """

    def __init__(self, set_name: str, lang: str | None, dcts: list[dict[str, Any]]):
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
                    lang,
                )
                for dct in dcts
            ]
            super().__init__(set_name, words)
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
                        lang,
                    )
                    for dct in toml["words"]
                ]
                super().__init__(file_path, words)
        except KeyError as err:
            raise RuntimeError(f"Key {err} not found") from err
