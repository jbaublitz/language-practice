"""
Parsing for French language grammar charts.
"""

from bs4 import BeautifulSoup


def parse(html: BeautifulSoup) -> list[list[list[str]]]:
    """
    Parse HTML returned from web request for a French word.
    """
    all_tables = html.find_all("table", {"class": "inflection-table"})
    tables = [table for table in all_tables if table.select(".lang-fr") != []]

    charts = []
    for table in tables:
        for entry_to_remove in table.find_all("span", {"class": "IPA"}):
            entry_to_remove.decompose()
        chart = [
            [
                entry.text.strip()
                for entry in tr
                if (entry.name == "td" and entry.get("colspan") != "8")
                or (entry.name == "th" and entry.get("colspan") == "6")
            ]
            for tr in table.find_all("tr")
        ]
        charts.append(chart)

    adj_forms = html.select(".form-of.lang-fr")
    if adj_forms:
        charts.append([[adj.text for adj in adj_forms]])

    return charts
