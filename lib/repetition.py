from collections import deque
import json


class WordRepetition:
    def __init__(self, word, dct={}):
        self.word = word

        self.correct = dct["correct"] if "correct" in dct else 0
        self.incorrect = dct["incorrect"] if "incorrect" in dct else 0
        self.incorrect_since_ten_correct = (
            dct["incorrect_since_ten_correct"]
            if "incorrect_since_ten_correct" in dct
            else 0
        )

    def get_word(self):
        return self.word

    def mark_correct(self):
        self.correct += 1
        self.incorrect = 0
        if self.correct >= 10:
            self.incorrect_since_ten_correct = 0

    def mark_incorrect(self):
        self.incorrect += 1
        self.correct = 0
        self.incorrect_since_ten_correct += 1

    def repeat_in(self):
        index = 15
        if self.correct == 0:
            index = max(index - self.incorrect, 1)
        elif self.incorrect == 0:
            initial = max(index - self.incorrect_since_ten_correct, 1)
            initial *= self.correct

        return index

    def save(self):
        return {
            "word": self.word,
            "correct": self.correct,
            "incorrect": self.correct,
            "incorrect_since_ten_correct": self.incorrect_since_ten_correct,
        }


class Repetition:
    def __init__(self, path, words):
        self.repetition_path = path

        try:
            with open(self.repetition_path, "r", encoding="utf-8") as file_handle:
                lst = json.loads(file_handle.read())
                self.all_words = set(dct["word"] for dct in lst)
                self.repetitions = deque(
                    WordRepetition(rep_dct["word"], rep_dct) for rep_dct in lst
                )
        except IOError:
            self.repetitions = deque(WordRepetition(word) for word in words)
            self.all_words = set(words)
        except json.JSONDecodeError:
            self.repetitions = deque(WordRepetition(word) for word in words)
            self.all_words = set(words)
        except KeyError:
            self.repetitions = deque(WordRepetition(word) for word in words)
            self.all_words = set(words)
        except TypeError:
            self.repetitions = deque(WordRepetition(word) for word in words)
            self.all_words = set(words)

        for word in words:
            if word not in self.all_words:
                self.repetitions.insert(0, WordRepetition(word))

    def peek(self):
        print([rep.get_word() for rep in self.repetitions])
        return self.repetitions[0].get_word() if len(self.repetitions) > 0 else None

    def incorrect(self):
        elem = self.repetitions.popleft()
        elem.mark_incorrect()
        index = elem.repeat_in()
        self.repetitions.insert(min(index, len(self.repetitions)), elem)

    def correct(self):
        elem = self.repetitions.popleft()
        elem.mark_correct()
        index = elem.repeat_in()
        self.repetitions.insert(min(index, len(self.repetitions)), elem)

    def save(self):
        with open(self.repetition_path, "w", encoding="utf-8") as file_handle:
            file_handle.write(json.dumps([item.save() for item in self.repetitions]))