"""
Shared code across parsers
"""

from typing import Any


def uk_ru_tables(tables: list[Any], remove: str) -> list[list[list[str]]]:
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
        max_len = max(map(len, chart))
        for chart_line in chart:
            for _ in range(0, max_len - len(chart_line)):
                chart_line.insert(1, "")

        charts.append(chart)

    return charts
