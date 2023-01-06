from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import QTimer, Qt

from .custom_widgets import SlidingStackedWidget
from .answer_slide import AnswerKeySlide
from ..constants import GREEN_BTN_QSS, RED_BTN_QSS

from math import ceil


# Test view slide
class TestWidget(QWidget):
    def __init__(
        self,
        time_limit: int,
        show_total_time: bool,
        show_question_time: bool,
        question_counts: int,
        first_question_num: int,
        show_doubt_button: bool,
        question_options: list,
        automatic_slide_next: bool,
    ):
        super().__init__()
        self.time_limit = time_limit
        self.show_total_time = show_total_time
        self.show_question_time = show_question_time
        self.question_counts = question_counts
        self.first_question_num = first_question_num
        self.show_doubt_button = show_doubt_button
        self.question_options = question_options
        self.automatic_slide_next = automatic_slide_next

        self.setLayout(QHBoxLayout())

        # Inner state
        self.answers = {}
        for num in range(
            self.first_question_num,
            self.first_question_num + self.question_counts,
        ):
            self.answers[num] = ""
        self.current_question = self.first_question_num

        # Timer
        self.total_timer = QTimer(self)
        # If time limit have not been set
        if self.time_limit == 0:
            # HACK if I set it to -1, it will start at 00:00
            self.total_time_counter = -1
            self.timer_delta = 1  # Increase time
        else:
            # HACK if I add 1 here, it will start at the time limit (ex: 10:00)
            self.total_time_counter = self.time_limit * 60 + 1
            self.timer_delta = -1  # Decrease time
        self.total_timer.setInterval(1000)  # 1 seconds
        self.total_timer.timeout.connect(self.update_timer)
        self.total_timer.start()

        ###################################################
        # Left Side section
        ###################################################
        self.left_section = QWidget()
        self.left_section.setLayout(QVBoxLayout())
        self.layout().addWidget(self.left_section)

        # Time remaining or time spent
        self.time_remaining = QLabel()
        self.time_hidden_text = "Tunjukkan waktu"
        self.time_remaining.setStyleSheet("font-size: 18px")
        self.time_remaining.setAlignment(Qt.AlignCenter)
        self.update_timer()
        self.time_remaining.mousePressEvent = self.toggle_show_time
        self.left_section.layout().addWidget(self.time_remaining)

        # Questions list
        self.questions_scroll = QScrollArea()
        self.questions_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.questions_scroll.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.questions_scroll.setStyleSheet("QScrollArea {border:none}")
        self.questions_list = QWidget()
        self.questions_list.setLayout(QGridLayout())
        self.questions_list.layout().setAlignment(Qt.AlignTop)
        self.questions_list.setContentsMargins(0, 0, 15, 0)
        ## Grid logic, just trust me
        positions = [
            (i, j) for i in range(ceil(self.question_counts / 4)) for j in range(4)
        ]
        for pos, num in zip(
            positions,
            range(
                self.first_question_num,
                self.first_question_num + self.question_counts,
            ),
        ):
            button = QuestionNumberButton(str(num), objectName=f"questionButton{num}")
            button.setFixedSize(42, 42)
            button.clicked.connect(self.go_to_question)
            self.questions_list.layout().addWidget(button, *pos)
        ##
        self.questions_scroll.setWidget(self.questions_list)
        self.left_section.layout().addWidget(self.questions_scroll)

        # Quit test button
        self.quit_test_button = QPushButton("Batalkan tes")
        self.quit_test_button.setStyleSheet(RED_BTN_QSS)
        self.quit_test_button.clicked.connect(self.quit_test)
        self.left_section.layout().addWidget(self.quit_test_button)

        ###################################################
        # Right Side section
        ###################################################
        self.right_section = QWidget()
        self.right_section.setLayout(QVBoxLayout())
        self.layout().addWidget(self.right_section)

        # Finish button container and finish button
        self.finish_btn_cont = QWidget()
        self.finish_btn_cont.setLayout(QVBoxLayout())
        self.finish_btn = QPushButton("Selesaikan Tes")
        self.finish_btn.clicked.connect(self.finish_test)
        self.finish_btn.setStyleSheet(GREEN_BTN_QSS)
        self.finish_btn_cont.layout().addWidget(self.finish_btn)
        self.finish_btn_cont.setContentsMargins(420, 0, 0, 0)
        self.right_section.layout().addWidget(self.finish_btn_cont)

        # Answer slide
        self.answers_slide = SlidingStackedWidget()
        for num in range(
            self.first_question_num,
            self.first_question_num + self.question_counts,
        ):
            answer_view = AnswerWidget(self, num)
            answer_view.setObjectName(f"answerWidget{num}")
            self.answers_slide.addWidget(answer_view)
        self.right_section.layout().addWidget(self.answers_slide)

        # Set style and other things after all things have been done
        self.change_question_view(self.current_question)

    # Just to make things easier
    def get_answer_slide(self, num: int):
        return self.answers_slide.findChild(AnswerWidget, f"answerWidget{num}")

    def get_question_btn(self, num: int):
        return self.left_section.findChild(QPushButton, f"questionButton{num}")

    # Called every tick
    def update_timer(self):
        # Update count by adding delta (1 to increase and -1 to decrease)
        self.total_time_counter += self.timer_delta
        if self.show_total_time:
            seconds = str(self.total_time_counter % 60).zfill(2)
            minutes = str(self.total_time_counter // 60).zfill(2)
            self.time_remaining.setText(f"{minutes}:{seconds}")
        else:
            self.time_remaining.setText(self.time_hidden_text)

        # If time_limit is up
        if self.time_limit != 0 and self.total_time_counter == 0:
            self.finish_test(time_up=True)

    # Toggle show time when time remaing label is clicked
    def toggle_show_time(self, _):
        self.show_total_time = not self.show_total_time
        self.update_timer()

    # This will only be called outside of this class
    # Get time spent in each questions
    def get_questions_time(self) -> dict:
        # Imma steal it from self.answers for the key
        question_times = self.answers.copy()
        for num in question_times.keys():
            answer_widget = self.get_answer_slide(num)
            question_times[num] = answer_widget.timer_count
        return question_times

    # Callback when button in self.questions_list is clicked
    def go_to_question(self):
        num = int(self.sender().text())
        self.change_question_view(num)

    # The only function to call when user want to change question view
    # stop previous answer timer, and start the next answer timer
    def change_question_view(self, question_num: int):
        current_answer = self.get_answer_slide(question_num)
        previous_answer = self.get_answer_slide(self.current_question)
        self.highlight_selected_qb(self.current_question, question_num)
        # Timer
        previous_answer.stop_timer()
        current_answer.start_timer()
        ###
        self.current_question = question_num
        self.answers_slide.slideInWgt(current_answer)

    # Highlight selected question button
    def highlight_selected_qb(self, prev: int, next: int):
        selected_style = "background-color: #283593;color: white;"
        # Remove previous style
        prev = self.get_question_btn(prev)
        prev_style = prev.styleSheet()
        prev.setStyleSheet(prev_style.replace(selected_style, ""))
        # Add style to current
        current = self.get_question_btn(next)
        current.setStyleSheet(current.styleSheet() + selected_style)

    # Higlight question button in Question List to yellow,
    # Highlight currently answered option in AnswerWidget
    def change_answer(self, num: int, answer: str):
        question_button_ls = self.get_question_btn(num)
        question_button_ls.setStyleSheet(
            question_button_ls.styleSheet() + "border: 1px solid #FFD54F;"
        )
        answer_widget_rs = self.get_answer_slide(num)
        answer_widget_rs.highlight_answer(self.answers[num], answer)

        self.answers[num] = answer

        # Slide to the next question if automatic_slide_next is True
        if self.automatic_slide_next:
            self.change_question_view(self.current_question + 1)

    # Toggle notification on question button in left_section
    # This will only get called outside of this function,
    # at AnswerWidget.doubt_button_click
    def doubt_question(self, num):
        qb_ls = self.get_question_btn(num)
        qb_ls.toggle_doubt()

    # Slide back to previous slide, which is settings
    # this widget will later be deleted when the user start a new test
    # and also stop total timer and currently viewed answer widget timers
    def quit_test(self):
        # Confirmation
        qm = QMessageBox
        res = qm().warning(
            self,
            "Konfirmasi",
            "Data tidak akan tersimpan,\napa anda yakin ingin membatalkan tes?",
            qm.Yes | qm.No,
        )
        if res == qm.No:
            return

        current_answer = self.get_answer_slide(self.current_question)
        current_answer.stop_timer()
        self.total_timer.stop()
        self.parent().slideInPrev()

    # End timer, start answer_key widget,
    # this will only be used in self.finish_test function
    def end_test(self):
        # Stop timer
        self.total_timer.stop()
        current_answer = self.get_answer_slide(self.current_question)
        current_answer.timer.stop()
        # Start answer key widget
        answer_key = AnswerKeySlide(
            first_question_num=self.first_question_num,
            question_counts=self.question_counts,
            question_options=self.question_options,
        )
        self.parent().addWidget(answer_key)
        self.parent().slideInNext()

    def finish_test(self, time_up: bool = False):
        qm = QMessageBox

        # if time_up is True, than there will be no confirmation dialog if user
        # have not completed all the question
        if time_up:
            qm.information(
                self, "Waktu habis", "Maaf, waktu pengerjaan soal telah habis", qm.Ok
            )
            self.end_test()
            return

        # If there are unanswered questions
        if "" in self.answers.values():
            res = qm().warning(
                self,
                "Konfirmasi",
                "Masih ada pertanyaan yang belum terjawab, apa anda yakin ingin menyelesaikan tes?",
                qm.Yes | qm.No,
            )
            if res == qm.Yes:
                self.end_test()
        else:
            self.end_test()


# Question number button on the left side
class QuestionNumberButton(QPushButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setLayout(QVBoxLayout())
        self.setStyleSheet("padding: 0;")

        # Add small widget at the top left of the button
        self.notification = QWidget()
        self.notification.setFixedSize(10, 10)
        self.notification.setStyleSheet(
            "background-color: #FFD54F; border-radius: 2.5px;border:none;"
        )
        self.layout().setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop
        )
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().addWidget(self.notification)

        # Inner state
        self.doubt = False
        self.toggle_doubt()

    # This will only be used outside of this class
    def toggle_doubt(self):
        self.notification.setVisible(self.doubt)
        self.doubt = not self.doubt


###############################################################################################

# Answer widget for each slide
class AnswerWidget(QWidget):
    def __init__(self, root: TestWidget, question_num: int):
        super().__init__()
        # this is just TestWidget, I use this because most of the data is stored there
        self.root = root
        self.question_num = question_num

        self.setLayout(QVBoxLayout())

        # Inner timer
        self.timer = QTimer()
        self.timer_on = False
        self.timer_count = 0
        self.timer.setInterval(1000)  # 1 second
        self.timer.timeout.connect(self.timer_update)

        ##########################################
        ## Top section (timer, question number)
        ##########################################
        self.top_section = QWidget()
        self.top_section.setLayout(QHBoxLayout())
        self.layout().addWidget(self.top_section)

        # Question time
        self.question_time = QLabel("")
        if self.root.show_question_time:
            self.question_time.setText("00:00")
            self.question_time.setStyleSheet("font-size: 18px;")
            self.question_time.setAlignment(Qt.AlignTop)
            self.timer_update()
        self.question_time.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.top_section.layout().addWidget(self.question_time)

        # Number
        self.number_text = QLabel(str(question_num))
        self.number_text.setFixedSize(60, 60)
        self.number_text.setStyleSheet(
            """
            font-size: 22px;
            border: 1px solid white;
            border-radius: 30.2px;
            """
        )
        self.number_text.setAlignment(Qt.AlignCenter)
        self.number_text.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.top_section.layout().addWidget(self.number_text)

        # Empty space after number
        self.spacer_ts = QWidget()
        self.spacer_ts.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.top_section.layout().addWidget(self.spacer_ts)

        ##########################################
        ## Middle section (answer options)
        ##########################################
        self.middle_section = QWidget()
        self.middle_section.setLayout(QHBoxLayout())
        self.middle_section.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.layout().addWidget(self.middle_section)

        # Answer option buttons
        for option in self.root.question_options:
            button = SquareButton(option, objectName=f"answerButton{option}")
            button.clicked.connect(self.choose_answer)
            button_font = button.font()
            button_font.setPointSize(24)
            button.setFont(button_font)
            # TODO damn, size is fucking confusing here in qt
            button.setMaximumSize(200, 200)
            self.middle_section.layout().addWidget(button)

        ##########################################
        ## Bottom section ((previous question, doubt, next question) buttons)
        ##########################################
        self.bottom_section = QWidget()
        self.bottom_section.setLayout(QHBoxLayout())
        self.layout().addWidget(self.bottom_section)

        # Previous question button
        # hide the button if this is the first question
        if self.question_num != self.root.first_question_num:
            self.prev_button = QPushButton("<- Sebelumnya")
            self.prev_button.clicked.connect(lambda: self.change_question(-1))
        else:
            self.prev_button = QWidget()
        self.bottom_section.layout().addWidget(self.prev_button)

        # Doubt buttons
        # set it to plain QWidget if the user choose not to show doubt button
        if self.root.show_doubt_button:
            self.doubt_button = QPushButton("Ragu-ragu")
            self.doubt_button.setCheckable(True)
            self.doubt_button.clicked.connect(self.doubt_button_click)
        else:
            self.doubt_button = QWidget()
        self.bottom_section.layout().addWidget(self.doubt_button)

        # Next question button
        # if this is the last question, then change the button to "Finish button"
        if (
            self.question_num
            != self.root.question_counts + self.root.first_question_num - 1
        ):
            self.next_button = QPushButton("Berikutnya ->")
            self.next_button.clicked.connect(lambda: self.change_question(1))
        else:
            self.next_button = QPushButton("Selesai")
            self.next_button.setStyleSheet(GREEN_BTN_QSS)
            self.next_button.clicked.connect(self.root.finish_test)
        self.bottom_section.layout().addWidget(self.next_button)

    # Callback when choosing answer
    def choose_answer(self):
        self.root.change_answer(self.question_num, self.sender().text())

    # Highlight option button, this function is only used outside this class
    # if the previous answer has been selected, remove the style
    # then, highlight the new answer
    def highlight_answer(self, prev_answer, answer):
        if prev_answer != "":
            prev = self.middle_section.findChild(
                QPushButton, f"answerButton{prev_answer}"
            )
            prev.setStyleSheet("")
        current = self.middle_section.findChild(QPushButton, f"answerButton{answer}")
        current.setStyleSheet("background: #3F51B5;color: white;")

    # idx_move is either 1 or -1
    def change_question(self, idx_move):
        self.root.change_question_view(self.root.current_question + idx_move)

    def doubt_button_click(self):
        # If user haven't select any answer
        if self.root.answers[self.root.current_question] == "":
            self.doubt_button.setChecked(False)
            return
        self.root.doubt_question(self.root.current_question)

    ### TIMER
    def start_timer(self):
        self.timer_on = True
        self.timer.start()

    def stop_timer(self):
        self.timer_on = False
        self.timer.stop()

    def timer_update(self):
        if self.timer_on == False:
            return
        self.timer_count += 1
        if self.root.show_question_time:
            seconds = str(self.timer_count % 60).zfill(2)
            minutes = str(self.timer_count // 60).zfill(2)
            self.question_time.setText(f"{minutes}:{seconds}")


# just re implement the resizeEvent and nothing else
class SquareButton(QPushButton):
    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.setFixedHeight(event.size().width())
