"""
Terminal application interface.
"""
import os
import sys
import termios
import tty

from tabulate import tabulate

from language_practice.cache import Cache
from language_practice.repetition import Repetition
from language_practice.toml import TomlConfig
from language_practice.web import refresh, scrape


class Application:
    """
    Handles the interactive user input from the terminal.
    """

    def __init__(self, word_path, reset):
        if not word_path.endswith(".toml"):
            raise RuntimeError("Word file needs to be a TOML file")

        (name, _) = os.path.splitext(word_path)
        repetition_path = f"{name}-repetition.json"
        cache_path = f"{name}-cache.json"

        if reset:
            try:
                os.remove(repetition_path)
                os.remove(cache_path)
            except FileNotFoundError:
                pass

        self.settings = termios.tcgetattr(sys.stdin.fileno())

        self.cache = Cache(cache_path)
        self.words = TomlConfig(word_path)
        self.lang = self.words.get_lang()
        self.repetition = Repetition(repetition_path, self.words.get_words())

        current_word = self.repetition.peek()
        self.current_entry = self.words[current_word]

    async def startup(self):
        """
        Start up application.
        """
        await scrape(self.words.get_words(), self.cache, self.lang)

    def run(self):
        """
        Run application.
        """
        try:
            tty.setraw(sys.stdin.fileno())

            self.definition()

            cont = True
            while cont:
                code = sys.stdin.read(1)
                cont = self.handle_code(code)

        except:
            self.shutdown()
            raise

        self.shutdown()

    def shutdown(self):
        """
        Shutdown application.
        """
        if hasattr(self, "settings"):
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)
        if hasattr(self, "repetition"):
            self.repetition.save()
        if hasattr(self, "cache"):
            self.cache.save()

    def handle_code(self, code):
        """
        Handle user input.
        """
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
            self.repetition.incorrect()
            current_word = self.repetition.peek()
            self.current_entry = self.words[current_word]
            self.definition()
        elif code == "y":
            self.repetition.correct()
            current_word = self.repetition.peek()
            self.current_entry = self.words[current_word]
            self.definition()

        return True

    def definition(self):
        """
        Display the definition for the current word.
        """
        definition = self.current_entry.show_definition()
        if definition is None:
            return
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)
        print("\033c", end="")
        print(definition)
        tty.setraw(sys.stdin)

    def usage(self):
        """
        Display the usage for the current word.
        """
        usage = self.current_entry.show_usage()
        if usage is None:
            return
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)
        print("\033c", end="")
        print(usage)
        tty.setraw(sys.stdin)

    def chart(self):
        """
        Display the chart for the current word.
        """
        charts = self.current_entry.get_charts()
        if charts is None:
            cache = self.cache[self.current_entry.get_word()]
            if "charts" not in cache:
                return
            charts = cache["charts"]
        else:
            charts = [charts]

        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)
        print("\033c", end="")
        for chart in charts:
            print(tabulate(chart, tablefmt="pretty"), end="\n\n")
        tty.setraw(sys.stdin)

    def refresh_cache(self):
        """
        Refresh the cache for the current word.
        """
        self.cache[self.current_entry.show_word()] = refresh(
            self.current_entry.get_word(), self.lang
        )

    def show_word(self):
        """
        Show the current word.
        """
        word = self.current_entry.show_word()
        if word is None:
            return
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)
        print("\033c", end="")
        print(word)
        cache = self.cache[self.current_entry.get_word()]
        if "comparative" in cache:
            comparative = ", ".join(cache["comparative"])
            print(f"\n\n{comparative}", end="")
        if "superlative" in cache:
            superlative = ", ".join(cache["superlative"])
            print(f"\n\n{superlative}", end="")
        if "adjective_forms" in cache:
            adj_forms = ", ".join(cache["adjective_forms"])
            print(f"\n\n{adj_forms}", end="")
        tty.setraw(sys.stdin)
