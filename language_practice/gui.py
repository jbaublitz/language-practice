"""
Graphical user interface.
"""

#  pylint: disable=wrong-import-position
#  pylint: disable=too-few-public-methods

import asyncio
import functools
import tomllib
from sqlite3 import IntegrityError
from threading import Thread
from typing import Self

import gi  # type: ignore

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import (  # type: ignore  # pylint: disable=wrong-import-order
    Adw,
    Gio,
    GLib,
    Gtk,
)

from language_practice.config import TomlConfig
from language_practice.flashcard import Flashcard  # type: ignore
from language_practice.sqlite import SqliteHandle
from language_practice.web import scrape


def start_loop():
    """
    Start asyncio event loop
    """
    loop = asyncio.new_event_loop()
    Thread(target=loop.run_forever, daemon=True).start()
    return loop


class GuiApplication(Adw.Application):
    """
    Graphical application.
    """

    def __init__(self, loop, **kwargs):
        super().__init__(**kwargs)

        self.win: None | MainWindow = None
        self.loop = loop

        self.connect("activate", self.on_activate)

    def on_activate(self, app: Self):
        """
        Handle window setup on activation of application.
        """
        self.win = MainWindow(self.loop, application=app)
        self.win.set_title("Language Practice")

        css = Gtk.CssProvider.new()
        css.load_from_string(
            """
            grid {
                margin-top: 15px;
                margin-bottom: 15px;
                margin-left: 15px;
                margin-right: 15px;
            }

            button.main-buttons {
                margin-top: 15px;
                margin-bottom: 15px;
                margin-left: 15px;
                margin-right: 15px;
            }

            button.study-buttons {
                margin-left: 15px;
                margin-right: 15px;
            }

            button.study-top {
                margin-top: 15px;
                margin-bottom: 15px;
            }

            button.study-bottom {
                margin-bottom: 15px;
            }

            label.word {
                font-size: 40px;
                margin-top: 15px;
                margin-bottom: 45px;
                margin-left: 15px;
                margin-right: 15px;
            }

            label.counter {
                font-size: 30px;
                margin-top: 15px;
                margin-bottom: 15px;
                margin-left: 15px;
                margin-right: 15px;
            }
            """
        )

        Gtk.StyleContext.add_provider_for_display(
            Gtk.Widget.get_display(self.win),
            css,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

        self.win.present()


class MainWindow(Gtk.ApplicationWindow):
    """
    Main window for GUI application.
    """

    # pylint: disable=too-many-statements
    def __init__(self, loop, **kwargs):
        super().__init__(**kwargs)

        self.loop = loop

        self.set_default_size(600, 600)

        self.handle = None
        self.flashcard: Flashcard | None = None

        vbox = Gtk.Box(spacing=6, orientation=Gtk.Orientation.VERTICAL)

        self.flashcard_set_grid = FlashcardSetGrid()
        scrollable = Gtk.ScrolledWindow()
        scrollable.set_vexpand(True)
        scrollable.set_child(self.flashcard_set_grid)

        button_hbox = Gtk.Box()
        select_all_button = Gtk.Button()
        select_all_button.set_icon_name("edit-select-all")
        select_all_button.connect("clicked", self.flashcard_set_grid.select_all)
        select_all_button.set_css_classes(["main-buttons"])
        button_hbox.append(select_all_button)
        deselect_all_button = Gtk.Button()
        deselect_all_button.set_icon_name("edit-clear-all")
        deselect_all_button.connect("clicked", self.flashcard_set_grid.deselect_all)
        deselect_all_button.set_css_classes(["main-buttons"])
        button_hbox.append(deselect_all_button)
        start_button = Gtk.Button()
        start_button.set_icon_name("media-playback-start")
        start_button.connect("clicked", self.handle_start)
        start_button.set_css_classes(["main-buttons"])
        button_hbox.append(start_button)
        button_hbox.set_halign(Gtk.Align.CENTER)

        vbox.append(scrollable)
        vbox.append(button_hbox)

        menu_model = Gio.Menu()

        action = Gio.SimpleAction.new("db_create")
        action.connect("activate", self.db_create_button)
        self.add_action(action)
        menu_model.append("Create database", "win.db_create")

        action = Gio.SimpleAction.new("db_import")
        action.connect("activate", self.db_import_button)
        self.add_action(action)
        menu_model.append("Import database", "win.db_import")

        action = Gio.SimpleAction.new("db_close")
        action.connect("activate", self.db_close_button)
        self.add_action(action)
        menu_model.append("Close database", "win.db_close")

        action = Gio.SimpleAction.new("import")
        action.connect("activate", self.import_button)
        self.add_action(action)
        menu_model.append("Import set", "win.import")

        action = Gio.SimpleAction.new("delete")
        action.connect("activate", self.delete_flashcard_set)
        self.add_action(action)
        menu_model.append("Delete set", "win.delete")

        popover = Gtk.PopoverMenu()
        popover.set_menu_model(menu_model)
        popover.set_position(Gtk.PositionType.BOTTOM)

        menu_button = Gtk.MenuButton()
        menu_button.set_popover(popover)
        menu_button.set_icon_name("open-menu-symbolic")
        menu_button.show()

        headerbar = Gtk.HeaderBar()
        headerbar.props.show_title_buttons = True
        headerbar.pack_end(menu_button)
        headerbar.show()
        self.set_titlebar(headerbar)

        self.set_child(vbox)

        self.connect("destroy", self.on_destroy)

    #  pylint: disable=unused-argument
    def on_destroy(self):
        """
        Cleanup handler for application.
        """
        if self.handle is not None:
            self.handle.close()

    #  pylint: disable=unused-argument
    def db_create_button(self, action, param):
        """
        Handle database creation button action.
        """
        if self.handle is not None:
            dialog = Gtk.AlertDialog()
            dialog.set_message("Database already imported")
            dialog.set_modal(True)
            dialog.choose()
            return
        file_chooser = Gtk.FileDialog()
        file_chooser.save(self, None, self.create, None)

    #  pylint: disable=unused-argument
    def create(self, source, res, data):
        """
        Database creation callback.
        """
        self.handle = SqliteHandle(source.save_finish(res).get_path())

    #  pylint: disable=unused-argument
    def db_import_button(self, action, param):
        """
        Handle database import button action.
        """
        if self.handle is not None:
            dialog = Gtk.AlertDialog()
            dialog.set_message("Database already imported")
            dialog.set_modal(True)
            dialog.choose()
            return
        file_chooser = Gtk.FileDialog()
        file_chooser.open(self, None, self.open, None)

    #  pylint: disable=unused-argument
    def open(self, source, res, data):
        """
        Database import callback.
        """
        self.handle = SqliteHandle(source.open_finish(res).get_path())
        sets = self.handle.get_all_sets()
        for flashcard_set in sets:
            label = Gtk.Label(halign=Gtk.Align.START)
            label.set_text(flashcard_set)
            self.flashcard_set_grid.add_row(Gtk.CheckButton(), label)

    #  pylint: disable=unused-argument
    def db_close_button(self, action, param):
        """
        Handle database import button action.
        """
        if self.handle is None:
            dialog = Gtk.AlertDialog()
            dialog.set_message("No database to close")
            dialog.set_modal(True)
            dialog.choose()
            return
        self.flashcard_set_grid.clear()
        self.handle.close()
        self.handle = None

    #  pylint: disable=unused-argument
    def import_button(self, action, param):
        """
        Handle import button action.
        """
        if self.handle is None:
            dialog = Gtk.AlertDialog()
            dialog.set_message("Must create or import database first")
            dialog.set_modal(True)
            dialog.choose()
            return
        file_dialog = Gtk.FileDialog()
        file_dialog.open_multiple(callback=self.handle_files)

    #  pylint: disable=unused-argument
    def delete_flashcard_set(self, action, param):
        """
        Handle deleting flashcard set on button press.
        """
        if self.handle is None:
            dialog = Gtk.AlertDialog()
            dialog.set_message("Must create or import database first")
            dialog.set_modal(True)
            dialog.choose()
            return

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
        imports = [entry.get_path() for entry in dialog.open_multiple_finish(task)]

        for current_import in imports:
            fut = asyncio.run_coroutine_threadsafe(
                self.handle_single_import(current_import), self.loop
            )
            fut.add_done_callback(
                functools.partial(
                    GLib.idle_add, self.update_ui_when_done, current_import
                )
            )

    async def handle_single_import(self, current_import: str):
        """
        Handle TOML parsing and web scraping.
        """
        try:
            toml = TomlConfig(current_import)
        except tomllib.TOMLDecodeError as err:
            dialog = Gtk.AlertDialog()
            dialog.set_message(f"{current_import}: {err}")
            dialog.set_modal(True)
            dialog.choose()
            return (None, None)
        except UnicodeDecodeError as err:
            dialog = Gtk.AlertDialog()
            dialog.set_message(f"{current_import}: {err}")
            dialog.set_modal(True)
            dialog.choose()
            return (None, None)
        except RuntimeError as err:
            dialog = Gtk.AlertDialog()
            dialog.set_message(f"{current_import}: {err}")
            dialog.set_modal(True)
            dialog.choose()
            return (None, None)

        return (toml, await scrape(toml.get_words(), toml.get_lang()))

    def update_ui_when_done(self, current_import, future):
        """
        Handle updating the UI on future completion.
        """
        (toml, scraped) = future.result(10)
        if toml is None or scraped is None:
            return

        try:
            new = self.handle.import_set(
                current_import,
                toml,
                scraped,
            )
        except IntegrityError as err:
            dialog = Gtk.AlertDialog()
            dialog.set_message(f"{current_import}: {err}")
            dialog.set_modal(True)
            dialog.choose()
            set_id = self.handle.get_id_from_file_name(current_import)
            if set_id is not None:
                self.handle.delete_set(set_id)
            return
        except RuntimeError as err:
            dialog = Gtk.AlertDialog()
            dialog.set_message(f"{current_import}: {err}")
            dialog.set_modal(True)
            dialog.choose()
            set_id = self.handle.get_id_from_file_name(current_import)
            if set_id is not None:
                self.handle.delete_set(set_id)
            return

        if new:
            label = Gtk.Label(halign=Gtk.Align.START)
            label.set_text(current_import)
            self.flashcard_set_grid.add_row(Gtk.CheckButton(), label)

    #  pylint: disable=unused-argument
    def handle_start(self, button):
        """
        Handle starting flashcard study
        """
        if self.handle is None:
            dialog = Gtk.AlertDialog()
            dialog.set_message("Must create or import database first")
            dialog.set_modal(True)
            dialog.choose()
            return
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
            win.present()


class FlashcardSetGrid(Gtk.Grid):
    """
    Grid used for flashcard sets.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.set_column_spacing(15)
        self.set_row_spacing(15)
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
    def select_all(self, button):
        """
        Mark all checkboxes as selected.
        """
        for row in range(self.num_rows):
            self.get_child_at(0, row).set_active(True)

    #  pylint: disable=unused-argument
    def deselect_all(self, button):
        """
        Mark all checkboxes as selected.
        """
        for row in range(self.num_rows):
            self.get_child_at(0, row).set_active(False)

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

    def clear(self):
        """
        Clear all flashcard sets from the UI.
        """
        for i in reversed(range(self.num_rows)):
            self.delete_row(i)


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

            vbox = Gtk.Box(spacing=6, orientation=Gtk.Orientation.VERTICAL)
            self.counter_label = Gtk.Label(halign=Gtk.Align.START)
            self.counter_label.set_text(f"{self.flashcard.flashcards_left()} left")
            self.counter_label.set_css_classes(["counter"])
            vbox.append(self.counter_label)
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
        button_hbox_1 = Gtk.Box(spacing=6)
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
        button_hbox_2 = Gtk.Box(spacing=6)
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
                    grid.set_column_spacing(10)
                    grid.set_row_spacing(10)
                    for i, row in enumerate(chart):
                        for j, col_val in enumerate(row):
                            grid.attach(Gtk.Label.new(col_val), j, i, 1, 1)

                    vbox.append(grid)

            self.display_box.set_child(vbox)
