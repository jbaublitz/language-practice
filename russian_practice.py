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
    try:
        if "--traceback" in sys.argv:
            traceback = True
            sys.argv.remove("--traceback")

        word_file = sys.argv[1]

        app = Application(word_file)
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
