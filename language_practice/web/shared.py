"""
Shared code across parsers
"""


def uk_ru_tables(cache, tables, remove):
    """
    Shared code between Russian and Ukrainian table parsing.
    """
    charts = []
    for table in tables:
        for entry_to_remove in table.find_all("span", {"lang": remove}):
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
