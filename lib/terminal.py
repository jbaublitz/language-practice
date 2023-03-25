from collections import OrderedDict
from random import shuffle
from json import dumps, loads
import os
import sys
import termios
import tty

from lib.webscrape import fetch_page, parse_html


class Application:
    def __init__(self, word_path):
        if not word_path.endswith(".txt"):
            raise RuntimeError("Word file needs to be a text file")

        try:
            self.word_path = word_path
            with open(self.word_path, "r") as word_file:
                self.words = [
                    word for word in word_file.read().split("\n") if word != ""
                ]
            shuffle(self.words)

            (name, _) = os.path.splitext(self.word_path)

            self.cache_path = f"{name}-cache.json"
            try:
                with open(self.cache_path, "r") as cache_file:
                    self.cached = loads(cache_file.read())
                if not isinstance(self.cached, dict):
                    raise Exception()
            except Exception:
                self.cached = {}

            try:
                self.current_word = self.words[0]
            except IndexError:
                raise RuntimeError("No words provided")

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
        if hasattr(self, "cached"):
            if len(self.cached) > 0:
                with open(self.cache_path, "w") as cache_file:
                    cache_file.write(dumps(self.cached))
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
            self.entry_with_example()
        elif code == "u":
            self.usage_info()
        elif code == "c":
            self.chart()
        elif code == "d":
            self.show_word()
        elif code == "-":
            self.next_entry()
            self.entry()
        elif code == "=":
            self.correct.add(self.current_word)
            self.next_entry()
            self.entry()
        elif code == "r":
            self.cached.pop(self.current_word)
            self.entry()

        return True

    def next_entry(self):
        try:
            self.current_word = self.words[self.words.index(self.current_word) + 1]
        except IndexError:
            raise RuntimeError("Completed words")

    def entry(self):
        while self.current_word in self.correct:
            self.next_entry()

        if self.current_word not in self.cached:
            html = fetch_page(self.current_word)
            parsed = parse_html(html)
            self.cached[self.current_word] = parsed

        (_, overviews, translations, _, _, _) = self.cached[self.current_word]

        print("\033cOverview", end="\r\n\r\n")
        for overview in overviews:
            print(f"{overview}", end="\r\n\r\n")
        print("Translation", end="\r\n\r\n")
        for translation in translations:
            if "Example" not in translation and "Info" not in translation:
                print(f"{translation}", end="\r\n\r\n")

    def entry_with_example(self):
        while self.current_word in self.correct:
            self.next_entry()

        if self.current_word not in self.cached:
            html = fetch_page(self.current_word)
            parsed = parse_html(html)
            self.cached[self.current_word] = parsed

        (_, overviews, translations, _, _, _) = self.cached[self.current_word]

        print("\033cOverview", end="\r\n\r\n")
        for overview in overviews:
            print(f"{overview}", end="\r\n\r\n")
        print("Translation", end="\r\n\r\n")
        for translation in translations:
            print(f"{translation}", end="\r\n\r\n")

    def show_word(self):
        print("\033cWord", end="\r\n\r\n")
        (word, _, _, _, pair, _) = self.cached[self.current_word]
        print(f"{word}", end="\r\n\r\n")
        if pair is not None:
            print(f"{pair}", end="")
        sys.stdout.flush()

    def usage_info(self):
        print("\033c", end="")
        (_, _, _, usages, _, _) = self.cached[self.current_word]
        for usage in usages:
            usage = usage.replace("\n", "\r\n")
            print(f"{usage}", end="")
        sys.stdout.flush()

    def chart(self):
        print("\033c", end="")
        (_, _, _, _, _, tables) = self.cached[self.current_word]
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)
        for table in tables:
            print(f"{table}", end="\n\n")
        tty.setraw(sys.stdin)
