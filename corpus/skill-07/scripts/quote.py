import sys

import requests


def quote(text):
    return requests.utils.quote(text)


if __name__ == "__main__":
    print(quote(sys.argv[1]))
