import sys
import os


def get_base_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


if __name__ == "__main__":
    base = get_base_path()
    os.chdir(base)
    if base not in sys.path:
        sys.path.insert(0, base)

    from src.app import run
    run()
