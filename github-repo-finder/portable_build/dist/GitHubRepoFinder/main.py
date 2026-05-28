import sys
import os


def get_base_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def setup_qt_env():
    base = get_base_path()
    python_dir = os.path.join(base, "python")
    site_packages = os.path.join(python_dir, "Lib", "site-packages")

    qt_plugins = os.path.join(site_packages, "PyQt5", "Qt5", "plugins")
    if os.path.exists(qt_plugins):
        os.environ["QT_PLUGIN_PATH"] = qt_plugins
        platforms_dir = os.path.join(qt_plugins, "platforms")
        if os.path.exists(platforms_dir):
            os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = platforms_dir

    qt_bin = os.path.join(site_packages, "PyQt5", "Qt5", "bin")
    if os.path.exists(qt_bin):
        current_path = os.environ.get("PATH", "")
        os.environ["PATH"] = qt_bin + os.pathsep + current_path


if __name__ == "__main__":
    base = get_base_path()
    os.chdir(base)
    if base not in sys.path:
        sys.path.insert(0, base)

    setup_qt_env()

    from src.app import run
    run()
