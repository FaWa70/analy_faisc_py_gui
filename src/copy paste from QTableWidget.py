# add imports
import sys, csv, io
import pandas as pd, numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets


class Window(QtWidgets.QWidget):
    def __init__(self):
        super(Window, self).__init__()
        self.model = QtGui.QStandardItemModel(self)
        self.model.setSortRole(QtCore.Qt.UserRole)
        self.tableView = QtWidgets.QTableView()
        self.tableView.setSortingEnabled(True)
        self.tableView.setModel(self.model)
        # install event filter
        self.tableView.installEventFilter(self)
        self.button = QtWidgets.QPushButton('Open CSV', self)
        self.button.clicked.connect(self.handleButton)
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.tableView)
        layout.addWidget(self.button)

    # add event filter
    def eventFilter(self, source, event):
        if (event.type() == QtCore.QEvent.KeyPress and
                event.matches(QtGui.QKeySequence.Copy)):
            self.copySelection()
            return True
        return super(Window, self).eventFilter(source, event)

    # add copy method
    def copySelection(self):
        selection = self.tableView.selectedIndexes()
        if selection:
            rows = sorted(index.row() for index in selection)
            columns = sorted(index.column() for index in selection)
            rowcount = rows[-1] - rows[0] + 1
            colcount = columns[-1] - columns[0] + 1
            table = [[''] * colcount for _ in range(rowcount)]
            for index in selection:
                row = index.row() - rows[0]
                column = index.column() - columns[0]
                table[row][column] = index.data()
            stream = io.StringIO()
            csv.writer(stream).writerows(table)
            QtWidgets.qApp.clipboard().setText(stream.getvalue())

    def handleButton(self):
        filters = (
            'CSV files (*.csv *.txt)',
            'Excel Files (*.xls *.xml *.xlsx *.xlsm)',
        )
        path, filter = QtWidgets.QFileDialog.getOpenFileName(
            self, 'Open File', '', ';;'.join(filters))
        if path:
            csv = filter.startswith('CSV')
            if csv:
                dataframe = pd.read_csv(path)
            else:
                dataframe = pd.read_excel(path)
            self.model.setRowCount(0)
            dateformat = '%m/%d/%Y'
            rows, columns = dataframe.shape
            for row in range(rows):
                items = []
                for column in range(columns):
                    field = dataframe.iat[row, column]
                    if csv and isinstance(field, str):
                        try:
                            field = pd.to_datetime(field, format=dateformat)
                        except ValueError:
                            pass
                    if isinstance(field, pd.Timestamp):
                        text = field.strftime(dateformat)
                        data = field.timestamp()
                    else:
                        text = str(field)
                        if isinstance(field, np.number):
                            data = field.item()
                        else:
                            data = text
                    item = QtGui.QStandardItem(text)
                    item.setData(data, QtCore.Qt.UserRole)
                    items.append(item)
                self.model.appendRow(items)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = Window()
    window.setGeometry(500, 150, 600, 400)
    window.show()
    sys.exit(app.exec_())
