import sys
from PyQt5.QtWidgets import QApplication
from gui.tsp_gui import TSPApp

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TSPApp()
    window.show()
    sys.exit(app.exec_())
