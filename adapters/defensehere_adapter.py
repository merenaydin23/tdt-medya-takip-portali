from datetime import datetime
from bs4 import BeautifulSoup
from .base_adapter import BaseAdapter
from config import CATEGORIES

class DefenseHereAdapter(BaseAdapter):
    def __init__(self):
        super().__init__(
            source_id="defensehere",
            source_name="Defensehere",
            category=CATEGORIES["OTHER"]
        )

    def fetch_latest_news(self) -> list:
        rss_urls = [
            "https://www.defensehere.com/tr/rss",
            "https://www.defensehere.com/tr/feed/",
            "https://news.google.com/rss/search?q=site:defensehere.com&hl=tr&gl=TR&ceid=TR:tr"
        ]
        items = []
        for url in rss_urls:
            rss_items = self.parse_rss_feed(url, max_items=50)
            if rss_items:
                for item in rss_items:
                    item["source_name"] = "Defensehere"
                    item["source_id"] = "defensehere"
                    item["category"] = self.category
                    items.append(item)

        return items
