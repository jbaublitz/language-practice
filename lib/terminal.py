import os
import regex
import sys
import termios
import tty

from lib.toml import TomlConfig


class Application:
    def __init__(self, word_path):
        if not word_path.endswith(".toml"):
            raise RuntimeError("Word file needs to be a TOML file")
        self.word_path = word_path

        try:
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

            self.words = TomlConfig(self.word_path, self.correct)

            self.iter = iter(self.words)
            self.next = next(self.iter)

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
        elif code == "c":
            self.chart()
        elif code == "n":
            try:
                self.next = next(self.iter)
            except StopIteration:
                return False
            self.entry()
        elif code == "y":
            self.correct.add(self.next.show_word())
            try:
                self.next = next(self.iter)
            except StopIteration:
                return False
            self.entry()

        return True

    def entry(self):
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)
        print("\033c", end="")
        entry = self.next.entry()
        print(f"{entry}")
        tty.setraw(sys.stdin)

    def chart(self):
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)
        print("\033c", end="")
        chart = self.next.chart()
        print(f"{chart}")
        tty.setraw(sys.stdin)

    def show_word(self):
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)
        print("\033c", end="")
        word = self.next.show_word()
        print(f"{word}", end="\n\n")
        tty.setraw(sys.stdin)
