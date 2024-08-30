"""
Terminal application interface.
"""

import os
import tomllib
from uuid import uuid4

from textual.app import App
from textual.containers import (
    Container,
    Horizontal,
    HorizontalScroll,
    ScrollableContainer,
    Vertical,
)
from textual.css.query import NoMatches
from textual.dom import DOMNode
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    Checkbox,
    DataTable,
    DirectoryTree,
    Footer,
    Header,
    Label,
)

from language_practice.config import TomlConfig
from language_practice.flashcard import Flashcard
from language_practice.sqlite import SqliteHandle
from language_practice.web import scrape


class TerminalApplication(App):
    """
    Terminal application.
    """

    CSS = """
    .bottom-buttons-one {
        height: 3;
    }

    .bottom-buttons-two {
        height: 6;
    }

    .flashcard-set {
        height: 3;
    }
    """

    def __init__(
        self, handle: SqliteHandle, flashcard_sets: list[str], *args, **kwargs
    ):
        self.handle = handle
        self.flashcard_sets = flashcard_sets
        self.file_path = None
        self.flashcard: Flashcard | None = None
        self.imports: dict[str, str] = {}
        super().__init__(*args, **kwargs)

    def compose(self):
        yield Header()
        yield Footer()
        args = []
        for flashcard_set in self.flashcard_sets:
            hex_string = flashcard_set.encode("utf-8").hex()
            args.append(
                Horizontal(
                    Checkbox(id=f"select-{hex_string}"),
                    Container(),
                    Label(flashcard_set),
                    Container(),
                    Button("Delete", id=f"delete-{hex_string}"),
                    classes="flashcard-set",
                )
            )
        yield ScrollableContainer(*args, id="scrollable")
        yield Horizontal(
            Container(),
            Button("Import", id="import"),
            Button("Select all", id="select_all"),
            Button("Start", id="start"),
            Button("Exit", id="exit"),
            Container(),
            classes="bottom-buttons-one",
        )

    def on_start(self):
        """
        On start button press.
        """
        scrollable = self.query_one("#scrollable")
        checkboxes = map(lambda child: child.query_one(Checkbox), scrollable.children)
        config = None
        for checkbox in checkboxes:
            if checkbox.value:
                checkbox_id = checkbox.id
                if checkbox_id is not None:
                    name = bytes.fromhex(checkbox_id.split("select-")[1]).decode(
                        "utf-8"
                    )
                    if config is None:
                        config = self.handle.load_config(name)
                    else:
                        config = config.extend(self.handle.load_config(name))
        if config is not None:
            self.flashcard = Flashcard(self.handle, config.get_words())
            self.push_screen(StudyScreen(self.flashcard))

    def on_delete(self, button_id: str, parent: DOMNode | None):
        """
        On delete button press.
        """
        name = bytes.fromhex(button_id.split("delete-")[1]).decode("utf-8")
        self.handle.delete_set(name)
        if parent is not None:
            parent.remove()  # type: ignore

    def on_exit_study(self):
        """
        On exit study button press.
        """
        if self.flashcard is not None:
            self.flashcard.save()
        self.flashcard = None
        self.pop_screen()

    async def on_complete_import(self):
        """
        On complete import button press.
        """
        toml = None
        for import_file in self.imports:
            try:
                toml = TomlConfig(import_file)
            except tomllib.TOMLDecodeError:
                self.pop_screen()

            if toml is not None:
                self.handle.import_set(
                    import_file,
                    toml,
                    await scrape(toml.get_words(), toml.get_lang()),
                )

            hex_string = import_file.encode("utf-8").hex()
            scrollable = self.query_one("#scrollable")
            try:
                scrollable.query_one(f"#delete-{hex_string}")
            except NoMatches:
                scrollable.mount(
                    Horizontal(
                        Checkbox(id=f"select-{hex_string}"),
                        Container(),
                        Label(import_file),
                        Container(),
                        Button("Delete", id=f"delete-{hex_string}"),
                    )
                )

        self.pop_screen()

        self.imports = {}

    #  pylint: disable=too-many-branches
    async def on_button_pressed(self, event: Button.Pressed):
        """
        Handle button presses in application.
        """
        button_id = event.button.id
        if button_id is not None:
            if button_id == "import":
                self.push_screen(ImportPopup())
            elif button_id == "start":
                self.on_start()
            elif button_id.startswith("delete"):
                self.on_delete(button_id, event.button.parent)
            elif button_id == "exit":
                self.exit()
            elif button_id == "exit_study":
                self.on_exit_study()
            elif button_id == "complete_import":
                await self.on_complete_import()
            elif button_id == "select_all":
                for checkbox in self.query(Checkbox):
                    checkbox.value = True

    async def on_directory_tree_file_selected(self, event):
        """
        Handle directory tree selection in application.
        """
        table = self.query_one("#selected")
        path = event.path
        realpath = os.path.realpath(path)
        if realpath in self.imports:
            this_uuid = self.imports.pop(realpath)
            table.remove_row(this_uuid)
        else:
            this_uuid = str(uuid4())
            self.imports[realpath] = this_uuid
            table.add_row(realpath, key=this_uuid)


class ImportPopup(ModalScreen):
    """
    Popup for importing TOML files.
    """

    def compose(self):
        table = DataTable(id="selected")
        table.add_columns("Files")
        yield Vertical(
            HorizontalScroll(
                DirectoryTree(os.environ["HOME"]),
                table,
            ),
            Horizontal(
                Container(),
                Button("Complete import", id="complete_import"),
                Container(),
                classes="bottom-buttons-one",
            ),
        )


class StudyScreen(ModalScreen):
    """
    Study screen where flashcards can be reviewed.
    """

    def __init__(self, flashcard, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.flashcard = flashcard
        self.peek = None
        self.is_review = None

    def compose(self):
        (self.peek, self.is_review) = self.flashcard.current()
        if self.peek is not None:
            part_of_speech = self.peek.get_part_of_speech()
            aspect = self.peek.get_aspect()
            definition = self.peek.get_definition()
            if part_of_speech is not None:
                definition = r"\[" + f"{part_of_speech}] {definition}"
            if aspect is not None:
                definition = r"\[" + f"{aspect}] {definition}"
            yield Horizontal(
                Container(),
                Label(definition, id="display"),
                Container(id="post_display"),
            )
            yield Vertical(
                Horizontal(
                    Container(),
                    Button("No recall", id="zero"),
                    Button("Wrong, familiar", id="one"),
                    Button("Wrong, easy to remember", id="two"),
                    Button("Correct, hard", id="three"),
                    Button("Correct, medium", id="four"),
                    Button("Correct, easy", id="five"),
                    Container(),
                    id="grade",
                ),
                Horizontal(
                    Container(),
                    Button("Flashcard front", id="definition"),
                    Button("Flashcard back", id="word"),
                    Button("Usage", id="usage"),
                    Button("Charts", id="charts"),
                    Button("Exit", id="exit_study"),
                    Container(),
                ),
                classes="bottom-buttons-two",
            )
        else:
            yield Label("Nothing to study")
            yield Button("Exit", id="exit_study")

    def initial_display(self):
        """
        Initial display for a flashcard.
        """
        part_of_speech = self.peek.get_part_of_speech()
        aspect = self.peek.get_aspect()
        definition = self.peek.get_definition()
        if part_of_speech is not None:
            definition = r"\[" + f"{part_of_speech}] {definition}"
        if aspect is not None:
            definition = r"\[" + f"{aspect}] {definition}"
        self.mount(Label(definition, id="display"), before="#post_display")

    def next(self):
        """
        Select next flashcard.
        """
        self.flashcard.post_grade()
        (self.peek, self.is_review) = self.flashcard.current()

    async def at_end(self):
        """
        Handle condition at end of flashcard set.
        """
        self.mount(Label("All done!", id="display"), before="#post_display")
        await self.query_one("#grade").remove()
        await self.query_one("#definition").remove()
        await self.query_one("#word").remove()
        await self.query_one("#usage").remove()
        await self.query_one("#charts").remove()

    async def grade(self, grade):
        """
        Grade a flashcard.
        """
        if self.is_review:
            self.peek.get_repetition().review(grade)
        else:
            self.peek.get_repetition().grade(grade)
        self.next()
        await self.query_one("#display").remove()
        if self.peek is None:
            await self.at_end()
        else:
            self.initial_display()

    async def on_word(self):
        """
        Handle flashcard back button.
        """
        word = self.peek.get_word()
        gender = self.peek.get_gender()
        if gender is None:
            string = f"{word}"
        else:
            string = r"\[" + f"{gender}] {word}"
        await self.query_one("#display").remove()
        self.mount(Label(string, id="display"), before="#post_display")

    async def on_usage(self):
        """
        Handle usage button.
        """
        if self.peek.get_usage() is not None:
            await self.query_one("#display").remove()
            self.mount(
                Label(self.peek.get_usage(), id="display"), before="#post_display"
            )

    async def on_charts(self):
        """
        Handle charts button.
        """
        await self.query_one("#display").remove()
        tables = []
        for chart in self.peek.get_charts():
            table = DataTable(show_header=False)
            max_cols = max(map(len, chart))
            cols = [chr(i + 97) for i in range(0, max_cols)]
            table.add_columns(*cols)
            for row in chart:
                table.add_row(*row)
            tables.append(table)

        vert = Vertical(*tables, id="display")
        self.mount(vert, before="#post_display")

    #  pylint: disable=too-many-branches
    #  pylint: disable=too-many-statements
    async def on_button_pressed(self, event):
        """
        Handle button presses in study screen.
        """
        if event.button.id == "definition":
            await self.query_one("#display").remove()
            self.initial_display()
        elif event.button.id == "word":
            await self.on_word()
        elif event.button.id == "usage":
            await self.on_usage()
        elif event.button.id == "charts":
            await self.on_charts()
        elif event.button.id == "zero":
            await self.grade(0)
        elif event.button.id == "one":
            await self.grade(1)
        elif event.button.id == "two":
            await self.grade(2)
        elif event.button.id == "three":
            await self.grade(3)
        elif event.button.id == "four":
            await self.grade(4)
        elif event.button.id == "five":
            await self.grade(5)
