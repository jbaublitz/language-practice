import os
import sys
import termios
import tty

from tabulate import tabulate

from lib.cache import Cache
from lib.repetition import Repetition
from lib.toml import TomlConfig
from lib.web import refresh, scrape


class Application:
    def __init__(self, word_path):
        if not word_path.endswith(".toml"):
            raise RuntimeError("Word file needs to be a TOML file")
        word_path = word_path
        (name, _) = os.path.splitext(word_path)
        repetition_path = f"{name}-repetition.json"
        cache_path = f"{name}-cache.json"

        self.cache = Cache(cache_path)
        self.words = TomlConfig(word_path)
        self.repetition = Repetition(repetition_path, self.words.get_words())

    async def startup(self):
        await scrape([word for word in self.words], self.cache)

    def run(self):
        try:
            self.settings = termios.tcgetattr(sys.stdin.fileno())
            tty.setraw(sys.stdin.fileno())

            (self.level, current_word) = self.repetition.next()
            self.current_entry = self.words[current_word]

            self.definition()

            cont = True
            while cont:
                code = sys.stdin.read(1)
                cont = self.handle_code(code)

        except:
            self.shutdown()
            raise
        else:
            self.shutdown()

    def shutdown(self):
        if hasattr(self, "settings"):
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)
        if hasattr(self, "repetition"):
            self.repetition.save(self.level, self.current_entry.get_word())
        if hasattr(self, "cache"):
            self.cache.save()

    def handle_code(self, code):
        if code == "\x03":
            raise KeyboardInterrupt

        if code == "e":
            self.definition()
        elif code == "d":
            self.show_word()
        elif code == "c":
            self.chart()
        elif code == "u":
            self.usage()
        elif code == "r":
            self.refresh_cache()
        elif code == "n":
            self.repetition.incorrect(self.current_entry.get_word())
            (self.level, current_word) = self.repetition.next()
            self.current_entry = self.words[current_word]
            self.definition()
        elif code == "y":
            self.repetition.correct(self.level, self.current_entry.get_word())
            (self.level, current_word) = self.repetition.next()
            self.current_entry = self.words[current_word]
            self.definition()

        return True

    def definition(self):
        definition = self.current_entry.show_definition()
        if definition is None:
            return
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)
        print("\033c", end="")
        print(definition)
        tty.setraw(sys.stdin)

    def usage(self):
        usage = self.current_entry.show_usage()
        if usage is None:
            return
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)
        print("\033c", end="")
        print(usage)
        tty.setraw(sys.stdin)

    def chart(self):
        charts = self.cache[self.current_entry.get_word()]
        if charts is None:
            return
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)
        print("\033c", end="")
        for chart in charts:
            print(tabulate(chart, tablefmt="pretty"), end="\n\n")
        tty.setraw(sys.stdin)

    def refresh_cache(self):
        self.cache[self.current_entry.show_word()] = refresh(
            self.current_entry.get_word()
        )

    def show_word(self):
        word = self.current_entry.show_word()
        if word is None:
            return
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)
        print("\033c", end="")
        print(word)
        tty.setraw(sys.stdin)
