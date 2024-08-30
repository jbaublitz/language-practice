"""
Parsing for Russian language grammar charts.
"""

from bs4 import BeautifulSoup

from language_practice.web.shared import uk_ru_tables


def parse(html: BeautifulSoup) -> list[list[list[str]]]:
    """
    Parse HTML returned from web request for a Russian word.
    """
    all_tables = html.find_all("table", {"class": "inflection-table"})
    tables = [table for table in all_tables if table.select(".lang-ru") != []]

    charts = uk_ru_tables(tables, "ru-Latn")

    rows = []

    comparative = html.find_all("b", {"class": "comparative-form-of"})
    if comparative:
        rows.append([comp.text for comp in comparative])

    superlative = html.find_all("b", {"class": "superlative-form-of"})
    if superlative:
        rows.append([sup.text for sup in superlative])

    if rows:
        charts.append(rows)

    return charts
