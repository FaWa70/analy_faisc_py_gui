import sys  # still useful ? yes if not it would be grey
import numpy as np

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget,
                             QGridLayout, QVBoxLayout, QHBoxLayout, QSplitter,
                             QSlider, QTabWidget, QButtonGroup, QRadioButton,
                             QPushButton, QCheckBox, QLabel, QFileDialog, QLineEdit,
                             QSpinBox, QProgressBar, QComboBox, QTableWidget, QTableWidgetItem,
                             QSizePolicy, QScrollArea)
from PyQt5.QtCore import Qt, QRectF  # for the focus from keyboard
from PyQt5.QtGui import QFont, QFontMetricsF, QIcon

class MyTableWidget(QWidget):
    def __init__(self, parent):
        print('__init__ called')
        super().__init__(parent)

        # Initialize tab screen
        self.tabs = QTabWidget()

        # Add pages (tab1, tab2...) to tabWidget (tabs)
        self.tab1 = QWidget()
        self.tabs.addTab(self.tab1, "Load and pre-process images")  # includes noise subtraction
        self.tab2 = QWidget()
        self.tabs.addTab(self.tab2, 'Full analysis of one image')

        message = "New message. "
        for count in range(8):
            message += message
        self.LbTitleSub2 = QLabel(message)
        self.LbTitleSub2.setWordWrap(True)

        self.LbTitleSub1 = QLabel(message)
        self.LbTitleSub1.setWordWrap(True)


        # make tab 1
        tab1_scr_area = QScrollArea(self)
        tab1_scr_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        tab1_scr_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        tab1_scr_area.setWidget(self.LbTitleSub1)

        tab1_layout = QVBoxLayout(self)
        tab1_layout.addWidget(tab1_scr_area)
        self.tab1.setLayout(tab1_layout)

        # make tab 2
        tab2_layout = QVBoxLayout(self)
        tab2_layout.addWidget(self.LbTitleSub2)
        self.tab2.setLayout(tab2_layout)

        # Add tabs-widget to centralwidget
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.tabs)


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setGeometry(200, 100, 300, 200)
        # Instantiate the tab component and set as Central.
        self.tw = MyTableWidget(self)
        self.setCentralWidget(self.tw)
        self.show()

####################################################
if __name__ == "__main__":
    app = QApplication(sys.argv)  # std : create and launch Application
    main = MainWindow()  # self.show() is the last line of MainWindow.__init__()
    sys.exit(app.exec_())  # std : exits python when the app finishes
