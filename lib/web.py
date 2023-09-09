"""
Handles web scraping.
"""
import asyncio

import aiohttp
from bs4 import BeautifulSoup
from requests import get

URL = "https://en.wiktionary.org/wiki/"


def parse(html):
    """
    Parse HTML returned from web request.
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


def refresh(word):
    """
    Refresh individual cache entry.
    """
    try:
        response = get(URL + word.replace("\u0301", ""), timeout=5)
        if response.status_code == 404:
            return None
        html = BeautifulSoup(response.text, "html.parser")
        return parse(html)
    except Exception as err:
        raise RuntimeError(f"Error fetching word {word}") from err


async def fetch(session, word):
    """
    Fetch individual word asynchronously.
    """
    try:
        async with session.get(URL + word.replace("\u0301", "")) as response:
            if response.status == 404:
                return (word, None)
            text = await response.text()
            html = BeautifulSoup(text, "html.parser")
            return (word, parse(html))
    except Exception as err:
        raise RuntimeError(f"Error fetching word {word}") from err


async def scrape(words, cache):
    """
    Fetch all words asynchronously.
    """
    async with aiohttp.ClientSession() as session:
        words_not_in_cache = [word for word in words if word not in cache]
        ret = await asyncio.gather(
            *[fetch(session, word) for word in words_not_in_cache]
        )
        for word, info in ret:
            cache[word] = info
