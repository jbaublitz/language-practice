"""
Handles web scraping.
"""

import asyncio

import aiohttp
from bs4 import BeautifulSoup

from language_practice.config import Entry
from language_practice.web import fr, ru, uk

URL = "https://en.wiktionary.org/wiki/"


async def fetch(
    session: aiohttp.ClientSession, word: str, lang: str | None
) -> tuple[str, list[list[list[str]]]]:
    """
    Fetch individual word asynchronously.
    """
    if lang is None:
        return (word, [])

    try:
        async with session.get(URL + word.replace("\u0301", "")) as response:
            if response.status == 404:
                return (word, [])
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


async def scrape(
    words: list[Entry], lang: str | None
) -> dict[str, list[list[list[str]]]]:
    """
    Fetch all words asynchronously.
    """
    async with aiohttp.ClientSession() as session:
        ret = await asyncio.gather(
            *[fetch(session, word.get_word(), lang) for word in words]
        )
        scraped_info = {}
        for word, info in ret:
            scraped_info[word] = info

        return scraped_info
