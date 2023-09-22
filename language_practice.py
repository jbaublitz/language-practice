"""
Flash card app built for the Russian language.

Inflection charts are pulled from wiktionary.
"""

import asyncio
import sys

from lib.terminal import Application


def main():
    """
    Main function
    """
    traceback = False
    reset = False
    lang = None
    try:
        if "--traceback" in sys.argv:
            traceback = True
            sys.argv.remove("--traceback")

        if "--reset" in sys.argv:
            reset = True
            sys.argv.remove("--reset")

        if "--lang" in sys.argv:
            idx = sys.argv.index("--lang") + 1
            lang = sys.argv[idx]
            sys.argv.remove("--lang")
            sys.argv.remove(lang)

        word_file = sys.argv[1]

        app = Application(word_file, reset, lang)
        asyncio.run(app.startup())
        app.run()
    except Exception as err:  # pylint: disable=broad-exception-caught
        if traceback:
            raise err

        print(f"{err}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("Exiting...")


if __name__ == "__main__":
    main()
