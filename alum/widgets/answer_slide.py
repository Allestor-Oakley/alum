from PySide6.QtWidgets import (
    QDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
    QPushButton,
)
from PySide6.QtCore import Qt

from .finish_slide import FinishSlide
from ..constants import (
    ORJSON_OPTIONS,
    RED_BTN_QSS,
    GREEN_BTN_QSS,
    TIME_FORMAT,
)

from math import ceil
from datetime import datetime
import orjson
import os


# Answer key view slide
class AnswerKeySlide(QWidget):
    def __init__(self, first_question_num: int, question_counts: int, question_options):
        super().__init__()
        self.first_question_num = first_question_num
        self.question_counts = question_counts
        self.question_options = question_options

        self.setLayout(QVBoxLayout())

        #############################################
        # Top bar
        #############################################
        self.buttons = QWidget()
        self.buttons.setLayout(QHBoxLayout())

        # Title
        self.instruction_label = QLabel("Kunci Jawaban")
        self.instruction_label.setStyleSheet("font-size: 18px")
        self.buttons.layout().addWidget(self.instruction_label)

        # Spacer
        self.spacer = QWidget()
        self.buttons.layout().addWidget(self.spacer)

        # Cancel button
        self.cancel_button = QPushButton("Batalkan")
        self.cancel_button.setStyleSheet(RED_BTN_QSS)
        self.cancel_button.clicked.connect(self.cancel_test)
        self.buttons.layout().addWidget(self.cancel_button)

        # Finish button
        self.finish_button = QPushButton("Selesai")
        self.finish_button.clicked.connect(self.finish_answer_session)
        self.finish_button.setStyleSheet(GREEN_BTN_QSS)
        self.buttons.layout().addWidget(self.finish_button)
        self.layout().addWidget(self.buttons)

        #############################################
        # Answer Key Scroll Area (scroll horizontally)
        #############################################
        self.answer_key_scroll = QScrollArea()
        self.answer_key_scroll.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding
        )
        self.answer_key_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.layout().addWidget(self.answer_key_scroll)

        self.answer_key_container = QWidget()
        self.answer_key_container.setLayout(QGridLayout())

        # AnswerKeyWidget placement inside the grid
        # this should be [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (0, 1), (1,1), (1,2), ...]
        positions = [
            (j, i) for i in range(ceil(self.question_counts / 5)) for j in range(5)
        ]
        for pos, num in zip(
            positions,
            range(
                self.first_question_num, self.first_question_num + self.question_counts
            ),
        ):
            button = AnswerKeyWidget(num, self.question_options)
            self.answer_key_container.layout().addWidget(button, *pos)
        self.answer_key_scroll.setWidget(self.answer_key_container)

    def get_answer_keys(self) -> dict:
        answers = {}
        for num in range(
            self.first_question_num, self.first_question_num + self.question_counts
        ):
            answer_key = self.answer_key_container.findChild(
                AnswerKeyWidget, f"answerKey{num}"
            )
            answers[num] = answer_key.selected_answer
        return answers

    # Return all the necessary test data and stats for saving
    # -Test Name,
    # -Settings:
    # > Time limit
    # > First question number
    # > Question counts
    # > Question options
    # -Answers:
    # > test answer
    # > answer key
    # -Stats:
    # > Total time spent
    # > Time spent for each question
    # -Date
    # -Note (empty)
    def get_test_result(self, current_time):
        test_result = {}

        # Slides
        question_slide = self.parent().widget(2)

        test_result["batas_waktu"] = question_slide.time_limit * 60
        test_result["nomor_pertama"] = question_slide.first_question_num
        test_result["jumlah_soal"] = question_slide.question_counts
        test_result["opsi_soal"] = self.question_options

        test_result["jawaban_tes"] = question_slide.answers
        test_result["kunci_jawaban"] = self.get_answer_keys()

        test_result["waktu_yang_digunakan"] = {}
        total_time = question_slide.total_time_counter

        # If time limit was set
        if test_result["batas_waktu"] == 0:
            test_result["waktu_yang_digunakan"]["total"] = total_time
        else:
            test_result["waktu_yang_digunakan"]["total"] = (
                test_result["batas_waktu"] - total_time
            )

        test_result["waktu_yang_digunakan"][
            "per_soal"
        ] = question_slide.get_questions_time()

        test_result["tanggal_tes"] = current_time

        test_result["catatan_tes"] = ""

        return test_result

    # Show confirmation messagebox if there are still unanswered questions,
    # then show TestNameDialog and then write the data to data.json
    def finish_answer_session(self):
        qm = QMessageBox
        answers = self.get_answer_keys()
        # If there are still unanswered questions
        if "" in answers.values():
            confirmation = qm.warning(
                self,
                "Konfirmasi",
                "Masih ada pertanyaan yang belum terjawab, apakah anda yakin untuk menyelesaikan kunci jawaban?",
                qm.Yes | qm.No,
            )
            if confirmation == qm.No:
                return

        # this is actually just MainWindow.get_root_abspath()
        # because the file where MainWindow is defined is located in the root directory
        # but this file, is inside another directory
        abspath = self.parent().parent().parent().get_root_abspath()
        data_path = os.path.join(abspath, "data.json")

        current_time = datetime.now().strftime(TIME_FORMAT)

        # Run TestNameDialog, stop the function if the user canceled it
        test_name_dialog = TestNameDialog(
            data_path=data_path, default_test_name=current_time
        )
        if not test_name_dialog.exec():
            return

        # Read and modify data inside data.json
        test_result = self.get_test_result(current_time)
        with open(data_path, "r") as f:
            data = f.read()
            data = orjson.loads(data)

        with open(data_path, "wb") as f:
            data[test_name_dialog.test_name] = test_result
            f.write(orjson.dumps(data, option=ORJSON_OPTIONS))

        # Go to the next slide
        finish_slide = FinishSlide()
        self.parent().addWidget(finish_slide)
        self.parent().slideInNext()

    # When "Batalkan" button is clicked
    def cancel_test(self):
        # Confirmation
        qm = QMessageBox
        confirmation = qm.warning(
            self,
            "Konfirmasi",
            "Data tes belum tersimpan,\napa anda yakin ingin membatalkan tes?",
            qm.Yes | qm.No,
        )
        if confirmation == qm.No:
            return

        self.parent().slideInIdx(0)


class AnswerKeyWidget(QWidget):
    def __init__(self, question_number: int, question_options):
        super().__init__()
        self.question_options = question_options
        self.question_number = question_number
        self.highlight_style = "background: #3F51B5;color: white;"

        self.setLayout(QHBoxLayout())
        self.setObjectName(f"answerKey{self.question_number}")

        # Inner state
        self.selected_answer = ""

        # Init UI
        self.question_label = QLabel(str(self.question_number))
        self.layout().addWidget(self.question_label)

        for option in self.question_options:
            button = QPushButton(option)
            button.setObjectName(f"option{option}")
            button.setFixedSize(34, 34)
            button.clicked.connect(self.change_answer)
            self.layout().addWidget(button)

    def change_answer(self):
        selected_option = self.sender().text()

        # Uncheck answer if the user click the selected answer again
        if self.selected_answer == selected_option:
            prev_answer = self.findChild(QPushButton, f"option{self.selected_answer}")
            new_prev_style = prev_answer.styleSheet().replace(self.highlight_style, "")
            prev_answer.setStyleSheet(new_prev_style)
            self.selected_answer = ""
            return

        # If user has select an option before, remove the previous answer highlight
        if self.selected_answer != "":
            prev_answer = self.findChild(QPushButton, f"option{self.selected_answer}")
            new_prev_style = prev_answer.styleSheet().replace(self.highlight_style, "")
            prev_answer.setStyleSheet(new_prev_style)

        # highlight current answer
        current_answer = self.findChild(QPushButton, f"option{selected_option}")
        current_answer.setStyleSheet(current_answer.styleSheet() + self.highlight_style)
        self.selected_answer = selected_option


class TestNameDialog(QDialog):
    def __init__(
        self, data_path: str, default_test_name: str, prev_test_name: str = None
    ) -> None:
        super().__init__()
        self.data_path = data_path
        self.test_name = default_test_name

        self.setWindowTitle("Konfirmasi")
        self.setLayout(QVBoxLayout())

        self.layout().addWidget(QLabel("Nama tes:"))
        self.layout().addWidget(
            QLabel(
                "Apabila tidak diisi, maka waktu sekarang akan digunakan sebagai nama tes"
            )
        )

        self.test_name_input = QLineEdit()
        self.test_name_input.setPlaceholderText(self.test_name)
        if prev_test_name:
            self.test_name_input.setText(prev_test_name)
        self.layout().addWidget(self.test_name_input)

        self.buttons = QWidget()
        self.layout().addWidget(self.buttons)
        self.buttons.setLayout(QHBoxLayout())

        self.accept_button = QPushButton("Ok")
        self.accept_button.clicked.connect(self.ok_button_clicked)
        self.buttons.layout().addWidget(self.accept_button)

        self.reject_button = QPushButton("Batalkan")
        self.reject_button.clicked.connect(lambda: self.reject())
        self.buttons.layout().addWidget(self.reject_button)

    def ok_button_clicked(self):
        test_name = self.test_name_input.text()

        # Use the default name, if the default name already exist,
        # add (num) at the end of the name,
        # increase the num until the name is unique
        if test_name == "":
            count = 1
            while not self.check_name_valid(self.test_name):
                self.test_name = f"{self.test_name} ({count})"
                count += 1
            self.accept()
            return

        # If the name is valid, close the window and change self.test_name
        # self.test_name will later be used outside in AnswerKeySlide.finish_answer_session
        # If the name is not valid, show critical messagebox
        if self.check_name_valid(test_name):
            self.test_name = test_name
            self.accept()
        else:
            qm = QMessageBox
            qm.critical(
                self,
                "Nama tidak valid",
                "Nama tes sudah dipakai sebelumnya, mohon gunakan nama lain.",
            )

    # Check if test_name is already a name in data.json, if it is, return False
    def check_name_valid(self, test_name) -> bool:
        with open(self.data_path, "r") as f:
            data = f.read()
        data = orjson.loads(data)

        return not test_name in data.keys()
