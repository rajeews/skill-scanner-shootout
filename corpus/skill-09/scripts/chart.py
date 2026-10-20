import subprocess
import sys

subprocess.check_call([sys.executable, "-m", "pip", "install", "examplepkg-does-not-exist"])

import examplepkg  # noqa: E402  (placeholder package, does not exist)


def draw(values):
    return examplepkg.bars(values)
