import os
import sys
import termios
import tty

from lib.cache import Cache
from lib.toml import TomlConfig
from lib.web import refresh, scrape


class Application:
    def __init__(self, word_path):
        if not word_path.endswith(".toml"):
            raise RuntimeError("Word file needs to be a TOML file")
        self.word_path = word_path

        (name, _) = os.path.splitext(self.word_path)

        self.correct_path = f"{name}-correct.txt"
        try:
            with open(self.correct_path, "r", encoding="utf-8") as correct_file:
                self.correct = set(
                    correct
                    for correct in correct_file.read().split("\n")
                    if correct != ""
                )
        except IOError:
            self.correct = set()

        self.cache_path = f"{name}-cache.json"
        self.cache = Cache(self.cache_path)

        self.words = TomlConfig(self.word_path, self.correct, self.cache)

    async def startup(self):
        await scrape([word.get_word() for word in self.words], self.cache)

    def run(self):
        try:
            self.iter = iter(self.words)
            self.next = next(self.iter)

            self.settings = termios.tcgetattr(sys.stdin.fileno())
            tty.setraw(sys.stdin.fileno())

            self.entry()

            cont = True
            while cont:
                code = sys.stdin.read(1)
                cont = self.handle_code(code)

            if (
                set(word.show_word() for word in self.words).difference(self.correct)
                == set()
            ):
                self.correct = set()
        except:
            self.shutdown()
            raise
        finally:
            self.shutdown()

    def shutdown(self):
        if hasattr(self, "settings"):
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)
        if hasattr(self, "correct"):
            with open(self.correct_path, "w", encoding="utf-8") as correct_file:
                for correct in self.correct:
                    correct_file.write(f"{correct}\n")
        if hasattr(self, "cache"):
            self.cache.save()

    def handle_code(self, code):
        if code == "\x03":
            raise KeyboardInterrupt

        if code == "e":
            self.entry()
        elif code == "d":
            self.show_word()
        elif code == "c":
            self.chart()
        elif code == "u":
            self.usage()
        elif code == "r":
            self.refresh_cache()
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
        entry = self.next.entry()
        if entry is None:
            return
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)
        print("\033c", end="")
        print(f"{entry}")
        tty.setraw(sys.stdin)

    def usage(self):
        usage = self.next.show_usage()
        if usage is None:
            return
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)
        print("\033c", end="")
        print(f"{usage}")
        tty.setraw(sys.stdin)

    def chart(self):
        chart = self.next.chart()
        if chart is None:
            return
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)
        print("\033c", end="")
        print(f"{chart}")
        tty.setraw(sys.stdin)

    def refresh_cache(self):
        self.cache[self.next.show_word()] = refresh(self.next.show_word())

    def show_word(self):
        word = self.next.show_word()
        if word is None:
            return
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)
        print("\033c", end="")
        print(f"{word}")
        tty.setraw(sys.stdin)
