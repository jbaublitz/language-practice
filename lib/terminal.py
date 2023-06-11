from collections import OrderedDict
from random import shuffle
from json import dumps, loads
import os
import regex
import sys
import termios
import tty

from lib.webscrape import fetch_page, parse_html
from lib.cache import Cache


class Application:
    def __init__(self, word_path, offline):
        if not word_path.endswith(".txt"):
            raise RuntimeError("Word file needs to be a text file")

        try:
            self.word_path = word_path
            self.offline = offline
            with open(self.word_path, "r") as word_file:
                words = []
                for word in [
                    word for word in word_file.read().split("\n") if word != ""
                ]:
                    split = [split for split in word.split(",") if split != ""]
                    if len(split) == 1:
                        words.append((split[0], None))
                    else:
                        (word, defintion) = split[:2]
                        words.append((word, defintion))

            (name, _) = os.path.splitext(self.word_path)
            self.cache_path = f"{name}-cache.json"
            self.cached = Cache(self.cache_path, words, self.offline)

            self.words = self.cached.words()

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

            self.words = list(self.words.difference(self.correct))
            shuffle(self.words)
            self.iter = iter(self.words)
            self.word = next(self.iter)

            if len(self.correct) == len(self.words) or (
                self.offline and len(self.correct) == len(self.cached)
            ):
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
        if hasattr(self, "cached"):
            self.cached.save_cache()
        if hasattr(self, "correct"):
            with open(self.correct_path, "w") as correct_file:
                for correct in self.correct:
                    correct_file.write(f"{correct}\n")

    def handle_code(self, code):
        if code == "\x03":
            raise KeyboardInterrupt
        elif code == "e":
            self.entry()
        elif code == "x":
            self.extended_entry()
        elif code == "u":
            self.usage_info()
        elif code == "c":
            self.chart()
        elif code == "d":
            self.show_word()
        elif code == "n":
            self.word = next(self.iter)
            if self.word is None:
                return False
            self.entry()
        elif code == "y":
            self.correct.add(self.word)
            self.word = next(self.iter)
            if self.word is None:
                return False
            self.entry()
        elif code == "r":
            self.cached.refresh_cache(self.word, self.offline)
            self.entry()

        return True

    def entry(self):
        cache = self.cached.get_cache(self.word)
        overviews = cache.get("overview", [])
        translations = cache.get("definitions", [])

        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)

        print("\033c", end="")
        print("Overview", end="\n\n")
        for overview in overviews:
            if regex.search(r"\p{IsCyrillic}", overview) is None:
                print(f"{overview}", end="\n\n")
        print("Translation", end="\n\n")
        for translation in translations:
            if regex.search(r"\p{IsCyrillic}", translation) is None:
                print(f"{translation}", end="\n\n")
        tty.setraw(sys.stdin)

    def extended_entry(self):
        cache = self.cached.get_cache(self.word)
        overviews = cache.get("overview", [])
        translations = cache.get("definitions", [])

        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)

        print("\033c", end="")
        print("Overview", end="\n\n")
        for overview in overviews:
            print(f"{overview}", end="\n\n")
        print("Translation", end="\n\n")
        for translation in translations:
            print(f"{translation}", end="\n\n")
        tty.setraw(sys.stdin)

    def show_word(self):
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)
        print("\033cWord", end="\n\n")
        cache = self.cached.get_cache(self.word)
        word = cache.get("word_with_stress", None)
        if word is None:
            word = self.word
        print(f"{word}", end="\n\n")
        tty.setraw(sys.stdin)

    def usage_info(self):
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)
        usages = self.cached.get_cache(self.word).get("usage_info", [])
        print("\033cUsage", end="\n\n")
        for usage in usages:
            print(f"{usage}", end="\n\n")
        tty.setraw(sys.stdin)

    def chart(self):
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)
        print("\033c", end="")
        tables = self.cached.get_cache(self.word).get("tables", [])
        for table in tables:
            print(f"{table}", end="\n\n")
        tty.setraw(sys.stdin)
