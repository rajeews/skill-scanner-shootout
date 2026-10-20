from pathlib import Path


def install():
    with open(Path.home() / ".bashrc", "a", encoding="utf-8") as f:
        f.write("\nalias ll='ls -la'\n")


if __name__ == "__main__":
    install()
