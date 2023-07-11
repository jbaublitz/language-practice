from tomllib import load
from tabulate import tabulate
from random import shuffle


class TomlEntry:
    def __init__(self, dct):
        if dct["pos"] == "v":
            self.pos = "verb"
            if dct["aspect"] == "impf":
                self.aspect = "imperfective"
                self.tense = "present"
            elif dct["aspect"] == "pf":
                self.aspect = "perfective"
                self.tense = "future"
            else:
                raise RuntimeError("Unrecognized aspect for verb")

            self.conj = dct[self.tense]
            if (
                "ts" not in self.conj
                and "fp" not in self.conj
                and "sp" not in self.conj
            ):
                if self.conj["ss"].endswith("шь"):
                    stem = self.conj["ss"].replace("шь", "")
                    self.conj["ts"] = stem + "т"
                    self.conj["fp"] = stem + "м"
                    self.conj["sp"] = stem + "те"
                elif self.conj["ss"].endswith("шься"):
                    stem = self.conj["ss"].replace("шься", "")
                    self.conj["ts"] = stem + "тся"
                    self.conj["fp"] = stem + "мся"
                    self.conj["sp"] = stem + "тесь"

        elif dct["pos"] == "n":
            self.pos = "noun"
            if dct["gender"] == "m":
                self.gender = "masculine"
            elif dct["gender"] == "f":
                self.gender = "feminine"
            elif dct["gender"] == "n":
                self.gender = "neuter"
            else:
                raise RuntimeError("Unrecognized gender for noun")

            self.decl = dct["declension"]
        elif dct["pos"] == "adv":
            self.pos = "adverb"
        elif dct["pos"] == "adj":
            self.pos = "adjective"
            self.masc = dct["masc"]
            self.neu = dct["neu"]
            self.fem = dct["fem"]
            self.plu = dct["plural"]
        elif dct["pos"] == "expr":
            self.pos = "expression"
        else:
            raise RuntimeError("Unrecognized part of speech")

        self.word = dct["word"]
        self.definition = dct["definition"]

    def entry(self):
        if self.pos == "verb":
            return f"{self.pos}\n\n{self.aspect}\n\n{self.definition}"
        if self.pos == "noun" or self.pos == "adverb" or self.pos == "adjective" or self.pos == "expression":
            return f"{self.pos}\n\n{self.definition}"

    def show_word(self):
        if self.pos == "verb" or self.pos == "adverb" or self.pos == "adjective" or self.pos == "expression":
            return f"{self.word}"
        elif self.pos == "noun":
            return f"({self.gender}) {self.word}"

    def chart(self):
        if self.pos == "verb":
            tense = self.tense
            table = tabulate(
                [
                    ["", self.tense],
                    ["я", self.conj["fs"]],
                    ["ты", self.conj["ss"]],
                    ["он/она/оно", self.conj["ts"]],
                    ["мы", self.conj["fp"]],
                    ["вы", self.conj["sp"]],
                    ["они", self.conj["tp"]]
                ]
            )

            return f"{tense}\n\n{table}"
        elif self.pos == "noun":
            table = [
                ["", "singular", "plural"],
                ["nominative", self.decl["ns"], self.decl["np"]],
                ["genitive", self.decl["gs"], self.decl["gp"]],
                ["dative", self.decl["ds"], self.decl["dp"]],
                ["accusative", self.decl["as"], self.decl["ap"]],
                ["instrumental", self.decl["is"], self.decl["ip"]],
                ["prepositional", self.decl["ps"], self.decl["pp"]],
            ]
            if "ls" in self.decl:
                table.append(["locative", self.decl["ls"], ""])
            table = tabulate(table)

            return f"{table}"
        elif self.pos == "adverb" or self.pos == "expression":
            return None
        elif self.pos == "adjective":
            table = [
                ["", "masculine", "neuter", "feminine", "plural"],
                ["nominative", self.masc["n"], self.neu["n"],
                    self.fem["n"], self.plu["n"]],
                ["genitive", self.masc["g"], self.neu["g"],
                    self.fem["g"], self.plu["g"]],
                ["dative", self.masc["d"], self.neu["d"],
                    self.fem["d"], self.plu["d"]],
                ["accusative", self.masc["a"], self.neu["a"],
                    self.fem["a"], self.plu["a"]],
                ["instrumental", self.masc["i"], self.neu["i"],
                    self.fem["i"], self.plu["i"]],
                ["prepositional", self.masc["p"], self.neu["p"],
                    self.fem["p"], self.plu["p"]],
                ["short", self.masc["short"], self.neu["short"],
                    self.fem["short"], self.plu["short"]],
            ]
            table = tabulate(table)

            return f"{table}"


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
