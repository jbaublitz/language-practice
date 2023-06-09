from json import loads, dumps

from lib.webscrape import fetch_page, parse_html


class Cache:
    def __init__(self, file_path):
        self.file_path = file_path

        try:
            with open(file_path) as f:
                self.cache = loads(f.read())
        except Exception:
            self.cache = {}

    def __contains__(self, elem):
        return elem in self.cache

    def __len__(self):
        return len(self.cache)

    def refresh_cache(self, word, static_definition):
        if static_definition is not None:
            self.cache[word] = {"definitions": [static_definition]}
        else:
            html = fetch_page(word)
            self.cache[word] = parse_html(html)

    def set_cache(self, word, entry):
        self.cache[word] = entry

    def get_cache(self, word):
        return self.cache.get(word, None)

    def save_cache(self):
        with open(self.file_path, "w") as cache_file:
            cache_file.write(dumps(self.cache))
