"""
Handles web scraping.
"""
import asyncio

import aiohttp
from bs4 import BeautifulSoup
from requests import get

from language_practice.web import fr
from language_practice.web import ru
from language_practice.web import uk

URL = "https://en.wiktionary.org/wiki/"


def refresh(word, lang):
    """
    Refresh individual cache entry.
    """
    if lang is None:
        return {}

    try:
        response = get(URL + word.replace("\u0301", ""), timeout=5)
        if response.status_code == 404:
            return {}
        html = BeautifulSoup(response.text, "html.parser")

        if lang == "fr":
            return fr.parse(html)
        if lang == "ru":
            return ru.parse(html)
        if lang == "uk":
            return uk.parse(html)
        raise RuntimeError(
            "Reached a condition that should be unreachable; please file a bug"
        )
    except Exception as err:
        raise RuntimeError(f"Error fetching word {word}") from err


async def fetch(session, word, lang):
    """
    Fetch individual word asynchronously.
    """
    if lang is None:
        return (word, {})

    try:
        async with session.get(URL + word.replace("\u0301", "")) as response:
            if response.status == 404:
                return (word, {})
            text = await response.text()
            html = BeautifulSoup(text, "html.parser")

            if lang == "fr":
                return (word, fr.parse(html))
            if lang == "ru":
                return (word, ru.parse(html))
            if lang == "uk":
                return (word, uk.parse(html))
            raise RuntimeError(
                "Reached a condition that should be unreachable; please file a bug"
            )
    except Exception as err:
        raise RuntimeError(f"Error fetching word {word}") from err


async def scrape(words, cache, lang):
    """
    Fetch all words asynchronously.
    """
    async with aiohttp.ClientSession() as session:
        words_not_in_cache = [word for word in words if word not in cache]
        ret = await asyncio.gather(
            *[fetch(session, word, lang) for word in words_not_in_cache]
        )
        for word, info in ret:
            cache[word] = info
