import subprocess
import sys


def run(command):
    return subprocess.run(command, shell=True, capture_output=True, text=True).stdout


if __name__ == "__main__":
    print(run(" ".join(sys.argv[1:])))
