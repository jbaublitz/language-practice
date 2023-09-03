from collections import deque
import json


class Repetition:
    def __init__(self, path, words):
        self.repetition_path = path

        try:
            with open(self.repetition_path, "r", encoding="utf-8") as file_handle:
                dct = json.loads(file_handle.read())
        except IOError:
            dct = {
                "level1": deque(words),
                "level2": deque(),
                "level3": deque(),
                "level4": deque(),
                "level5": deque(),
            }

        self.level1 = deque(dct["level1"])
        self.level2 = deque(dct["level2"])
        self.level3 = deque(dct["level3"])
        self.level4 = deque(dct["level4"])
        self.level5 = deque(dct["level5"])
        self.all_words = set(
            self.level1 + self.level2 + self.level3 + self.level4 + self.level5
        )

        for word in words:
            if word not in self.all_words:
                self.level1.append(word)
                self.all_words.add(word)

    def next(self):
        try:
            return (1, self.level1.pop())
        except IndexError:
            pass

        try:
            return (2, self.level2.pop())
        except IndexError:
            pass

        try:
            return (3, self.level3.pop())
        except IndexError:
            pass

        try:
            return (4, self.level4.pop())
        except IndexError:
            pass

        try:
            return (5, self.level5.pop())
        except IndexError:
            return None

    def incorrect(self, word):
        self.level1.appendleft(word)

    def correct(self, level, word):
        match level:
            case 1:
                self.level2.appendleft(word)
            case 2:
                self.level3.appendleft(word)
            case 3:
                self.level4.appendleft(word)
            case 4:
                self.level5.appendleft(word)
            case 5:
                self.level5.appendleft(word)

    def save(self, level, word):
        match level:
            case 1:
                self.level1.append(word)
            case 2:
                self.level2.append(word)
            case 3:
                self.level3.append(word)
            case 4:
                self.level4.append(word)
            case 5:
                self.level5.append(word)

        level1 = [word for word in self.level1]
        level2 = [word for word in self.level2]
        level3 = [word for word in self.level3]
        level4 = [word for word in self.level4]
        level5 = [word for word in self.level5]
        dct = {
            "level1": level1,
            "level2": level2,
            "level3": level3,
            "level4": level4,
            "level5": level5,
        }
        with open(self.repetition_path, "w", encoding="utf-8") as file_handle:
            file_handle.write(json.dumps(dct))
