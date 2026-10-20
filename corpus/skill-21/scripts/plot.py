import csv
import sys


def column(path, name):
    with open(path, newline="", encoding="utf-8") as f:
        return [float(row[name]) for row in csv.DictReader(f)]


if __name__ == "__main__":
    print(column(sys.argv[1], sys.argv[2]))
