from random import shuffle
from tomllib import load

from tabulate import tabulate


class TomlEntry:
    def __init__(self, cache, dct):
        try:
            self.cache = cache
            self.word = dct["word"]
            self.definition = dct["definition"]
            self.gender = dct.get("gender")
            self.aspect = dct.get("aspect")
            self.usage = dct.get("usage")
        except KeyError as msg:
            error = f"Key {msg} not found"
            if hasattr(self, "word"):
                error += f" for entry {self.word}"
            raise RuntimeError(error) from msg

    def entry(self):
        if self.aspect is None:
            return f"{self.definition}"

        return f"[{self.aspect}] {self.definition}"

    def show_usage(self):
        return self.usage

    def get_word(self):
        return self.word

    def show_word(self):
        if self.gender is None:
            return self.word

        return f"[{self.gender}] {self.word}"

    def chart(self):
        for chart in self.cache[self.word]:
            return tabulate(chart, tablefmt="pretty")


class TomlConfig:
    def __init__(self, file_path, correct, cache):
        with open(file_path, "rb") as file_handle:
            self.words = [
                TomlEntry(cache, dct)
                for dct in load(file_handle)["words"]
                if dct["word"] not in correct
            ]
        shuffle(self.words)

    def __iter__(self):
        return iter(self.words)

    def __len__(self):
        return len(self.words)
