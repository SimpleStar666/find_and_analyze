import sys
from PyQt5.QtWidgets import QApplication
from .ui.main_window import MainWindow


def run():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())
