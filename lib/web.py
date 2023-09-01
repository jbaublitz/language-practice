from bs4 import BeautifulSoup
from requests import get


class Page:
    url = "https://en.wiktionary.org/wiki/"

    def _fetch(self, word):
        try:
            html = get(Page.url + word.replace("\u0301", ""), timeout=5)
            if html.status_code == 404:
                return None
            self.html = BeautifulSoup(html.text, "html.parser")

            all_tables = self.html.find_all("table", {"class": "inflection-table"})
            if all_tables == []:
                return None
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
            return charts
        except Exception as err:
            raise RuntimeError(f"Error fetching word {word}") from err

    def __init__(self, word):
        self.charts = self._fetch(word)

    def show_charts(self):
        return self.charts
