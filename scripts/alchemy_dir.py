"""Where the upstream (alchemy) working copy lives; the same lookup as
alchemy-dir.sh: $ALCHEMY_DIR, else the first line of the git-ignored file
.alchemy-dir in the repo root, else <repo>/work/alchemy. A leading ~ is expanded.

    from alchemy_dir import ALCHEMY, GAME     # GAME is <ALCHEMY>/games/tbs
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def alchemy_dir():
    d = os.environ.get("ALCHEMY_DIR", "").strip()
    if not d:
        f = os.path.join(ROOT, ".alchemy-dir")
        if os.path.isfile(f):
            with open(f, encoding="utf-8") as fh:
                d = fh.readline().strip()
    if not d:
        d = os.path.join(ROOT, "work", "alchemy")
    d = os.path.expanduser(d)
    if not os.path.isabs(d):
        d = os.path.join(ROOT, d)
    return os.path.normpath(d)


ALCHEMY = alchemy_dir()
GAME = os.path.join(ALCHEMY, "games", "tbs")

if __name__ == "__main__":
    print(ALCHEMY)
