from json import loads, dumps

from lib.webscrape import fetch_page, parse_html


class Cache:
    def __init__(self, file_path, words):
        self.file_path = file_path

        try:
            with open(file_path) as f:
                self.cache = loads(f.read())
        except Exception:
            self.cache = {}

        self.build_cache(words)

    def __contains__(self, elem):
        return elem in self.cache

    def __len__(self):
        return len(self.cache)

    def build_cache(self, words, offline):
        for word, definition in words:
            if word not in self:
                if definition is not None:
                    self.cache[word] = {"definitions": [definition]}
                else:
                    if not offline:
                        html = fetch_page(word)
                        self.cache[word] = parse_html(html)

    def set_cache(self, word, entry):
        self.cache[word] = entry

    def get_cache(self, word):
        return self.cache.get(word, None)

    def words(self):
        return set([key for key in self.cache.keys()])

    def save_cache(self):
        with open(self.file_path, "w") as cache_file:
            cache_file.write(dumps(self.cache))
