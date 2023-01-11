from datetime import datetime

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
import orjson

from .custom_widgets import SlidingStackedWidget
from .answer_slide import TestNameDialog
from ..constants import DAY_INDO, GREEN_BTN_QSS, MONTH_INDO, ORJSON_OPTIONS, TIME_FORMAT


class ReviewTestWindow(QWidget):
    SORT_METHODS = ("number", "accuracy", "time")

    # Signals
    dataUpdated = Signal()
    windowClosed = Signal(QWidget)

    def __init__(self, test_name: str, test_data: dict, data_path: str):
        super().__init__()
        self.test_name = test_name
        self.test_data = test_data
        self.data_path = data_path

        self.setFixedSize(500, 550)
        self.setWindowTitle(f"Tinjauan tes '{test_name}'")
        self.setLayout(QVBoxLayout())

        #########################################
        # Main slide
        #########################################
        self.main_slide = SlidingStackedWidget()
        self.layout().addWidget(self.main_slide)

        #########################################
        # Nav Buttons
        #########################################
        self.nav_buttons = QWidget()
        self.nav_buttons.setLayout(QHBoxLayout())

        self.prev_btn = QPushButton("Kembali")
        self.prev_btn.clicked.connect(self.main_slide.slideInPrev)
        spacer = QWidget()
        self.next_btn = QPushButton("Lanjut")
        self.next_btn.clicked.connect(self.main_slide.slideInNext)
        self.nav_buttons.layout().addWidget(self.prev_btn)
        self.nav_buttons.layout().addWidget(spacer)
        self.nav_buttons.layout().addWidget(self.next_btn)
        self.layout().addWidget(self.nav_buttons)

        #########################################
        # Init slide
        #########################################
        self.init_stat_slide()
        self.init_test_review_slide()
        self.init_test_note_slide()

    def closeEvent(self, event):
        self.windowClosed.emit(self)
        # Quit
        event.accept()

    def init_stat_slide(self):
        self.stats_slide = QWidget()
        self.stats_slide.setLayout(QVBoxLayout())
        self.stats_slide.layout().setAlignment(Qt.AlignTop)

        ########################################
        # Title and rename button
        ########################################
        # title
        self.title_test_name = QLabel(f"Tinjauan tes '{self.test_name}'")
        self.title_test_name.setStyleSheet("font-size: 22px;")
        self.stats_slide.layout().addWidget(self.title_test_name)

        # rename button
        rename_container = QWidget()
        rename_container.setLayout(QHBoxLayout())
        self.stats_slide.layout().addWidget(rename_container)

        rename_spacer = QWidget()
        rename_spacer.setFixedWidth(300)
        rename_container.layout().addWidget(rename_spacer)

        rename_button = QPushButton("Ubah nama tes")
        rename_button.clicked.connect(self.rename_test)
        rename_container.layout().addWidget(rename_button)

        ########################################
        # Stats
        ########################################
        stats_list = QWidget()
        stats_list.setLayout(QFormLayout())
        stats_list.setStyleSheet("font-size: 14px;")

        left_colon = ":    "

        # Date
        tests_date = self.test_data["tanggal_tes"]
        tests_date = self.format_date(tests_date)
        stats_list.layout().addRow(
            QLabel("Tanggal tes"), QLabel(f"{left_colon}{tests_date}")
        )

        # Time limit
        time_limit = int(self.test_data["batas_waktu"])
        if time_limit != 0:
            self.format_time(str(time_limit))
        else:
            time_limit = "tidak ada"
        stats_list.layout().addRow(
            QLabel("Batas Waktu"), QLabel(f"{left_colon}{time_limit}")
        )

        # Question counts
        question_counts = self.test_data["jumlah_soal"]
        stats_list.layout().addRow(
            QLabel("Jumlah Soal"), QLabel(f"{left_colon}{question_counts}")
        )

        # Questions range
        first_num = self.test_data["nomor_pertama"]
        question_range = f"{first_num} - {first_num+question_counts-1}"
        stats_list.layout().addRow(
            QLabel("Nomor-nomor Soal"), QLabel(f"{left_colon}{question_range}")
        )

        # Question options
        question_options = self.test_data["opsi_soal"]
        question_options = ", ".join(question_options)
        stats_list.layout().addRow(
            QLabel("Opsi Soal"), QLabel(f"{left_colon}{question_options}")
        )

        # Total time used
        total_time = self.test_data["waktu_yang_digunakan"]["total"]
        total_time = self.format_time(total_time)
        stats_list.layout().addRow(
            QLabel("Waktu yang digunakan"),
            QLabel(f"{left_colon}{total_time}"),
        )

        # Corret, Incorrect, and Undetermined counts
        test_and_key = zip(
            self.test_data["jawaban_tes"].values(),
            self.test_data["kunci_jawaban"].values(),
        )
        correct_count = 0
        incorrect_count = 0
        undetermined_count = 0
        for test, key in test_and_key:
            if test == "":
                incorrect_count += 1
            elif key == "":
                undetermined_count += 1
            elif test != key:
                incorrect_count += 1
            else:
                correct_count += 1

        stats_list.layout().addRow(
            QLabel("Jawaban benar"), QLabel(f"{left_colon}{correct_count} soal")
        )
        stats_list.layout().addRow(
            QLabel("Jawaban salah"), QLabel(f"{left_colon}{incorrect_count} soal")
        )
        stats_list.layout().addRow(
            QLabel("Tidak dapat ditentukan"),
            QLabel(f"{left_colon}{undetermined_count} soal"),
        )

        self.stats_slide.layout().addWidget(stats_list)
        self.main_slide.addWidget(self.stats_slide)

    def init_test_review_slide(self):
        self.test_review_slide = QWidget()
        self.test_review_slide.setLayout(QVBoxLayout())

        #######################################
        # Combo box sort
        #######################################
        # Title
        sort_title = QLabel("Urutkan berdasarkan:")
        sort_title.setStyleSheet("font-size: 18px")
        self.test_review_slide.layout().addWidget(sort_title, alignment=Qt.AlignCenter)

        combo_boxes = QWidget()
        combo_boxes.setLayout(QHBoxLayout())

        # Sort method
        self.sort_method = QComboBox()
        self.sort_method.addItems(
            ("Nomor Soal", "Benar atau Salah", "Waktu Pengerjaan")
        )
        self.sort_method.currentIndexChanged.connect(self.update_table)
        combo_boxes.layout().addWidget(self.sort_method)

        # Ascending or descending
        self.asc_or_desc = QComboBox()
        self.asc_or_desc.addItems(("Naik", "Turun"))
        self.asc_or_desc.currentIndexChanged.connect(self.update_table)
        combo_boxes.layout().addWidget(self.asc_or_desc)

        self.test_review_slide.layout().addWidget(combo_boxes)

        #######################################
        # Table
        #######################################
        question_counts = self.test_data["jumlah_soal"]

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setRowCount(question_counts)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().hide()

        # Set header
        hor_header = ("No.", "Jawaban terpilih", "Kunci Jawaban", "Waktu")
        self.table.setHorizontalHeaderLabels(hor_header)

        self.table.itemClicked.connect(self.table_item_clicked)
        # Double click mechanism
        self.__prev_click = 0

        # Update table
        self.update_table()

        # Resize column to content so it fits nicely
        self.table.resizeColumnToContents(0)
        self.table.resizeColumnToContents(1)
        self.table.resizeColumnToContents(2)
        self.table.resizeColumnToContents(3)

        self.test_review_slide.layout().addWidget(self.table)

        self.main_slide.addWidget(self.test_review_slide)

    def init_test_note_slide(self):
        self.test_note_slide = QWidget()
        self.test_note_slide.setLayout(QVBoxLayout())

        #################################
        # Top part (title and save button)
        #################################
        top_container = QWidget()
        top_container.setLayout(QHBoxLayout())
        self.test_note_slide.layout().addWidget(top_container)

        title = QLabel("Catatan tes")
        title.setStyleSheet("font-size: 22px")
        top_container.layout().addWidget(title)

        spacer = QWidget()
        top_container.layout().addWidget(spacer)
        spacer.setFixedWidth(40)

        save_btn = QPushButton("Simpan Catatan")
        save_btn.setStyleSheet(GREEN_BTN_QSS)
        save_btn.clicked.connect(self.save_test_note)
        top_container.layout().addWidget(save_btn)

        #################################
        # Note
        #################################
        self.test_note = QPlainTextEdit()
        self.test_note.setStyleSheet("font-size: 15px")
        self.test_note.setPlainText(self.test_data["catatan_tes"])
        self.test_note_slide.layout().addWidget(self.test_note)

        self.main_slide.addWidget(self.test_note_slide)

    # sort_method should be "correctness", "time", "number"(default)
    def get_sorted_result(
        self, sort_method: str = "number", ascending: bool = True
    ) -> list:
        if sort_method not in self.SORT_METHODS:
            return

        first_num = self.test_data["nomor_pertama"]
        question_counts = self.test_data["jumlah_soal"]

        # Data
        numbers = [str(i) for i in range(first_num, first_num + question_counts)]
        data = []
        user_answers = list(self.test_data["jawaban_tes"].values())
        answer_key = list(self.test_data["kunci_jawaban"].values())
        time_spent = list(self.test_data["waktu_yang_digunakan"]["per_soal"].values())

        # Add data to data variable
        # if the user didn't answer the question or answer key, then set it to "tidak ada"
        for (idx, val) in enumerate(numbers):
            ua = user_answers[idx] if user_answers[idx] != "" else "tidak ada"
            ak = answer_key[idx] if answer_key[idx] != "" else "tidak ada"
            row = (val, ua, ak, time_spent[idx])
            data.append(row)

        # Sort the list based on sort_method
        if sort_method == "number":
            data.sort(key=lambda x: int(x[0]))
        elif sort_method == "accuracy":

            # Compare user answers and the answer key
            def sort_tf(x1, x2):
                # no answer
                if x2 == "tidak ada":
                    return 3
                # false
                elif x1 != x2:
                    return 2
                # true
                else:
                    return 1

            data.sort(key=lambda x: sort_tf(x[1], x[2]))
        else:
            data.sort(key=lambda x: int(x[3]))

        # Ascending or descending
        if ascending == False:
            data = reversed(data)

        return data

    # Called everytime there is an update on the data
    def update_table(self):
        sort_method = self.SORT_METHODS[self.sort_method.currentIndex()]
        ascending = self.asc_or_desc.currentIndex() == 0

        data = self.get_sorted_result(sort_method, ascending)

        for (row, row_value) in enumerate(data):
            test_answer = row_value[1]
            answer_key = row_value[2]

            # Highlight, correct = green, incorrect = red, undetermined = black
            # if the test answer is nothing, then it's incorrect
            # if the answer key is nothing, then it's undetermined,
            # if the test answer is not the same as the answer key, it's incorrect
            # else it is correct
            if test_answer == "tidak ada":
                bg = "#C62828"
            elif answer_key == "tidak ada":
                bg = ""
            elif test_answer != answer_key:
                bg = "#C62828"
            else:
                bg = "#2E7D32"

            for (idx, value) in enumerate(row_value):
                # Format time, time is always the last in row_value
                if idx == len(row_value) - 1:
                    value = self.format_time(value)

                item = QTableWidgetItem(str(value))
                item.setBackground(QColor(bg))
                item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                self.table.setItem(row, idx, item)

    def format_time(self, time) -> str:
        time = int(time)
        seconds = str(time % 60)
        minutes = str(time // 60)
        return f"{minutes} menit {seconds} detik"

    def format_date(self, time) -> str:
        tests_date = datetime.strptime(time, TIME_FORMAT)
        tests_day = DAY_INDO[tests_date.strftime("%A").lower()].capitalize()
        tests_month = MONTH_INDO[tests_date.strftime("%B").lower()].capitalize()
        tests_date = f"{tests_day}, {tests_date.day} {tests_month} {tests_date.year}"

        return tests_date

    # When rename test clicked
    def rename_test(self):
        dialog = TestNameDialog(
            self.data_path, self.test_data["tanggal_tes"], self.test_name
        )

        # Update in file
        if not dialog.exec():
            return
        new_name = dialog.test_name

        with open(self.data_path, "r") as f:
            data = orjson.loads(f.read())

        # rename self.test_name key to new_name
        new_keys = list(data.keys())
        new_keys = [x.replace(self.test_name, new_name) for x in new_keys]
        values = list(data.values())
        new_data = {new_keys[i]: values[i] for i in range(len(values))}

        with open(self.data_path, "wb") as f:
            f.write(orjson.dumps(new_data, option=ORJSON_OPTIONS))

        # Update Review windows
        self.title_test_name.setText(
            self.title_test_name.text().replace(self.test_name, new_name)
        )
        self.setWindowTitle(self.windowTitle().replace(self.test_name, new_name))
        self.test_name = new_name

        # Update test list
        self.dataUpdated.emit()

    @Slot(QTableWidgetItem)
    def table_item_clicked(self, it: QTableWidgetItem):
        question_num = int(self.table.item(it.row(), 0).text())

        options = self.test_data["opsi_soal"].copy()
        options.append("tidak ada")

        # Double click mechanism
        if it.column() == 2:
            current_idx = options.index(it.text())
            if question_num == self.__prev_click:
                self.change_answer_key(str(question_num), current_idx, options)
                self.__prev_click = 0
            else:
                self.__prev_click = question_num
        else:
            self.__prev_click = 0

    def change_answer_key(self, question_num, current_idx, options):
        dialog = ChangeAnswerDialog(options, current_idx)

        # Canceled
        if not dialog.exec():
            return

        # Change the last option from "tidak ada" to ""
        options.pop()
        options.append("")

        idx = dialog.combo_box.currentIndex()
        self.test_data["kunci_jawaban"][question_num] = options[idx]
        self.update_table()

        # Read and modify file
        with open(self.data_path, "r") as f:
            data = orjson.loads(f.read())

        data[self.test_name] = self.test_data

        with open(self.data_path, "wb") as f:
            f.write(orjson.dumps(data, option=ORJSON_OPTIONS))

        # Update list to avoid inconsistent data
        self.dataUpdated.emit()

    def save_test_note(self):
        with open(self.data_path, "r") as f:
            data = orjson.loads(f.read())

        data[self.test_name]["catatan_tes"] = self.test_note.toPlainText()

        with open(self.data_path, "wb") as f:
            f.write(orjson.dumps(data, option=ORJSON_OPTIONS))

        # Update list to avoid inconsistent data
        self.dataUpdated.emit()


class ChangeAnswerDialog(QDialog):
    def __init__(self, options, current_idx) -> None:
        super().__init__()
        self.options = options
        self.current_idx = current_idx

        self.setWindowTitle("Ubah kunci jawaban")
        self.setLayout(QVBoxLayout())
        self.setFixedWidth(200)

        # Title
        self.layout().addWidget(QLabel("Kunci jawaban baru: "))

        # Combo box
        self.combo_box = QComboBox()
        self.combo_box.addItems(self.options)
        self.combo_box.setCurrentIndex(self.current_idx)
        self.layout().addWidget(self.combo_box)

        # Buttons
        self.buttons = QWidget()
        self.layout().addWidget(self.buttons)
        self.buttons.setLayout(QHBoxLayout())

        self.accept_button = QPushButton("Ok")
        self.accept_button.clicked.connect(lambda: self.accept())
        self.buttons.layout().addWidget(self.accept_button)

        self.reject_button = QPushButton("Batalkan")
        self.reject_button.clicked.connect(lambda: self.reject())
        self.buttons.layout().addWidget(self.reject_button)
