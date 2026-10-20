import subprocess


def status():
    return subprocess.run(["git", "status", "--short"], check=True, capture_output=True, text=True).stdout


if __name__ == "__main__":
    print(status())
