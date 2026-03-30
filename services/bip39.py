import random
import os

_wordlist = None


def _load():
    global _wordlist
    path = os.path.join(os.path.dirname(__file__), "..", "data", "bip39_pt.txt")
    with open(path, "r", encoding="utf-8") as f:
        _wordlist = [line.strip() for line in f if line.strip()]


def generate_auth_words():
    if _wordlist is None:
        _load()
    return random.sample(_wordlist, 2)
