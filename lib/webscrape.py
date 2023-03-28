from requests.api import get
from bs4 import BeautifulSoup
from tabulate import tabulate


def fetch_page(word):
    response = get(f"https://en.openrussian.org/ru/{word}")
    if response.status_code != 200:
        raise RuntimeError(f"Page for {word} could not be fetched")
    else:
        return BeautifulSoup(response.text, "html.parser")


def parse_html(page):
    cache = {}

    cache["word_with_stress"] = page.find("div", {"class": "bare"}).text

    overview_html = page.find("div", {"class": "overview"})
    overview = (
        [p for p in overview_html.find_all("p")[:-1]]
        if overview_html is not None
        else []
    )
    overview_filtered = []
    for overview_entry in overview:
        overview_filtered.append(overview_entry.text)
    if overview_filtered != []:
        cache["overview"] = overview_filtered

    definitions = [
        p.text
        for content in page.find("div", {"class": "translations"}).find_all(
            "div", {"class": "content"}
        )
        for p in content.find_all("p")
    ]
    cache["definitions"] = definitions

    usage_info_html = page.find("div", {"class": "usage"})
    usage_info = (
        [
            p.text
            for p in usage_info_html.find("div", {"class": "content"}).find_all("p")
        ]
        if usage_info_html is not None
        else []
    )
    if usage_info != []:
        cache["usage_info"] = usage_info

    tables = []
    table_html = page.find_all("table")
    for html in table_html:
        headers_html = [
            [child for child in row.children] for row in html.find_all("tr")
        ]

        headers = []
        for header_list_html in headers_html:
            header_list = []
            for header_html in header_list_html:
                for elem in header_html.find_all("span", {"class": "short"}):
                    elem.clear()
                if len(header_html.find_all("p")) == 0:
                    header_list.append(header_html.text)
                else:
                    header_list.append(
                        ", ".join([child.text for child in header_html.find_all("p")])
                    )
            headers.append(header_list)

        table = tabulate(headers)
        tables.append(table)
    if tables != []:
        cache["tables"] = tables

    return cache
