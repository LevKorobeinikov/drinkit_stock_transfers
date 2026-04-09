class Paginator:
    def __init__(self, session, url, headers, page_size=100):
        self.session = session
        self.url = url
        self.headers = headers
        self.page_size = page_size

    def fetch_all(self, params):
        all_items = []
        skip = 0
        while True:
            params["skip"] = skip
            response = self.session.get(self.url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            items = data.get("transfers", [])
            all_items.extend(items)
            if not items or data.get("isEndOfListReached"):
                break
            skip += self.page_size
        return all_items
