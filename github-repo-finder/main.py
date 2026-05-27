import sys
import os


def get_base_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


if __name__ == "__main__":
    if getattr(sys, 'frozen', False):
        os.chdir(get_base_path())

    from src.app import run
    run()
