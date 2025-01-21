"""
Flashcard handling code.
"""

from collections import deque
from datetime import date
from random import shuffle

from language_practice.config import Entry
from language_practice.sqlite import SqliteHandle


class Flashcard:
    """
    Handler for studying flashcards.
    """

    def __init__(self, handle: SqliteHandle, words: list[Entry]):
        self.handle = handle

        scheduled: list[Entry] = []
        review: list[Entry] = []
        for entry in words:
            repetition = entry.get_repetition()
            if repetition.get_review():
                review.append(entry)
            elif repetition.get_date_of_next() <= date.today():
                scheduled.append(entry)

        shuffle(scheduled)
        self.scheduled = deque(scheduled)
        shuffle(review)
        self.review = deque(review)
        self.complete: list[Entry] = []

    def flashcards_left(self) -> int:
        """
        Get number of flashcards left.
        """
        return len(self.scheduled) + len(self.review)

    def current(self) -> tuple[Entry | None, bool | None]:
        """
        Get current flashcard.
        """
        if len(self.scheduled) > 0:
            current_entry = self.scheduled[0]
            is_review = False
        elif len(self.review) > 0:
            current_entry = self.review[0]
            is_review = True
        else:
            current_entry = None
            is_review = None

        return (current_entry, is_review)

    def post_grade(self):
        """
        Handle changing to a new flashcard after grading has been completed.
        """
        if len(self.scheduled) > 0:
            next_entry = self.scheduled.popleft()
        else:
            next_entry = self.review.popleft()

        self.handle.update_config(next_entry.get_word(), next_entry.get_repetition())

        if next_entry.get_repetition().get_review():
            self.review.append(next_entry)
        else:
            self.complete.append(next_entry)

    def get_all_entries(self) -> list[Entry]:
        """
        Get all flashcard entries.
        """
        return list(self.review) + list(self.scheduled) + self.complete
