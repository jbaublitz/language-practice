from tomllib import load
from tabulate import tabulate
from random import shuffle


class TomlEntry:
    def __init__(self, dct):
        self.word = dct["word"]
        self.definition = dct["definition"]

        if dct["pos"] == "v":
            self.pos = "verb"
            if dct["aspect"] == "impf":
                self.aspect = "imperfective"
            elif dct["aspect"] == "pf":
                self.aspect = "perfective"
            else:
                raise RuntimeError("Unrecognized aspect for verb")

            if "present" in dct:
                self.present = dct["present"]
            if self.aspect == "perfective":
                self.future = dct["future"]
            else:
                self.future = {
                    "fs": f"бу́ду {self.word}",
                    "ss": f"бу́дешь {self.word}",
                    "ts": f"бу́дет {self.word}",
                    "fp": f"бу́дем {self.word}",
                    "sp": f"бу́дете {self.word}",
                    "tp": f"бу́дут {self.word}",
                }
            if "past" in dct:
                self.past = dct["past"]
            else:
                if self.word.endswith("ть"):
                    stem = self.word.replace("ть", "")
                    self.past = {
                        "ms": stem + "л",
                        "fs": stem + "ла",
                        "ns": stem + "ло",
                        "p": stem + "ли",
                    }
                elif self.word.endswith("ться"):
                    stem = self.word.replace("ться", "")
                    self.past = {
                        "ms": stem + "лся",
                        "fs": stem + "лась",
                        "ns": stem + "лось",
                        "p": stem + "лись",
                    }
            self.part = dct["participles"]
            self.imp = dct["imperative"]

            self.conj = self.future if self.aspect == "perfective" else self.present

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

            self.sing = dct["singular"]
            self.plu = dct["plural"]
        elif dct["pos"] == "adv":
            self.pos = "adverb"
        elif dct["pos"] == "adj":
            self.pos = "adjective"
            self.masc = dct["masculine"]
            self.neu = dct["neuter"]
            self.fem = dct["feminine"]
            self.plu = dct["plural"]
        elif dct["pos"] == "expr":
            self.pos = "expression"
        else:
            raise RuntimeError("Unrecognized part of speech")

    def entry(self):
        if self.pos == "verb":
            return f"{self.pos}\n\n{self.aspect}\n\n{self.definition}"
        if (
            self.pos == "noun"
            or self.pos == "adverb"
            or self.pos == "adjective"
            or self.pos == "expression"
        ):
            return f"{self.pos}\n\n{self.definition}"

    def show_word(self):
        if (
            self.pos == "verb"
            or self.pos == "adverb"
            or self.pos == "adjective"
            or self.pos == "expression"
        ):
            return f"{self.word}"
        elif self.pos == "noun":
            return f"({self.gender}) {self.word}"

    def chart(self):
        if self.pos == "verb":
            if hasattr(self, "present"):
                table = tabulate(
                    [
                        ["", "present", "future"],
                        ["я", self.present["fs"], self.future["fs"]],
                        ["ты", self.present["ss"], self.future["ss"]],
                        ["он/она/оно", self.present["ts"], self.future["ts"]],
                        ["мы", self.present["fp"], self.future["fp"]],
                        ["вы", self.present["sp"], self.future["sp"]],
                        ["они", self.present["tp"], self.future["tp"]],
                    ]
                )
            else:
                table = tabulate(
                    [
                        ["", "future"],
                        ["я", self.future["fs"]],
                        ["ты", self.future["ss"]],
                        ["он/она/оно", self.future["ts"]],
                        ["мы", self.future["fp"]],
                        ["вы", self.future["sp"]],
                        ["они", self.future["tp"]],
                    ]
                )

            imperative = tabulate(
                [
                    ["", "imperative"],
                    ["singular", self.imp["s"]],
                    ["plural", self.imp["p"]],
                ]
            )

            if self.aspect == "perfective":
                participles_header = ["", "past"]
            else:
                participles_header = ["", "present", "past"]
            active_participles = ["active"]
            if self.aspect == "imperfective":
                active_participles.append(
                    "" if self.part.get("pres_act") is None else self.part["pres_act"]
                )
            active_participles.append(
                "" if self.part.get("past_act") is None else self.part["past_act"]
            )
            passive_participles = ["passive"]
            if self.aspect == "imperfective":
                passive_participles.append(
                    ""
                    if self.part.get("pres_pass") is None
                    else self.part["pres_pass"],
                )
            passive_participles.append(
                "" if self.part.get("past_pass") is None else self.part["past_pass"],
            )
            adverbial_participles = ["adverbial"]
            if self.aspect == "imperfective":
                adverbial_participles.append(
                    "" if self.part.get("pres_adv") is None else self.part["pres_adv"],
                )
            adverbial_participles.append(
                "" if self.part.get("past_adv_l") is None else self.part["past_adv_l"],
            )

            participles_list = [
                participles_header,
                active_participles,
                passive_participles,
                adverbial_participles,
            ]
            if "past_adv_s" in self.part:
                if self.aspect == "imperfective":
                    participles_list.append(
                        ["adverbial short", "", self.part["past_adv_s"]]
                    )
                else:
                    participles_list.append(
                        ["adverbial short", self.part["past_adv_s"]]
                    )
            participles = tabulate(participles_list)

            return f"{table}\n\n{imperative}\n\n{participles}"

        elif self.pos == "noun":
            table = [
                ["", "singular", "plural"],
                ["nominative", self.sing["n"], self.plu["n"]],
                ["genitive", self.sing["g"], self.plu["g"]],
                ["dative", self.sing["d"], self.plu["d"]],
                ["accusative", self.sing["a"], self.plu["a"]],
                ["instrumental", self.sing["i"], self.plu["i"]],
                ["prepositional", self.sing["p"], self.plu["p"]],
            ]
            if "ls" in self.sing:
                table.append(["locative", self.sing["l"], ""])
            table = tabulate(table)

            return f"{table}"
        elif self.pos == "adverb" or self.pos == "expression":
            return None
        elif self.pos == "adjective":
            table = [
                ["", "masculine", "neuter", "feminine", "plural"],
                [
                    "nominative",
                    self.masc["n"],
                    self.neu["n"],
                    self.fem["n"],
                    self.plu["n"],
                ],
                [
                    "genitive",
                    self.masc["g"],
                    self.neu["g"],
                    self.fem["g"],
                    self.plu["g"],
                ],
                ["dative", self.masc["d"], self.neu["d"], self.fem["d"], self.plu["d"]],
                [
                    "accusative",
                    self.masc["a"],
                    self.neu["a"],
                    self.fem["a"],
                    self.plu["a"],
                ],
                [
                    "instrumental",
                    self.masc["i"],
                    self.neu["i"],
                    self.fem["i"],
                    self.plu["i"],
                ],
                [
                    "prepositional",
                    self.masc["p"],
                    self.neu["p"],
                    self.fem["p"],
                    self.plu["p"],
                ],
            ]
            if (
                "short" in self.masc
                and "short" in self.fem
                and "short" in self.neu
                and "short" in self.plu
            ):
                table.append(
                    [
                        "short",
                        self.masc["short"],
                        self.neu["short"],
                        self.fem["short"],
                        self.plu["short"],
                    ]
                )
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
