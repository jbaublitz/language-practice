"""
Parsing for Russian language grammar charts.
"""


from language_practice.web.shared import uk_ru_tables


def parse(html):
    """
    Parse HTML returned from web request for a Russian word.
    """
    cache = {}

    all_tables = html.find_all("table", {"class": "inflection-table"})
    tables = [table for table in all_tables if table.select(".lang-ru") != []]

    uk_ru_tables(cache, tables, "ru-Latn")

    comparative = html.find_all("b", {"class": "comparative-form-of"})
    if comparative:
        cache["comparative"] = [comp.text for comp in comparative]

    superlative = html.find_all("b", {"class": "superlative-form-of"})
    if superlative:
        cache["superlative"] = [sup.text for sup in superlative]

    return cache
