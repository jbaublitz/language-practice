"""
Parsing for French language grammar charts.
"""


def parse(html):
    """
    Parse HTML returned from web request for a French word.
    """
    cache = {}

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
    if charts:
        cache["charts"] = charts

    adj_forms = html.select(".form-of.lang-fr")
    if adj_forms:
        cache["adjective_forms"] = [adj.text for adj in adj_forms]

    return cache
