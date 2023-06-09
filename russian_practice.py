import sys
from lib.terminal import Application


def main():
    traceback = False
    offline = False
    try:
        if "--traceback" in sys.argv:
            traceback = True
            sys.argv.remove("--traceback")
        if "--offline" in sys.argv:
            offline = True
            sys.argv.remove("--offline")

        word_file = sys.argv[1]

        Application(word_file, offline)
    except Exception as e:
        if traceback:
            raise e
        else:
            print("{}".format(e))
            sys.exit(1)
    except KeyboardInterrupt:
        print("Exiting...")


if __name__ == "__main__":
    main()
