import os

from PySide6.QtCore import QMimeData, Qt, Signal
from PySide6.QtGui import QDrag, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QScrollArea,
    QVBoxLayout,
    QWidget,
    QPushButton,
    QSizePolicy,
)
import orjson
import qdarktheme

from alum.widgets.custom_widgets import SlidingStackedWidget
from alum.widgets.settings_slide import TestSettings
from alum.widgets.review_window import ReviewTestWindow
from alum.constants import ORJSON_OPTIONS


# TODO Pause feature
# TODO milisecond instead of second


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Create data.json if it has not been created before
        data_path = os.path.join(self.get_root_abspath(), "data.json")
        if not os.path.exists(data_path):
            with open(data_path, "w") as f:
                f.write("{}")

        # Window
        self.setWindowTitle("ALUM")
        self.setFixedSize(900, 460)

        # Layout and central widget
        self.root = QWidget()
        self.setCentralWidget(self.root)
        self.root_layout = QVBoxLayout()
        self.root.setLayout(self.root_layout)
        self.root_layout.setContentsMargins(5, 5, 5, 5)

        # Main title
        title = QLabel("Aplikasi Latihan UTBK Mandiri")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 28pt")
        self.root_layout.addWidget(title)

        # Main stacked widget
        self.main = SlidingStackedWidget()
        self.root_layout.addWidget(self.main)

        # Init UI
        self.init_home_slide()

    def init_home_slide(self):
        # Home slide widget
        home_slide = QWidget()
        home_slide.setLayout(QHBoxLayout())
        self.main.addWidget(home_slide)

        # Test list
        self.review_test = ReviewTestPane()
        home_slide.layout().addWidget(self.review_test)

        # Start button
        start_button_container = QWidget()
        start_button_container.setLayout(QHBoxLayout())
        start_button_container.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding
        )
        home_slide.layout().addWidget(start_button_container)

        # "Mulai" button
        start_button = QPushButton("Mulai")
        start_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        start_button.setStyleSheet("font-size: 18px; padding: 8px")
        start_button.clicked.connect(self.start_slide)
        start_button_container.layout().addWidget(
            start_button, alignment=Qt.AlignCenter
        )

    # This will only be used outside of this class,
    # because this file is in the root directory, but other files are inside
    # another directory
    def get_root_abspath(self):
        return os.path.dirname(os.path.abspath(__file__))

    # When "Mulai" button is clicked
    def start_slide(self):
        # If the user already start a test before, and they want to start another test
        # remove all slide ahead
        if self.main.count() > 1:
            # Delete from the last slide, so it doesn't mess up the index
            for idx in reversed(range(1, self.main.count())):
                widget = self.main.widget(idx)
                self.main.removeWidget(widget)

        settings = TestSettings(self.main)
        self.main.addWidget(settings)

        self.main.slideInNext()

    def closeEvent(self, event):
        # also close all test review windows
        self.review_test.test_review_windows = []
        event.accept()


# Test list on the left side of the window
class ReviewTestPane(QWidget):
    def __init__(self):
        super().__init__()

        self.abspath = os.path.dirname(os.path.abspath(__file__))
        self.data_path = os.path.join(self.abspath, "data.json")
        self.test_review_windows = []

        self.setLayout(QVBoxLayout())
        self.setFixedWidth(300)

        # Side pane title
        label = QLabel("Daftar tes:")
        label.setStyleSheet("margin: 5px;font-size: 14px;")
        label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.layout().addWidget(label)

        # Side pane list
        self.test_list_scroll = QScrollArea()
        self.test_list_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.layout().addWidget(self.test_list_scroll)

        # Update everytime it starts
        self.update_test_list()

    # Called everytime the program want to update test list because
    # an update on data.json
    def update_test_list(self):
        with open(self.data_path, "r") as f:
            self.data = orjson.loads(f.read())

        # Create a new test list widget everytime this function is called
        test_list = TestListWidget(self.data)
        test_list.testNameClicked.connect(self.review_test)
        test_list.deleteTestClicked.connect(self.delete_test)
        test_list.dataOrderChanged.connect(self.update_data_order)

        self.test_list_scroll.setWidget(test_list)

    # Open review test window
    def review_test(self, test_name: str):
        test_data = self.data[test_name]

        # Prevent opening an already opened test review
        for win in self.test_review_windows:
            if test_name == win.test_name:
                return

        # Add window to the list and show it
        review_test = ReviewTestWindow(test_name, test_data, self.data_path)
        review_test.windowClosed.connect(self.close_window)
        review_test.dataUpdated.connect(self.update_test_list)
        review_test.testNameRenamed.connect(self.update_test_name)
        self.test_review_windows.append(review_test)
        self.test_review_windows[-1].show()

    def close_window(self, widget):
        self.test_review_windows.remove(widget)

    # Delete test review from list
    def delete_test(self, test_name: str):
        # Confirmation
        qm = QMessageBox
        warning = qm.warning(
            self,
            "Konfirmasi",
            f'Apakah anda ingin menghapus tes "{test_name}"?',
            qm.Yes | qm.No,
        )
        if warning == qm.No:
            return

        # Close test review window if it opened
        # by deleting it from the test review windows list
        for win in self.test_review_windows:
            if win.test_name == test_name:
                self.test_review_windows.remove(win)

        # Update the file and the list
        self.data.pop(test_name)
        with open(self.data_path, "wb") as f:
            f.write(orjson.dumps(self.data, option=ORJSON_OPTIONS))

        self.update_test_list()

    # data Updated, just write it to the file, because the order already changed in TestListWidget
    def update_data_order(self, new_data):
        self.data = new_data

        with open(self.data_path, "wb") as f:
            f.write(orjson.dumps(self.data, option=ORJSON_OPTIONS))

    def update_test_name(self, old_name, new_name):
        idx = list(self.data.keys()).index(old_name)
        widget = self.test_list_scroll.widget().layout().itemAt(idx).widget()
        widget.test_name_btn.setText(new_name)

        # reload new data
        with open(self.data_path, "r") as f:
            self.data = orjson.loads(f.read())


class TestListWidget(QWidget):
    # Signal
    testNameClicked = Signal(str)
    deleteTestClicked = Signal(str)
    dataOrderChanged = Signal(dict)

    def __init__(self, data) -> None:
        super().__init__()
        self.data = data
        self.margin = 4

        self.setAcceptDrops(True)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.setLayout(QVBoxLayout())
        self.layout().setSpacing(0)
        self.layout().setContentsMargins(*[self.margin for _ in range(4)])

        # Add buttons (test name and delete test) to the grid
        test_names = list(self.data.keys())
        for name in test_names:
            test_item = TestListItem(name)
            test_item.testNameClicked.connect(self.review_test)
            test_item.deleteTestClicked.connect(self.delete_test)

            self.layout().addWidget(test_item)

    def review_test(self, test_name: str):
        self.testNameClicked.emit(test_name)

    def delete_test(self, test_name: str):
        self.deleteTestClicked.emit(test_name)

    def dragEnterEvent(self, event):
        event.accept()

    def dropEvent(self, event):
        pos = event.position()
        widget = event.source()

        width = widget.height()
        idx = int((pos.y() - self.margin) // width)

        prev_idx = int(widget.y() - self.margin) // width

        # Down one list
        move_down = pos.y() - (width // 2) > width * idx

        # I don't know what I'm doing here, but the code works
        # Go Down
        if prev_idx < idx:
            if not move_down:
                idx = idx - 1
        # Go Up
        elif prev_idx > idx:
            if move_down:
                idx = idx + 1

        # If it's at the end of the list, addWidget instead
        if idx == len(self.data.keys()):
            self.layout().addWidget(widget)
        else:
            self.layout().insertWidget(idx, widget)

        # Update list
        new_data = {}
        for n in range(self.layout().count()):
            test_name = self.layout().itemAt(n).widget().test_name
            new_data[test_name] = self.data[test_name]

        event.accept()
        self.dataOrderChanged.emit(new_data)


class TestListItem(QWidget):
    testNameClicked = Signal(str)
    deleteTestClicked = Signal(str)

    def __init__(self, test_name: str):
        super().__init__()
        self.test_name = test_name

        self.setLayout(QHBoxLayout())
        self.layout().setContentsMargins(4, 4, 4, 4)

        self.test_name_btn = QPushButton(test_name)
        self.test_name_btn.setFixedWidth(190)
        self.test_name_btn.setStyleSheet("text-align: left;")
        self.test_name_btn.clicked.connect(self.test_name_btn_clicked)
        self.layout().addWidget(self.test_name_btn)

        self.del_test_btn = QPushButton("Hapus")
        self.del_test_btn.clicked.connect(self.delete_btn_clicked)
        self.layout().addWidget(self.del_test_btn)

    def test_name_btn_clicked(self):
        self.testNameClicked.emit(self.test_name)

    def delete_btn_clicked(self):
        self.deleteTestClicked.emit(self.test_name)

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            drag = QDrag(self)
            mime = QMimeData()
            drag.setMimeData(mime)

            pixmap = QPixmap(self.size())
            self.render(pixmap)
            drag.setPixmap(pixmap)

            drag.exec(Qt.MoveAction)


if __name__ == "__main__":
    app = QApplication([])
    qdarktheme.setup_theme("auto")
    window = MainWindow()
    window.show()
    app.exec()
