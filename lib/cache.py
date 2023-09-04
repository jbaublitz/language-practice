"""
Handles caching for web scraped data.
"""
import json
from json.decoder import JSONDecodeError


class Cache:
    """
    Cache for web scraped data.
    """

    def __init__(self, cache_path):
        self.cache_path = cache_path
        try:
            with open(cache_path, "r", encoding="utf-8") as file_handle:
                self.cache = json.loads(file_handle.read())
        except IOError:
            self.cache = {}
        except JSONDecodeError:
            self.cache = {}

    def __contains__(self, value):
        return value in self.cache

    def __setitem__(self, key, value):
        self.cache[key] = value

    def __getitem__(self, key):
        return self.cache[key]

    def save(self):
        """
        Save cache.
        """
        with open(self.cache_path, "w", encoding="utf-8") as file_handle:
            file_handle.write(json.dumps(self.cache))
