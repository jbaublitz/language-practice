"""
Handles spaced repetition.
"""

import math
from datetime import date, timedelta


class WordRepetition:
    """
    Information on a single word's repetition frequency.
    """

    DEFAULT_EASYNESS_FACTOR = 2.5

    #  pylint: disable=too-many-arguments
    #  pylint: disable=too-many-positional-arguments
    def __init__(
        self,
        easiness_factor: float,
        num_correct: int,
        in_n_days: int,
        date_of_next: date,
        should_review: bool,
    ):
        self.easiness_factor = easiness_factor
        self.num_correct = num_correct
        self.in_n_days = in_n_days
        self.date_of_next = date_of_next
        self.should_review = should_review

    def grade(self, grade: int):
        """
        Grade workflow.
        """
        if grade >= 3:
            if self.num_correct == 0:
                self.in_n_days = 1
                self.date_of_next = date.today() + timedelta(days=self.in_n_days)
            elif self.num_correct == 1:
                self.in_n_days = 6
                self.date_of_next = date.today() + timedelta(days=self.in_n_days)
            else:
                self.in_n_days = math.floor(self.in_n_days * self.easiness_factor)
                self.date_of_next = date.today() + timedelta(days=self.in_n_days)
            self.num_correct += 1

            if grade < 4:
                self.should_review = True
        else:
            self.num_correct = 0
            self.in_n_days = 1
            self.date_of_next = date.today() + timedelta(days=self.in_n_days)
            self.should_review = True

        self.easiness_factor = max(
            1.3,
            self.easiness_factor + (0.1 - (5 - grade) * (0.08 + (5 - grade) * 0.02)),
        )

    def review(self, grade: int):
        """
        Review workflow.
        """
        if grade >= 4:
            self.should_review = False

    def get_easiness_factor(self) -> float:
        """
        Get easiness factor.
        """
        return self.easiness_factor

    def get_num_correct(self) -> int:
        """
        Get number correct.
        """
        return self.num_correct

    def get_in_n_days(self) -> int:
        """
        Get the number of days in which a card should repeat.
        """
        return self.in_n_days

    def get_date_of_next(self) -> date:
        """
        Get the date on which a card should repeat.
        """
        return self.date_of_next

    def get_review(self) -> bool:
        """
        Get whether card should be reviewed.
        """
        return self.should_review
