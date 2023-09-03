from random import shuffle
from tomllib import load


class TomlEntry:
    def __init__(self, dct):
        try:
            self.word = dct["word"]
            self.definition = dct["definition"]
            self.gender = dct.get("gender")
            self.aspect = dct.get("aspect")
            self.usage = dct.get("usage")
            self.part_of_speech = dct.get("part_of_speech")
        except KeyError as msg:
            error = f"Key {msg} not found"
            if hasattr(self, "word"):
                error += f" for entry {self.word}"
            raise RuntimeError(error) from msg

    def entry(self):
        ret = self.definition
        if self.aspect is not None:
            ret = f"[{self.aspect}] " + ret
        if self.part_of_speech is not None:
            ret = f"[{self.part_of_speech}] " + ret

        return ret

    def show_usage(self):
        return self.usage

    def get_word(self):
        return self.word

    def show_word(self):
        ret = self.word
        if self.gender is not None:
            ret = f"[{self.gender}] " + ret

        return ret


class TomlConfig:
    def __init__(self, file_path, correct):
        with open(file_path, "rb") as file_handle:
            self.words = [
                TomlEntry(dct)
                for dct in load(file_handle)["words"]
                if dct["word"] not in correct
            ]
        shuffle(self.words)

    def __iter__(self):
        return iter(self.words)

    def __len__(self):
        return len(self.words)
