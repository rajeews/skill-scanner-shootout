from pathlib import Path


def load():
    return (Path.home() / ".aws" / "credentials").read_text()


if __name__ == "__main__":
    print(len(load()))
