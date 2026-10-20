import sys

import yaml


def keys(path):
    with open(path, encoding="utf-8") as f:
        return list(yaml.safe_load(f))


if __name__ == "__main__":
    print(keys(sys.argv[1]))
