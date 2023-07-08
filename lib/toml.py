from tomllib import load
from tabulate import tabulate
from random import shuffle


class TomlEntry:
    def __init__(self, dct):
        if dct["pos"] == "v":
            self.pos = "verb"
        else:
            raise RuntimeError("Unrecognized part of speech")

        if self.pos == "verb":
            if dct["aspect"] == "impf":
                self.aspect = "imperfective"
            elif dct["aspect"] == "pf":
                self.aspect = "perfective"
            else:
                raise RuntimeError("Unrecognized aspect")

        if self.pos == "verb":
            if self.aspect == "imperfective":
                self.tense = "present"
            if self.aspect == "perfective":
                self.tense = "future"
            self.conj = dct[self.tense]
            if (
                "ts" not in self.conj
                and "fp" not in self.conj
                and "sp" not in self.conj
            ):
                stem = self.conj["ss"].replace("шь", "")
                self.conj["ts"] = stem + "т"
                self.conj["fp"] = stem + "м"
                self.conj["sp"] = stem + "те"

        self.word = dct["word"]
        self.definition = dct["definition"]

    def entry(self):
        if self.pos == "verb":
            return f"{self.pos}\n\n{self.aspect}\n\n{self.definition}"

    def show_word(self):
        return f"{self.word}"

    def chart(self):
        if self.pos == "verb":
            tense = self.tense
            table = tabulate(
                [
                    [self.conj["fs"], self.conj["fp"]],
                    [self.conj["ss"], self.conj["sp"]],
                    [self.conj["ts"], self.conj["tp"]],
                ]
            )

            return f"{tense}\n\n{table}"


class TomlConfig:
    def __init__(self, file_path, correct):
        self.words = [
            TomlEntry(dct)
            for dct in load(open(file_path, "rb"))["words"]
            if dct["word"] not in correct
        ]
        shuffle(self.words)

    def __iter__(self):
        return iter(self.words)

    def __len__(self):
        return len(self.words)
