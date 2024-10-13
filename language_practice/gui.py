"""
Graphical user interface.
"""

#  pylint: disable=wrong-import-position
#  pylint: disable=too-few-public-methods

import asyncio
from sqlite3 import IntegrityError
import tomllib
from typing import Self

import gi  # type: ignore

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk, Gio  # type: ignore  # pylint: disable=wrong-import-order
from language_practice.flashcard import Flashcard  # type: ignore
from language_practice.config import TomlConfig
from language_practice.sqlite import SqliteHandle
from language_practice.web import scrape


class GuiApplication(Adw.Application):
    """
    Graphical application.
    """

    def __init__(self, handle: SqliteHandle, flashcard_sets: list[str], **kwargs):
        super().__init__(**kwargs)

        self.handle = handle
        self.flashcard_sets = flashcard_sets
        self.win: None | MainWindow = None

        self.connect("activate", self.on_activate)

    def on_activate(self, app: Self):
        """
        Handle window setup on activation of application.
        """
        self.win = MainWindow(self.handle, self.flashcard_sets, application=app)
        self.win.set_title("Language Practice")
        self.win.set_default_size(700, 700)
        self.win.present()


class MainWindow(Gtk.ApplicationWindow):
    """
    Main window for GUI application.
    """

    def __init__(
        self, handle: SqliteHandle, flashcard_sets: list[str], *args, **kwargs
    ):
        super().__init__(*args, **kwargs)

        self.handle = handle
        self.imports: list[str] = []
        self.flashcard: Flashcard | None = None

        vbox = Gtk.Box(spacing=6, orientation=Gtk.Orientation.VERTICAL)

        self.flashcard_set_grid = FlashcardSetGrid()
        for flashcard_set in flashcard_sets:
            self.flashcard_set_grid.add_row(
                Gtk.CheckButton(), Gtk.Label.new(flashcard_set)
            )
        scrollable = Gtk.ScrolledWindow()
        scrollable.set_size_request(700, 600)
        scrollable.set_child(self.flashcard_set_grid)

        button_hbox = Gtk.Box(spacing=6)
        import_button = Gtk.Button(label="Import")
        import_button.connect("clicked", self.import_button)
        button_hbox.append(import_button)
        delete_button = Gtk.Button(label="Delete")
        delete_button.connect("clicked", self.delete_flashcard_set)
        button_hbox.append(delete_button)
        select_all_button = Gtk.Button(label="Select all")
        select_all_button.connect("clicked", self.flashcard_set_grid.select_all)
        button_hbox.append(select_all_button)
        start_button = Gtk.Button(label="Start")
        start_button.connect("clicked", self.handle_start)
        button_hbox.append(start_button)
        button_hbox.set_halign(Gtk.Align.CENTER)

        vbox.append(scrollable)
        vbox.append(button_hbox)

        self.set_child(vbox)

    #  pylint: disable=unused-argument
    def import_button(self, button: Gtk.Button):
        """
        Handle import button action.
        """
        file_dialog = Gtk.FileDialog()
        file_dialog.open_multiple(callback=self.handle_files)

    #  pylint: disable=unused-argument
    def delete_flashcard_set(self, button: Gtk.Button):
        """
        Handle deleting flashcard set on button press.
        """
        selected = self.flashcard_set_grid.get_selected()
        selected.sort(reverse=True, key=lambda info: info[1])
        for text, row in selected:
            set_id = self.handle.get_id_from_file_name(text)
            if set_id is not None:
                self.handle.delete_set(set_id)
            self.flashcard_set_grid.delete_row(row)

    def handle_files(self, dialog: Gtk.FileDialog, task: Gio.Task):
        """
        Handle importing files on button press.
        """
        self.imports = [entry.get_path() for entry in dialog.open_multiple_finish(task)]
        for current_import in self.imports:
            try:
                toml = TomlConfig(current_import)
            except tomllib.TOMLDecodeError as err:
                dialog = Gtk.AlertDialog()
                dialog.set_message(f"{current_import}: {err}")
                dialog.set_modal(True)
                dialog.choose()
                continue
            except UnicodeDecodeError as err:
                dialog = Gtk.AlertDialog()
                dialog.set_message(f"{current_import}: {err}")
                dialog.set_modal(True)
                dialog.choose()
                continue

            try:
                new = self.handle.import_set(
                    current_import,
                    toml,
                    asyncio.run(scrape(toml.get_words(), toml.get_lang())),
                )
            except IntegrityError as err:
                dialog = Gtk.AlertDialog()
                dialog.set_message(f"{current_import}: {err}")
                dialog.set_modal(True)
                dialog.choose()
                set_id = self.handle.get_id_from_file_name(current_import)
                if set_id is not None:
                    self.handle.delete_set(set_id)
                continue

            if new:
                self.flashcard_set_grid.add_row(
                    Gtk.CheckButton(),
                    Gtk.Label.new(current_import),
                )
        self.imports = []

    #  pylint: disable=unused-argument
    def handle_start(self, button: Gtk.Button):
        """
        Handle starting flashcard study
        """
        files = self.flashcard_set_grid.get_selected()
        config = None
        for text, _ in files:
            if config is None:
                config = self.handle.load_config(text)
            else:
                config = config.extend(self.handle.load_config(text))

        if config is not None:
            self.flashcard = Flashcard(self.handle, config.get_words())
            win = StudyWindow(self.flashcard)
            win.connect("destroy", self.handle_study_exit)
            win.set_default_size(700, 300)
            win.present()

    def handle_study_exit(self):
        """
        Handle exit of study window.
        """
        if self.flashcard is not None:
            self.flashcard.save()
        self.flashcard = None


class FlashcardSetGrid(Gtk.Grid):
    """
    Grid used for flashcard sets.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.set_column_spacing(10)
        self.num_rows = 0

    def add_row(self, checkbox: Gtk.CheckButton, label: Gtk.Label):
        """
        Add a row to the grid.
        """
        self.attach(checkbox, 0, self.num_rows, 1, 1)
        self.attach(label, 1, self.num_rows, 1, 1)
        self.num_rows += 1

    def delete_row(self, row):
        """
        Delete a row from the grid.
        """
        self.remove_row(row)
        self.num_rows -= 1

    #  pylint: disable=unused-argument
    def select_all(self, button: Gtk.Button):
        """
        Mark all checkboxes as selected.
        """
        for row in range(self.num_rows):
            self.get_child_at(0, row).set_active(True)

    #  pylint: disable=unused-argument
    def get_selected(self) -> list[tuple[str, int]]:
        """
        Get all selected flashcard sets.
        """
        files = []
        for row in range(self.num_rows):
            if self.get_child_at(0, row).get_active():
                files.append((self.get_child_at(1, row).get_text(), row))

        return files


class StudyWindow(Gtk.ApplicationWindow):
    """
    Window for studying flashcards.
    """

    def __init__(self, flashcard: Flashcard, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_title("Language Practice")
        self.flashcard = flashcard

        (self.peek, self.is_review) = self.flashcard.current()
        if self.peek is not None:
            button_hbox_1 = self.grade_button_box()
            button_hbox_2 = self.navigation_button_box()

            self.display_box = Gtk.ScrolledWindow()
            self.display_box.set_halign(Gtk.Align.CENTER)
            self.display_box.set_size_request(700, 200)
            self.initial_display()

            vbox = Gtk.Box(spacing=6, orientation=Gtk.Orientation.VERTICAL)
            vbox.append(self.display_box)
            vbox.append(button_hbox_1)
            vbox.append(button_hbox_2)

            self.set_child(vbox)

    def grade_button_box(self) -> Gtk.Box:
        """
        Set up button box for grading.
        """
        button_hbox_1 = Gtk.Box(spacing=6)
        zero = Gtk.Button(label="No recall")
        zero.connect("clicked", lambda button: self.grade(0))
        button_hbox_1.append(zero)
        one = Gtk.Button(label="Wrong, familiar")
        one.connect("clicked", lambda button: self.grade(1))
        button_hbox_1.append(one)
        two = Gtk.Button(label="Wrong, easy to remember")
        two.connect("clicked", lambda button: self.grade(2))
        button_hbox_1.append(two)
        three = Gtk.Button(label="Correct, hard")
        three.connect("clicked", lambda button: self.grade(3))
        button_hbox_1.append(three)
        four = Gtk.Button(label="Correct, medium")
        four.connect("clicked", lambda button: self.grade(4))
        button_hbox_1.append(four)
        five = Gtk.Button(label="Correct, easy")
        five.connect("clicked", lambda button: self.grade(5))
        button_hbox_1.append(five)
        button_hbox_1.set_halign(Gtk.Align.CENTER)

        return button_hbox_1

    def navigation_button_box(self) -> Gtk.Box:
        """
        Set up button box for navigation.
        """
        button_hbox_2 = Gtk.Box(spacing=6)
        definition = Gtk.Button(label="Flashcard front")
        definition.connect("clicked", lambda button: self.initial_display())
        button_hbox_2.append(definition)
        back = Gtk.Button(label="Flashcard back")
        back.connect("clicked", lambda button: self.on_flashcard_back())
        button_hbox_2.append(back)
        usage = Gtk.Button(label="Usage")
        usage.connect("clicked", lambda button: self.on_usage())
        button_hbox_2.append(usage)
        charts = Gtk.Button(label="Charts")
        charts.connect("clicked", lambda button: self.on_charts())
        button_hbox_2.append(charts)
        button_hbox_2.set_halign(Gtk.Align.CENTER)

        return button_hbox_2

    def next(self):
        """
        Select next flashcard.
        """
        self.flashcard.post_grade()
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
            definition = Gtk.Label.new(self.peek.get_definition())
            box = Gtk.Box(spacing=10)
            box.prepend(definition)
            if part_of_speech is not None:
                box.prepend(Gtk.Label.new(part_of_speech))
            if aspect is not None:
                box.prepend(Gtk.Label.new(aspect))
            self.display_box.set_child(box)

    def on_flashcard_back(self):
        """
        Handle flashcard back button press.
        """
        if self.peek is not None:
            word = Gtk.Label.new(self.peek.get_word())
            gender = self.peek.get_gender()
            box = Gtk.Box(spacing=10)
            box.prepend(word)
            if gender is None:
                box.prepend(Gtk.Label.new(gender))
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
                    grid.set_column_spacing(10)
                    grid.set_row_spacing(10)
                    for i, row in enumerate(chart):
                        for j, col_val in enumerate(row):
                            grid.attach(Gtk.Label.new(col_val), j, i, 1, 1)

                    vbox.append(grid)

            self.display_box.set_child(vbox)
