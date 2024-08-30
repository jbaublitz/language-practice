"""
Parsing for Ukrainian language grammar charts.
"""

from bs4 import BeautifulSoup

from language_practice.web.shared import uk_ru_tables


def parse(html: BeautifulSoup) -> list[list[list[str]]]:
    """
    Parse HTML returned from web request for a Russian word.
    """
    all_tables = html.find_all("table", {"class": "inflection-table"})
    tables = [table for table in all_tables if table.select(".lang-uk") != []]

    charts = uk_ru_tables(tables, "uk-Latn")

    return charts
