"""
Implementation of the study window.
"""

from gi.repository import Gtk  # type: ignore

from language_practice.flashcard import Flashcard


class StudyWindow(Gtk.ApplicationWindow):
    """
    Window for studying flashcards.
    """

    def __init__(self, flashcard: Flashcard, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.set_default_size(-1, 600)

        self.set_title("Language Practice")
        self.flashcard = flashcard

        (self.peek, self.is_review) = self.flashcard.current()
        if self.peek is not None:
            button_hbox_1 = self.grade_button_box()
            button_hbox_2 = self.navigation_button_box()

            self.display_box = Gtk.ScrolledWindow()
            self.display_box.set_vexpand(True)
            self.initial_display()

            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            self.counter_label = Gtk.Label(halign=Gtk.Align.START)
            self.counter_label.set_text(f"{self.flashcard.flashcards_left()} left")
            self.counter_label.set_css_classes(["counter"])
            self.lang_label = Gtk.Label(halign=Gtk.Align.START)
            (entry, _) = self.flashcard.current()
            if entry is not None:
                self.lang_label.set_text(f"{entry.get_lang()}")
                self.lang_label.set_css_classes(["lang"])
            hbox.append(self.counter_label)
            hbox.append(self.lang_label)
            vbox.append(hbox)
            vbox.append(self.display_box)
            vbox.append(button_hbox_1)
            vbox.append(button_hbox_2)

            self.set_child(vbox)
        else:
            label = Gtk.Label()
            label.set_text("Nothing to study")
            label.set_css_classes("word")
            self.set_child(label)

    def grade_button_box(self) -> Gtk.Box:
        """
        Set up button box for grading.
        """
        button_hbox_1 = Gtk.Box()
        zero = Gtk.Button(label="No recall")
        zero.connect("clicked", lambda button: self.grade(0))
        zero.set_css_classes(["study-buttons", "study-top"])
        button_hbox_1.append(zero)
        one = Gtk.Button(label="Wrong, familiar")
        one.connect("clicked", lambda button: self.grade(1))
        one.set_css_classes(["study-buttons", "study-top"])
        button_hbox_1.append(one)
        two = Gtk.Button(label="Wrong, easy to remember")
        two.connect("clicked", lambda button: self.grade(2))
        two.set_css_classes(["study-buttons", "study-top"])
        button_hbox_1.append(two)
        three = Gtk.Button(label="Correct, hard")
        three.connect("clicked", lambda button: self.grade(3))
        three.set_css_classes(["study-buttons", "study-top"])
        button_hbox_1.append(three)
        four = Gtk.Button(label="Correct, medium")
        four.connect("clicked", lambda button: self.grade(4))
        four.set_css_classes(["study-buttons", "study-top"])
        button_hbox_1.append(four)
        five = Gtk.Button(label="Correct, easy")
        five.connect("clicked", lambda button: self.grade(5))
        five.set_css_classes(["study-buttons", "study-top"])
        button_hbox_1.append(five)
        button_hbox_1.set_halign(Gtk.Align.CENTER)

        return button_hbox_1

    def navigation_button_box(self) -> Gtk.Box:
        """
        Set up button box for navigation.
        """
        button_hbox_2 = Gtk.Box()
        definition = Gtk.Button(label="Flashcard front")
        definition.connect("clicked", lambda button: self.initial_display())
        definition.set_css_classes(["study-buttons", "study-bottom"])
        button_hbox_2.append(definition)
        back = Gtk.Button(label="Flashcard back")
        back.connect("clicked", lambda button: self.on_flashcard_back())
        back.set_css_classes(["study-buttons", "study-bottom"])
        button_hbox_2.append(back)
        usage = Gtk.Button(label="Usage")
        usage.connect("clicked", lambda button: self.on_usage())
        usage.set_css_classes(["study-buttons", "study-bottom"])
        button_hbox_2.append(usage)
        charts = Gtk.Button(label="Charts")
        charts.connect("clicked", lambda button: self.on_charts())
        charts.set_css_classes(["study-buttons", "study-bottom"])
        button_hbox_2.append(charts)
        button_hbox_2.set_halign(Gtk.Align.CENTER)

        return button_hbox_2

    def next(self):
        """
        Select next flashcard.
        """
        self.flashcard.post_grade()
        self.counter_label.set_text(f"{self.flashcard.flashcards_left()} left")
        (entry, _) = self.flashcard.current()
        self.lang_label.set_text(f"{entry.get_lang()}")
        (self.peek, self.is_review) = self.flashcard.current()

    def grade(self, grade: int):
        """
        Grade a flashcard.
        """
        if self.peek is not None:
            if self.is_review:
                self.peek.get_repetition().review(grade)
            else:
                self.peek.get_repetition().grade(grade)
            self.next()
            self.initial_display()

    def initial_display(self):
        """
        Initial display for a flashcard.
        """
        if self.peek is not None:
            part_of_speech = self.peek.get_part_of_speech()
            aspect = self.peek.get_aspect()
            definition = Gtk.Label()
            definition.set_text(self.peek.get_definition())
            definition.set_css_classes(["word"])
            box = Gtk.Box(spacing=10)
            box.prepend(definition)
            if part_of_speech is not None:
                part_of_speech_label = Gtk.Label()
                part_of_speech_label.set_text(part_of_speech)
                part_of_speech_label.set_css_classes(["word"])
                box.prepend(part_of_speech_label)
            if aspect is not None:
                aspect_label = Gtk.Label()
                aspect_label.set_text(aspect)
                aspect_label.set_css_classes(["word"])
                box.prepend(aspect_label)
            self.display_box.set_child(box)
        else:
            all_done = Gtk.Label()
            all_done.set_text("All done!")
            all_done.set_css_classes(["word"])
            self.set_child(all_done)

    def on_flashcard_back(self):
        """
        Handle flashcard back button press.
        """
        if self.peek is not None:
            word = Gtk.Label()
            word.set_text(self.peek.get_word())
            word.set_css_classes(["word"])
            gender = self.peek.get_gender()
            box = Gtk.Box(spacing=10)
            box.prepend(word)
            if gender is not None:
                gender_label = Gtk.Label()
                gender_label.set_text(gender)
                gender_label.set_css_classes(["word"])
                box.prepend(gender_label)
            self.display_box.set_child(box)

    def on_usage(self):
        """
        Handle usage button press.
        """
        if self.peek is not None:
            usage = self.peek.get_usage()
            if usage is not None:
                self.display_box.set_child(Gtk.Label.new(usage))

    def on_charts(self):
        """
        Handle usage button press.
        """
        if self.peek is not None:
            vbox = Gtk.Box(spacing=6, orientation=Gtk.Orientation.VERTICAL)
            charts = self.peek.get_charts()
            if charts is not None:
                for chart in charts:
                    grid = Gtk.Grid()
                    for i, row in enumerate(chart):
                        for j, col_val in enumerate(row):
                            grid.attach(Gtk.Label.new(col_val), j, i, 1, 1)

                    vbox.append(grid)

            self.display_box.set_child(vbox)
