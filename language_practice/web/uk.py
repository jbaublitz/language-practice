"""
Parsing for Ukrainian language grammar charts.
"""


from language_practice.web.shared import uk_ru_tables


def parse(html):
    """
    Parse HTML returned from web request for a Russian word.
    """
    cache = {}

    all_tables = html.find_all("table", {"class": "inflection-table"})
    tables = [table for table in all_tables if table.select(".lang-uk") != []]

    uk_ru_tables(cache, tables, "uk-Latn")

    return cache
