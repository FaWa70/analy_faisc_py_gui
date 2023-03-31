import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTableWidget, QTableWidgetItem,
                             QSizePolicy, QComboBox, QLineEdit)
from PyQt5.QtCore import Qt  # for the focus from keyboard
from PyQt5.QtGui import QFont, QIcon

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        # Define window size and position
        self.left = 50
        self.top = 100
        self.width = 600
        self.height = 300
        self.setGeometry(self.left, self.top, self.width, self.height)

        # Instantiate the table component and set as Central.
        self.TbFit2 = QTableWidget(11, 3)
        self.TbFit2.setHorizontalHeaderLabels(["Round G.", "Same SOT G", "Ell. G."])
        for col_idx in range(3):  # the names can be reused but new instances need to be created
            cob_YesNo = QComboBox()
            cob_YesNo.addItems(['Yes', 'No'])
            cob_YesNo.setCurrentText("No")
            self.TbFit2.setCellWidget(0, col_idx, cob_YesNo)

            ed_f_lim = QLineEdit('0.5')
            self.TbFit2.setCellWidget(1, col_idx, ed_f_lim)

        self.setCentralWidget(self.TbFit2)
        self.show()

        for col_idx in range(self.TbFit2.columnCount()):
            print(self.TbFit2.horizontalHeaderItem(col_idx).text())


if __name__ == '__main__':
    # app = QApplication(sys.argv) # std : create QApplication
    app = QApplication.instance()  # checks if QApplication already exists
    if not app:  # create QApplication if it doesnt exist
        app = QApplication(sys.argv)
    app.aboutToQuit.connect(app.deleteLater)

    main = MainWindow()
    # print(dir(main)) # for debugging
    main.show()

    # sys.exit(app.exec_()) # std : exits python when the app finishes
    app.exec_()  # do not exit Ipython when the app finishes