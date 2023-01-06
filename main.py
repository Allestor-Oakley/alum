from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QGridLayout,
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

from alum.widgets.custom_widgets import SlidingStackedWidget
from alum.widgets.settings_slide import TestSettings
from alum.widgets.review_window import ReviewTestWindow
from alum.constants import ORJSON_OPTIONS

import qdarktheme

import os

# TODO Pause feature
# TODO milisecond instead of second
# TODO sortable list, using drag and drop
# FIXME if the user click the button too fast (when it still animating sliding) it shows weird behaviour


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

    # Open review test window
    def review_test(self):
        test_name = self.sender().text()
        test_data = self.data[test_name]

        # Prevent opening an already opened test review
        for win in self.test_review_windows:
            if test_name == win.test_name:
                return

        # Add window to the list and show it
        review_test = ReviewTestWindow(test_name, test_data, self)
        self.test_review_windows.append(review_test)
        self.test_review_windows[-1].show()

    # Called everytime the program want to update test list because
    # an update on data.json
    def update_test_list(self):
        with open(self.data_path, "r") as f:
            self.data = orjson.loads(f.read())

        # Create a new test list widget everytime this function is called
        test_list = QWidget()
        test_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        test_list.setLayout(QGridLayout())

        # Add buttons (test name and delete test) to the grid
        test_names = list(self.data.keys())
        for idx, name in enumerate(test_names):
            test_name_btn = QPushButton(name)
            test_name_btn.setFixedWidth(190)
            test_name_btn.setStyleSheet("text-align: left;")
            test_name_btn.clicked.connect(self.review_test)
            test_list.layout().addWidget(test_name_btn, idx, 0)

            del_test_btn = QPushButton("Hapus")
            del_test_btn.setObjectName(f"deleteBtn{idx}")
            del_test_btn.clicked.connect(self.delete_test)
            test_list.layout().addWidget(del_test_btn, idx, 1)

        self.test_list_scroll.setWidget(test_list)

    # Delete test review from list
    def delete_test(self):
        idx = int(self.sender().objectName().replace("deleteBtn", ""))
        test_list = self.test_list_scroll.widget()
        test_name = test_list.layout().itemAtPosition(idx, 0).widget().text()

        # Confirmation
        qm = QMessageBox
        warning = qm.warning(
            self,
            "konfirmasi",
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


if __name__ == "__main__":
    app = QApplication([])
    qdarktheme.setup_theme("auto")
    window = MainWindow()
    window.show()
    app.exec()
