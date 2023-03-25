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
    word_with_stress = page.find("div", {"class": "bare"}).text

    overview_html = page.find("div", {"class": "overview"})
    overview = (
        [p for p in overview_html.find_all("p")[:-1]]
        if overview_html is not None
        else []
    )

    partner = None
    overview_filtered = []
    for overview_entry in overview:
        if "partner" in overview_entry.text:
            partner = overview_entry.text
        else:
            overview_filtered.append(overview_entry.text)

    definitions = [
        p.text
        for content in page.find("div", {"class": "translations"}).find_all(
            "div", {"class": "content"}
        )
        for p in content.find_all("p")
    ]

    usage_info_html = page.find("div", {"class": "usage"})
    usage_info = (
        [
            p.text
            for p in usage_info_html.find("div", {"class": "content"}).find_all("p")
        ]
        if usage_info_html is not None
        else []
    )

    tables = []
    table_html = page.find_all("table")
    for html in table_html:
        headers = [
            [child.text for child in row.children] for row in html.find_all("tr")
        ]
        table = tabulate(headers)
        tables.append(table)

    return (
        word_with_stress,
        overview_filtered,
        definitions,
        usage_info,
        partner,
        tables,
    )
