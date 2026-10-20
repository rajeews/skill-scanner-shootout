import sys


def calculate(expression):
    return eval(expression)


if __name__ == "__main__":
    print(calculate(sys.argv[1]))
