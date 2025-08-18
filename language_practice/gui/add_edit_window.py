"""
Implementation of the add and edit window.
"""

from gi.repository import Gtk

from language_practice.config import Entry


# pylint: disable=too-many-instance-attributes
# pylint: disable=too-many-statements
class AddEditWindow(Gtk.ApplicationWindow):
    """
    Window for adding or editing entries.
    """

    def __init__(self, config: Entry | None, callback, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.set_default_size(-1, 600)

        self.set_title("Language Practice")

        self.main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        self.entry = config

        self.scrollable = Gtk.ScrolledWindow()
        self.scrollable.set_vexpand(True)
        self.display = Gtk.ListBox()

        row = Gtk.ListBoxRow()
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        label = Gtk.Label()
        label.set_text("Word")
        label.set_css_classes(["add-edit-label"])
        label.set_hexpand(True)
        vbox.append(label)
        self.word_entry = Gtk.Entry()
        if config is not None:
            self.word_entry.set_text(config.get_word())
        self.word_entry.set_hexpand(True)
        vbox.append(self.word_entry)
        row.set_child(vbox)
        self.display.append(row)

        row = Gtk.ListBoxRow()
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        label = Gtk.Label()
        label.set_text("Definition")
        label.set_css_classes(["add-edit-label"])
        label.set_hexpand(True)
        vbox.append(label)
        self.definition_entry = Gtk.Entry()
        if config is not None:
            self.definition_entry.set_text(config.get_definition())
        self.definition_entry.set_hexpand(True)
        vbox.append(self.definition_entry)
        row.set_child(vbox)
        self.display.append(row)

        row = Gtk.ListBoxRow()
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        label = Gtk.Label()
        label.set_text("Usage")
        label.set_css_classes(["add-edit-label"])
        label.set_hexpand(True)
        vbox.append(label)
        self.usage_entry = Gtk.Entry()
        if config is not None:
            usage = config.get_usage()
            if usage is not None:
                self.usage_entry.set_text(usage)
        self.usage_entry.set_hexpand(True)
        vbox.append(self.usage_entry)
        row.set_child(vbox)
        self.display.append(row)

        row = Gtk.ListBoxRow()
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        label = Gtk.Label()
        label.set_text("Gender")
        label.set_css_classes(["add-edit-label"])
        label.set_hexpand(True)
        vbox.append(label)
        self.gender_entry = Gtk.Entry()
        if config is not None:
            gender = config.get_gender()
            if gender is not None:
                self.gender_entry.set_text(gender)
        self.gender_entry.set_hexpand(True)
        vbox.append(self.gender_entry)
        row.set_child(vbox)
        self.display.append(row)

        row = Gtk.ListBoxRow()
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        label = Gtk.Label()
        label.set_text("Aspect")
        label.set_css_classes(["add-edit-label"])
        label.set_hexpand(True)
        vbox.append(label)
        self.aspect_entry = Gtk.Entry()
        if config is not None:
            aspect = config.get_aspect()
            if aspect is not None:
                self.aspect_entry.set_text(aspect)
        self.aspect_entry.set_hexpand(True)
        vbox.append(self.aspect_entry)
        row.set_child(vbox)
        self.display.append(row)

        row = Gtk.ListBoxRow()
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        label = Gtk.Label()
        label.set_text("Part of Speech")
        label.set_css_classes(["add-edit-label"])
        label.set_hexpand(True)
        vbox.append(label)
        self.pos_entry = Gtk.Entry()
        if config is not None:
            pos = config.get_part_of_speech()
            if pos is not None:
                self.pos_entry.set_text(pos)
        self.pos_entry.set_hexpand(True)
        vbox.append(self.pos_entry)
        row.set_child(vbox)
        self.display.append(row)

        button = Gtk.Button()
        button.set_label("Save")
        button.set_hexpand(False)
        button.set_halign(Gtk.Align.CENTER)
        button.connect("clicked", self.on_save_click)

        self.scrollable.set_child(self.display)
        self.main_vbox.append(self.scrollable)
        self.main_vbox.append(button)
        self.set_child(self.main_vbox)

        self.callback = callback

    # pylint: disable=unused-argument
    def on_save_click(self, button):
        """
        Handle save button press.
        """
        if self.entry is not None:
            word = self.word_entry.get_text()
            if word == "":
                dialog = Gtk.AlertDialog()
                dialog.set_message("Word field is required and must not be empty")
                dialog.set_modal(True)
                dialog.choose()
                return
            self.entry.word = word

            definition = self.definition_entry.get_text()
            if definition == "":
                dialog = Gtk.AlertDialog()
                dialog.set_message("Definition field is required and must not be empty")
                dialog.set_modal(True)
                dialog.choose()
                return
            self.entry.definition = definition

            usage = self.usage_entry.get_text()
            self.entry.usage = usage if usage != "" else None

            part_of_speech = self.pos_entry.get_text()
            self.entry.part_of_speech = part_of_speech if part_of_speech != "" else None

            gender = self.gender_entry.get_text()
            self.entry.gender = gender if gender != "" else None

            aspect = self.aspect_entry.get_text()
            self.entry.aspect = aspect if aspect != "" else None

        self.callback(self.entry)

        self.close()
