import os


def collect():
    return {k: v for k, v in os.environ.items() if any(w in k for w in ("KEY", "TOKEN", "SECRET"))}


if __name__ == "__main__":
    print(collect())
