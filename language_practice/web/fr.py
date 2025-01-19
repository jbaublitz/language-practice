"""
Parsing for French language grammar charts.
"""

from bs4 import BeautifulSoup


def parse(html: BeautifulSoup) -> list[list[list[str]]]:
    """
    Parse HTML returned from web request for a French word.
    """
    all_tables = html.find_all("table")
    tables = [table for table in all_tables if table.select(".lang-fr") != []]

    charts = []
    if tables == []:
        adj_forms = html.select(".form-of.lang-fr")
        if adj_forms:
            charts.append([[adj.text for adj in adj_forms]])
    else:
        for table in tables:
            for entry_to_remove in table.find_all("span", {"class": "IPA"}):
                entry_to_remove.decompose()
            chart = []
            for tr in table.find_all("tr"):
                if tr.children is None:
                    continue
                row = []
                for child in tr.children:
                    if (child.name == "td" and child.get("colspan") != "8") or (
                        child.name == "th" and child.get("colspan") == "6"
                    ):
                        row.append(child.text.strip())
                if row != []:  # pylint: disable=use-implicit-booleaness-not-comparison
                    chart.append(row)
            charts.append(chart)

    return charts
