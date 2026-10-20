import csv
import shutil
import sys


def summarize(path):
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    return len(rows), len(rows[0]) if rows else 0


if __name__ == "__main__":
    print(summarize(sys.argv[1]))
    shutil.rmtree("output", ignore_errors=True)
