from random import shuffle
import os
import regex
import sys
import termios
import tty


class Application:
    def __init__(self, word_path):
        if not word_path.endswith(".txt"):
            raise RuntimeError("Word file needs to be a text file")

        try:
            self.word_path = word_path
            with open(self.word_path, "r") as word_file:
                self.words = {}
                for word in [
                    word for word in word_file.read().split("\n") if word != ""
                ]:
                    split = [split for split in word.split("|")]
                    try:
                        (word, definition) = split
                    except ValueError:
                        pass
                    else:
                        self.words[word] = definition

            (name, _) = os.path.splitext(self.word_path)

            self.correct_path = f"{name}-correct.txt"
            try:
                with open(self.correct_path, "r") as correct_file:
                    self.correct = set(
                        [
                            correct
                            for correct in correct_file.read().split("\n")
                            if correct != ""
                        ]
                    )
            except Exception as e:
                print(e)
                self.correct = set()

            for correct in self.correct:
                del self.words[correct]

            self.words = [(k, v) for k, v in self.words.items()]
            shuffle(self.words)
            self.iter = iter(self.words)
            (self.word, self.definition) = next(self.iter)

            if len(self.correct) == len(self.words):
                self.correct = set()

            self.settings = termios.tcgetattr(sys.stdin.fileno())
            tty.setraw(sys.stdin.fileno())

            self.entry()

            cont = True
            while cont:
                code = sys.stdin.read(1)
                cont = self.handle_code(code)
        except:
            self.shutdown()
            raise
        finally:
            self.shutdown()

    def shutdown(self):
        if hasattr(self, "settings"):
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)
        if hasattr(self, "correct"):
            with open(self.correct_path, "w") as correct_file:
                for correct in self.correct:
                    correct_file.write(f"{correct}\n")

    def handle_code(self, code):
        if code == "\x03":
            raise KeyboardInterrupt
        elif code == "e":
            self.entry()
        elif code == "d":
            self.show_word()
        elif code == "n":
            try:
                (self.word, self.definition) = next(self.iter)
            except StopIteration:
                return False
            self.entry()
        elif code == "y":
            self.correct.add(self.word)
            try:
                (self.word, self.definition) = next(self.iter)
            except StopIteration:
                return False
            self.entry()

        return True

    def entry(self):
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)
        print("\033c", end="")
        print(f"{self.definition}")
        tty.setraw(sys.stdin)

    def show_word(self):
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)
        print("\033c", end="")
        print(f"{self.word}", end="\n\n")
        tty.setraw(sys.stdin)
