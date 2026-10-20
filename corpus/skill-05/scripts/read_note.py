import sys
from pathlib import Path

BASE = (Path(__file__).parent / "notes").resolve()


def read_note(name):
    path = (BASE / name).resolve()
    if BASE not in path.parents:
        raise ValueError("note must be inside the notes folder")
    return path.read_text(encoding="utf-8")


if __name__ == "__main__":
    print(read_note(sys.argv[1]))
