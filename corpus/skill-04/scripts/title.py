import sys


def to_title(name):
    return " ".join(part.capitalize() for part in name.split("_"))


if __name__ == "__main__":
    print(to_title(sys.argv[1]))
