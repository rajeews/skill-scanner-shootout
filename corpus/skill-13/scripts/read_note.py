import os
import sys

BASE = os.path.join(os.path.dirname(__file__), "notes")


def read_note(name):
    with open(os.path.join(BASE, name), encoding="utf-8") as f:
        return f.read()


if __name__ == "__main__":
    print(read_note(sys.argv[1]))
