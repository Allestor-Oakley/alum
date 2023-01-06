from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget
from PySide6.QtCore import Qt


class FinishSlide(QWidget):
    def __init__(self):
        super().__init__()
        self.setLayout(QVBoxLayout())

        container = QWidget()
        container.setFixedSize(300, 150)
        container.setLayout(QVBoxLayout())
        self.layout().addWidget(container, alignment=Qt.AlignCenter)

        message = QLabel("Selamat! Tes sudah selesai")
        message.setStyleSheet("font-size: 18px")
        container.layout().addWidget(message, alignment=Qt.AlignCenter)

        back_button = QPushButton("Kembali ke menu utama")
        back_button.clicked.connect(self.back_to_home)
        back_button.setStyleSheet("font-size: 14px")
        container.layout().addWidget(back_button)

    # update test list and then slide back to home slide
    def back_to_home(self):
        self.parent().parent().parent().review_test.update_test_list()
        self.parent().slideInIdx(0)
