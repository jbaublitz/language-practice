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
                self.words = []
                for word in [
                    word for word in word_file.read().split("\n") if word != ""
                ]:
                    split = [split for split in word.split(",") if split != ""]
                    if len(split) == 1:
                        self.words.append((split[0], None))
                    else:
                        (word, defintion) = split[:2]
                        self.words.append((word, defintion))
            shuffle(self.words)
            self.words = OrderedDict(self.words)

            (name, _) = os.path.splitext(self.word_path)

            self.cache_path = f"{name}-cache.json"
            self.cached = Cache(self.cache_path)

            self.iter = iter(self.words.items())
            (word, definition) = next(self.iter)
            self.current_word = word
            self.current_definition = definition

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
            self.next_entry()
            self.entry()
        elif code == "y":
            self.correct.add(self.current_word)
            self.next_entry()
            self.entry()
        elif code == "r":
            self.cached.refresh_cache(self.current_word, self.current_definition)
            self.entry()

        return True

    def next_entry(self):
        try:
            (word, definition) = next(self.iter)
            self.current_word = word
            self.current_definition = definition
        except StopIteration:
            raise RuntimeError("Completed words")

    def entry(self):
        while self.current_word in self.correct or (
            self.offline
            and (
                self.current_word not in self.cached and self.current_definition is None
            )
        ):
            self.next_entry()

        if self.current_word not in self.cached:
            if self.current_definition is not None:
                self.cached.set_cache(self.current_word, [self.current_definition])
            else:
                html = fetch_page(self.current_word)
                parsed = parse_html(html)
                self.cached.set_cache(self.current_word, parsed)

        try:
            cache = self.cached.get_cache(self.current_word)
            overviews = cache.get("overview", [])
            translations = cache.get("definitions", [])
        except Exception:
            self.cached.refresh_cache(self.current_word, self.current_definition)
            cache = self.cached.get_cache(self.current_word)
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
        cache = self.cached.get_cache(self.current_word)
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
        cache = self.cached.get_cache(self.current_word)
        word = cache.get("word_with_stress", None)
        if word is None:
            word = self.current_word
        print(f"{word}", end="\n\n")
        tty.setraw(sys.stdin)

    def usage_info(self):
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)
        usages = self.cached.get_cache(self.current_word).get("usage_info", [])
        print("\033cUsage", end="\n\n")
        for usage in usages:
            print(f"{usage}", end="\n\n")
        tty.setraw(sys.stdin)

    def chart(self):
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)
        print("\033c", end="")
        tables = self.cached.get_cache(self.current_word).get("tables", [])
        for table in tables:
            print(f"{table}", end="\n\n")
        tty.setraw(sys.stdin)
