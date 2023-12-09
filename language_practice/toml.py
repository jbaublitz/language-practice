"""
Handles TOML parsing from the configuration file.
"""
from tomllib import load


class TomlEntry:
    """
    A single entry in the TOML file.
    """

    def __init__(self, dct):
        try:
            self.word = dct["word"]
            self.definition = dct["definition"]
            self.gender = dct.get("gender")
            self.aspect = dct.get("aspect")
            self.usage = dct.get("usage")
            self.part_of_speech = dct.get("part_of_speech")
            self.charts = dct.get("charts")
        except KeyError as err:
            error = f"Key {err} not found"
            if hasattr(self, "word"):
                error += f" for entry {self.word}"
            raise RuntimeError(error) from err

    def show_definition(self):
        """
        Show the definition as a user readable string.
        """
        ret = self.definition
        if self.aspect is not None:
            ret = f"[{self.aspect}] " + ret
        if self.part_of_speech is not None:
            ret = f"[{self.part_of_speech}] " + ret

        return ret

    def show_usage(self):
        """
        Show the usage as a user readable string.
        """
        return self.usage

    def get_word(self):
        """
        Return the word to be used programmatically.
        """
        return self.word

    def show_word(self):
        """
        Show the word as a user readable string.
        """
        ret = self.word
        if self.gender is not None:
            ret = f"[{self.gender}] " + ret

        return ret

    def get_charts(self):
        """
        Get the inflection charts as a list of lists.
        """
        return self.charts


class TomlConfig:
    """
    All entries in the TOML file.
    """

    def __init__(self, file_path):
        try:
            with open(file_path, "rb") as file_handle:
                toml = load(file_handle)
                lang = toml["lang"]
                if lang is not None and lang not in ["fr", "uk", "ru"]:
                    raise RuntimeError(
                        f"Language {lang} is not supported; if you would like it to "
                        "be, please open a feature request!"
                    )
                self.lang = lang
                self.words = {dct["word"]: TomlEntry(dct) for dct in toml["words"]}
        except KeyError as err:
            raise RuntimeError(f"Key {err} not found") from err

    def __iter__(self):
        return iter(self.words)

    def __len__(self):
        return len(self.words)

    def __getitem__(self, item):
        return self.words[item]

    def get_lang(self):
        """
        Get the language associated with this word file, if any.
        """
        return self.lang

    def get_words(self):
        """
        Get a list of all words in the TOML file.
        """
        return list(self.words.keys())
