"""
Graphical user interface.
"""

#  pylint: disable=wrong-import-position
#  pylint: disable=too-few-public-methods

import asyncio
import functools
import os
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

from language_practice.config import Config, TomlConfig
from language_practice.flashcard import Flashcard  # type: ignore
from language_practice.gui.study_window import StudyWindow
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

    def __init__(self, handle: SqliteHandle, loop, **kwargs):
        super().__init__(**kwargs)

        self.win: None | MainWindow = None
        self.handle = handle
        self.loop = loop

        self.connect("activate", self.on_activate)

    def on_activate(self, app: Self):
        """
        Handle window setup on activation of application.
        """
        self.win = MainWindow(self.handle, self.loop, application=app)
        self.win.set_title("Language Practice")

        css = Gtk.CssProvider()
        css.load_from_string(
            """
            list {
                background-color: @theme_bg_color;
                color: @theme_text_color;
                margin-top: 15px;
                margin-bottom: 15px;
                margin-left: 15px;
                margin-right: 15px;
            }

            list > row:first-child {
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }

            list row {
                background-color: hsl(from @theme_bg_color calc(h - 2) calc(s - 2) calc(l - 2));
                padding: 12px;
                transition: background 150ms ease;
                border-top: 1px solid @borders;
                border-left: 1px solid @borders;
                border-right: 1px solid @borders;
            }
            
            list row label {
                margin-left: 20px;
            }

            list > row:last-child {
                border-bottom-left-radius: 8px;
                border-bottom-right-radius: 8px;
                border-bottom: 1px solid @borders;
            }

            grid {
                margin-left: 10px;
                margin-right: 10px;
                margin-bottom: 10px;
                margin-top: 10px;
            }

            grid label {
                background-color: hsl(from @theme_bg_color calc(h - 2) calc(s - 2) calc(l - 2));
                border-top: 1px solid @borders;
                border-left: 1px solid @borders;
                border-right: 1px solid @borders;
                border-bottom: 1px solid @borders;
                border-radius: 6px;
                padding: 10px;
            }

            button.main-buttons {
                margin-top: 15px;
                margin-bottom: 15px;
                margin-left: 15px;
                margin-right: 15px;
            }

            button.study-top {
                border-radius: 0px 0px 0px 0px;
                margin-bottom: 5px;
            }

            box button.study-top:last-child {
                border-radius: 0px 6px 6px 0px;
                margin-right: 10px;
            }

            box button.study-top:first-child {
                border-radius: 6px 0px 0px 6px;
                margin-left: 10px;
            }

            button.study-bottom {
                border-radius: 0px 0px 0px 0px;
                margin-top: 5px;
                margin-bottom: 10px;
            }

            box button.study-bottom:last-child {
                border-radius: 0px 6px 6px 0px;
                margin-right: 10px;
            }

            box button.study-bottom:first-child {
                border-radius: 6px 0px 0px 6px;
                margin-left: 10px;
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

            label.lang {
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


# pylint: disable=too-many-instance-attributes
class MainWindow(Gtk.ApplicationWindow):
    """
    Main window for GUI application.
    """

    # pylint: disable=too-many-statements
    # pylint: disable=too-many-locals
    def __init__(self, handle: SqliteHandle, loop, **kwargs):
        super().__init__(**kwargs)

        self.loop = loop

        self.set_default_size(600, 600)

        self.handle = handle
        self.search_scrollable = None
        self.flashcard: Flashcard | None = None

        self.vbox = Gtk.Box(spacing=6, orientation=Gtk.Orientation.VERTICAL)

        self.searchbar = Gtk.SearchBar()
        self.searchbar.set_hexpand(True)
        searchentry = Gtk.SearchEntry()
        searchentry.set_hexpand(True)
        searchentry.connect("changed", self.on_key_event)
        self.searchbar.connect_entry(searchentry)
        self.searchbar.set_child(searchentry)
        self.vbox.append(self.searchbar)

        self.flashcard_sets = FlashcardListBox()
        self.scrollable = Gtk.ScrolledWindow()
        self.scrollable.set_vexpand(True)
        self.scrollable.set_child(self.flashcard_sets)

        self.button_hbox = Gtk.Box()
        select_all_button = Gtk.Button()
        select_all_button.set_icon_name("edit-select-all")
        select_all_button.connect("clicked", self.flashcard_sets.select_all_checks)
        select_all_button.set_css_classes(["main-buttons"])
        self.button_hbox.append(select_all_button)
        deselect_all_button = Gtk.Button()
        deselect_all_button.set_icon_name("edit-clear-all")
        deselect_all_button.connect("clicked", self.flashcard_sets.deselect_all_checks)
        deselect_all_button.set_css_classes(["main-buttons"])
        self.button_hbox.append(deselect_all_button)
        start_button = Gtk.Button()
        start_button.set_icon_name("media-playback-start")
        start_button.connect("clicked", self.handle_start)
        start_button.set_css_classes(["main-buttons"])
        self.button_hbox.append(start_button)
        self.button_hbox.set_halign(Gtk.Align.CENTER)

        self.vbox.append(self.scrollable)
        self.vbox.append(self.button_hbox)

        menu_model = Gio.Menu()

        action = Gio.SimpleAction.new("recreate_database")
        action.connect("activate", self.recreate_database)
        self.add_action(action)
        menu_model.append("Recreate database", "win.recreate_database")

        action = Gio.SimpleAction.new("export")
        action.connect("activate", self.export_button)
        self.add_action(action)
        menu_model.append("Export set", "win.export")

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

        search_button = Gtk.Button()
        search_button.set_icon_name("system-search")
        search_button.connect("clicked", self.toggle_search)
        search_button.show()

        headerbar = Gtk.HeaderBar()
        headerbar.props.show_title_buttons = True
        headerbar.pack_end(menu_button)
        headerbar.pack_end(search_button)
        headerbar.show()
        self.set_titlebar(headerbar)

        self.set_child(self.vbox)

        sets = self.handle.get_all_sets()
        for flashcard_set in sets:
            label = Gtk.Label(halign=Gtk.Align.START)
            label.set_text(flashcard_set)
            self.flashcard_sets.add_row(Gtk.CheckButton(), label)

    #  pylint: disable=unused-argument
    def toggle_search(self, button):
        """
        Toggle the search mode on or off.
        """
        searchmode = self.searchbar.get_search_mode()
        self.searchbar.set_search_mode(not searchmode)

    def on_key_event(self, entry):
        """
        Handle typing in the search bar.
        """
        if self.handle is not None:
            text = entry.get_text()
            if text == "":
                self.vbox.remove(self.search_scrollable)
                self.vbox.append(self.scrollable)
                self.vbox.append(self.button_hbox)
            else:
                if self.search_scrollable is not None:
                    self.vbox.remove(self.search_scrollable)
                if self.vbox == self.scrollable.get_parent():
                    self.vbox.remove(self.scrollable)
                if self.vbox == self.button_hbox.get_parent():
                    self.vbox.remove(self.button_hbox)
                search_grid = SearchListBox()
                res = self.handle.search(text)
                for tup in res:
                    search_grid.add_row(tup)
                self.search_scrollable = Gtk.ScrolledWindow()
                self.search_scrollable.set_vexpand(True)
                self.search_scrollable.set_child(search_grid)
                self.vbox.append(self.search_scrollable)

    def recreate_database(self, action, param):
        """
        Recreate the database.
        """
        db_path = self.handle.db_path()
        self.handle.close()
        os.remove(db_path)
        self.handle = SqliteHandle(db_path)
        self.flashcard_sets.clear()

    #  pylint: disable=unused-argument
    def import_button(self, action, param):
        """
        Handle import button action.
        """
        file_dialog = Gtk.FileDialog()
        file_dialog.open_multiple(callback=self.handle_import_files)

    #  pylint: disable=unused-argument
    def export_button(self, action, param):
        """
        Handle import button action.
        """
        selected = list(map(lambda tup: tup[0], self.flashcard_sets.get_selected()))
        file_dialog = Gtk.FileDialog()
        file_dialog.select_folder(
            callback=lambda dialog, task: self.handle_export_files(
                dialog, task, selected
            )
        )

    #  pylint: disable=unused-argument
    def delete_flashcard_set(self, action, param):
        """
        Handle deleting flashcard set on button press.
        """
        selected = self.flashcard_sets.get_selected()
        selected.sort(reverse=True, key=lambda info: info[1])
        for text, row in selected:
            set_id = self.handle.get_id_from_file_name(text)
            if set_id is not None:
                self.handle.delete_set(set_id)
            self.flashcard_sets.delete_row(row)

    def handle_import_files(self, dialog: Gtk.FileDialog, task: Gio.Task):
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

    def handle_export_files(self, dialog: Gtk.FileDialog, result, selected: list[str]):
        """
        Handle importing files on button press.
        """
        export_dest = dialog.select_folder_finish(result)
        if not os.path.isdir(export_dest):
            dialog = Gtk.AlertDialog()
            dialog.set_message(f"{export_dest} must be a directory")
            dialog.set_modal(True)
            dialog.choose()
            return

        for one_selected in selected:
            config = self.handle.export_config(one_selected)
            fut = asyncio.run_coroutine_threadsafe(
                self.handle_single_export(export_dest, config), self.loop
            )
            fut.result()

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

        return (toml, await scrape(toml.get_words()))

    async def handle_single_export(self, export_dest: str, config: Config):
        """
        Handle TOML exports.
        """
        config.export(export_dest)

    def update_ui_when_done(self, current_import, future):
        """
        Handle updating the UI on future completion.
        """
        (toml, scraped) = future.result(10)
        if toml is None or scraped is None:
            return

        (set_name, _) = os.path.splitext(os.path.basename(current_import))
        try:
            new = self.handle.import_set(
                set_name,
                toml,
                scraped,
            )
        except IntegrityError as err:
            dialog = Gtk.AlertDialog()
            dialog.set_message(f"{current_import}: {err}")
            dialog.set_modal(True)
            dialog.choose()
            set_id = self.handle.get_id_from_file_name(set_name)
            if set_id is not None:
                self.handle.delete_set(set_id)
            return
        except RuntimeError as err:
            dialog = Gtk.AlertDialog()
            dialog.set_message(f"{current_import}: {err}")
            dialog.set_modal(True)
            dialog.choose()
            set_id = self.handle.get_id_from_file_name(set_name)
            if set_id is not None:
                self.handle.delete_set(set_id)
            return

        if new:
            label = Gtk.Label(halign=Gtk.Align.START)
            label.set_text(set_name)
            self.flashcard_sets.add_row(Gtk.CheckButton(), label)

    #  pylint: disable=unused-argument
    def handle_start(self, button):
        """
        Handle starting flashcard study
        """
        files = self.flashcard_sets.get_selected()
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


class FlashcardListBox(Gtk.ListBox):
    """
    List box used for flashcard sets.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def add_row(self, checkbox: Gtk.CheckButton, label: Gtk.Label):
        """
        Add a row to the grid.
        """
        listboxrow = Gtk.ListBoxRow()
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        box.append(checkbox)
        box.append(label)
        listboxrow.set_child(box)
        self.append(listboxrow)

    def delete_row(self, row: int):
        """
        Delete a row from the grid.
        """
        row = self.get_row_at_index(row)
        self.remove(row)

    #  pylint: disable=unused-argument
    def select_all_checks(self, button):
        """
        Mark all checkboxes as selected.
        """
        for row in self:
            box = row.get_child()
            (checkbox, _) = list(box)
            checkbox.set_active(True)

    #  pylint: disable=unused-argument
    def deselect_all_checks(self, button):
        """
        Mark all checkboxes as selected.
        """
        for row in self:
            box = row.get_child()
            (checkbox, _) = list(box)
            checkbox.set_active(False)

    #  pylint: disable=unused-argument
    def get_selected(self) -> list[tuple[str, int]]:
        """
        Get all selected flashcard sets.
        """
        files = []
        for row_num, row in enumerate(self):
            box = row.get_child()
            (checkbox, label) = list(box)
            if checkbox.get_active():
                files.append((label.get_text(), row_num))

        return files

    def clear(self):
        """
        Clear all flashcard sets from the UI.
        """
        for row in list(self):
            self.remove(row)


class SearchListBox(Gtk.ListBox):
    """
    List box used for search.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def add_row(self, entries: tuple[str, str, str]):
        """
        Add a row to the grid.
        """
        row = Gtk.ListBoxRow()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        (word, definition, usage) = entries
        word_label = Gtk.Label()
        word_label.set_text(word)
        box.append(word_label)
        def_label = Gtk.Label()
        def_label.set_text(definition)
        box.append(def_label)
        if usage is not None:
            usage_label = Gtk.Label()
            usage_label.set_text(usage)
            box.append(usage_label)
        else:
            usage_label = None
        row.set_child(box)
        self.append(row)
