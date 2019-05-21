import sys

from PyQt5.QtWidgets import QApplication, QWidget


class STLAnimator(QWidget):
    def __init__(self):
        super().__init__()

        self.title = f"STL Animator"

    def initUI(self):
        pass


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = STLAnimator()
    sys.exit(app.exec_())
