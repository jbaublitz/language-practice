"""
Parsing for Russian language grammar charts.
"""


def parse(html):
    """
    Parse HTML returned from web request for a Russian word.
    """
    cache = {}

    all_tables = html.find_all("table", {"class": "inflection-table"})
    tables = [table for table in all_tables if table.select(".lang-ru") != []]

    charts = []
    for table in tables:
        for entry_to_remove in table.find_all("span", {"lang": "ru-Latn"}):
            entry_to_remove.decompose()
        chart = [
            [entry.text.strip() for entry in tr.find_all("td")]
            for tr in table.find_all("tr")
            if [entry.text.strip() for entry in tr.find_all("td")] != []
        ]
        max_len = max(len(line) for line in chart)
        for line in chart:
            len_of_line = len(line)
            for i in range(max_len - len_of_line):
                line.insert(1 + i, "")
        charts.append(chart)
    if charts:
        cache["charts"] = charts

    comparative = html.find_all("b", {"class": "comparative-form-of"})
    if comparative:
        cache["comparative"] = [comp.text for comp in comparative]

    superlative = html.find_all("b", {"class": "superlative-form-of"})
    if superlative:
        cache["superlative"] = [sup.text for sup in superlative]

    return cache
