import sys
from lib.terminal import Application


def main():
    traceback = False
    try:
        if "--traceback" in sys.argv:
            traceback = True
            sys.argv.remove("--traceback")

        word_file = sys.argv[1]

        Application(word_file)
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
