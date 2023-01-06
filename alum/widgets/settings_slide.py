from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QFormLayout,
    QHBoxLayout,
    QSizePolicy,
    QSpinBox,
    QLabel,
    QCheckBox,
    QPushButton,
)
from .custom_widgets import SlidingStackedWidget
from .test_slide import TestWidget


class TestSettings(QWidget):
    def __init__(self, root: SlidingStackedWidget):
        super().__init__()
        self.root = root
        self.setLayout(QVBoxLayout())

        ###############################
        # Options
        ###############################
        options = QWidget()
        options.setLayout(QFormLayout())
        options.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Time Limit
        self.time_limit_on = QCheckBox()
        self.time_limit = QSpinBox()
        self.time_limit.setEnabled(False)
        self.time_limit.setFixedWidth(80)
        self.time_limit.setMinimum(10)
        self.time_limit.setMaximum(999)
        self.time_limit_on.stateChanged.connect(
            lambda: self.time_limit.setEnabled(not self.time_limit.isEnabled())
        )  # toggle time limit
        options.layout().addRow(QLabel("Batas Waktu (menit)"), self.time_limit_on)
        options.layout().addRow("", self.time_limit)

        # Show time
        self.show_time = QCheckBox()
        self.show_time.stateChanged.connect(self.toggle_show_time)
        options.layout().addRow("Tunjukkan waktu", self.show_time)
        self.show_total_time = QCheckBox("seluruh")
        options.layout().addRow("", self.show_total_time)
        self.show_question_time = QCheckBox("per-soal")
        options.layout().addRow("", self.show_question_time)
        self.toggle_show_time()

        # Number of questions
        self.question_counts = QSpinBox()
        self.question_counts.setFixedWidth(80)
        self.question_counts.setMinimum(1)
        self.question_counts.setMaximum(999)
        self.question_counts.setValue(10)
        self.question_counts.textChanged.connect(self.update_questions_range)
        options.layout().addRow(QLabel("Jumlah Soal"), self.question_counts)

        # First question number
        self.frst_question = QSpinBox()
        self.frst_question.setMinimum(1)
        self.frst_question.setFixedWidth(80)
        self.frst_question.textChanged.connect(self.update_questions_range)
        options.layout().addRow(QLabel("Nomor soal pertama"), self.frst_question)
        self.question_range = QLabel(str(self.frst_question.value()))
        self.question_range.setStyleSheet("color: Grey")
        options.layout().addRow(self.question_range, QWidget())
        self.update_questions_range()

        # Show doubt buttons
        self.show_doubt_buttons = QCheckBox()
        self.show_doubt_buttons.setChecked(True)
        options.layout().addRow("Tunjukkan tombol ragu", self.show_doubt_buttons)

        # Show options count
        self.options = ("A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K")
        self.option_counts = QSpinBox()
        self.option_counts.setMinimum(2)
        self.option_counts.setMaximum(10)
        self.option_counts.setValue(5)
        self.option_counts.setFixedWidth(80)
        self.option_counts.valueChanged.connect(self.update_option_count)
        options.layout().addRow("Jumlah opsi", self.option_counts)
        self.option_preview = QLabel()
        self.option_preview.setStyleSheet("color: Grey")
        self.update_option_count()
        options.layout().addRow(self.option_preview, QWidget())

        # Jump to the next question when answer button is clicked
        self.automatic_slide_next = QCheckBox()
        options.layout().addRow("Otomatis pindah soal", self.automatic_slide_next)

        ###############################
        # Buttons
        ###############################
        buttons = QWidget()
        buttons.setLayout(QHBoxLayout())

        back_button = QPushButton("Kembali")
        back_button.clicked.connect(self.root.slideInPrev)

        spacer = QWidget()

        start_button = QPushButton("Mulai")
        start_button.clicked.connect(self.start_test)

        buttons.layout().addWidget(back_button)
        buttons.layout().addWidget(spacer)
        buttons.layout().addWidget(start_button)

        self.layout().addWidget(options)
        self.layout().addWidget(buttons)

    def toggle_show_time(self):
        if self.show_time.isChecked():
            self.show_question_time.setEnabled(True)
            self.show_total_time.setEnabled(True)
        else:
            self.show_question_time.setEnabled(False)
            self.show_total_time.setEnabled(False)

    def update_questions_range(self):
        # I know this is stupid, but just in case the user just want one question
        if self.question_counts.value() == 1:
            self.question_range.setText(f"{self.frst_question.value()}")
            return

        first_question = self.frst_question.value()
        last_question = first_question + self.question_counts.value() - 1
        self.question_range.setText(f"{first_question} - {last_question}")

    def update_option_count(self):
        self.option_preview.setText(
            ", ".join(self.options[: self.option_counts.value()])
        )

    def start_test(self):
        if self.root.widget(self.root.currentIndex() + 1) != None:
            test_widget = self.root.widget(self.root.currentIndex() + 1)
            self.root.removeWidget(test_widget)
            test_widget.deleteLater()

        # Set time limit to 0 if the user doesn't set the time limit
        time_limit = self.time_limit.value() if self.time_limit_on.isChecked() else 0
        test_widget = TestWidget(
            time_limit=time_limit,
            show_total_time=self.show_time.isChecked()
            and self.show_total_time.isChecked(),  # True if both show_time and show_total_time
            show_question_time=self.show_time.isChecked()
            and self.show_question_time.isChecked(),  # True if both show_time and show_question_time
            question_counts=self.question_counts.value(),
            first_question_num=self.frst_question.value(),
            show_doubt_button=self.show_doubt_buttons.isChecked(),
            question_options=self.option_preview.text().split(", "),
            automatic_slide_next=self.automatic_slide_next.isChecked(),
        )
        self.root.addWidget(test_widget)
        self.root.slideInNext()
