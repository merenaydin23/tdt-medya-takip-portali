import logging
from datetime import datetime
from bs4 import BeautifulSoup
from .base_adapter import BaseAdapter
from config import CATEGORIES

logger = logging.getLogger("Adapter.BloombergHT")

class BloombergHTAdapter(BaseAdapter):
    def __init__(self):
        super().__init__(
            source_id="bloomberght",
            source_name="Bloomberg HT",
            category=CATEGORIES["RESMI"]
        )

    def fetch_latest_news(self) -> list:
        items = []
        seen_links = set()

        # 1. Native RSS Feeds & Google News live backup
        rss_urls = [
            "https://www.bloomberght.com/rss",
            "https://news.google.com/rss/search?q=site:bloomberght.com&hl=tr&gl=TR&ceid=TR:tr"
        ]
        for url in rss_urls:
            try:
                rss_items = self.parse_rss_feed(url, max_items=60)
                for item in rss_items:
                    link = item.get("link", "")
                    if link and link not in seen_links:
                        seen_links.add(link)
                        item["source_id"] = self.source_id
                        item["source_name"] = self.source_name
                        item["category"] = self.category
                        items.append(item)
            except Exception as e:
                logger.warning(f"Error fetching Bloomberg HT RSS ({url}): {e}")

        # 2. Comprehensive Direct Web Scraping: Ekonomi, Piyasalar & Enerji
        scrape_urls = [
            "https://www.bloomberght.com/ekonomi",
            "https://www.bloomberght.com/piyasalar",
            "https://www.bloomberght.com/enerji"
        ]
        for url in scrape_urls:
            html = self.fetch_url(url)
            if not html:
                continue
            soup = BeautifulSoup(html, "html.parser")
            cards = soup.select("article, .news-item, .card, a[href*='/haber/'], a[href*='/ekonomi/'], a[href*='/piyasalar/'], a[href*='/enerji/']")
            for card in cards[:30]:
                link_tag = card if card.name == "a" else card.find("a")
                if not link_tag or not link_tag.get("href"):
                    continue
                link = link_tag.get("href")
                if not link.startswith("http"):
                    link = "https://www.bloomberght.com" + link

                if link in seen_links:
                    continue

                title_tag = card.find(["h2", "h3", "h4", "strong", "span"]) or link_tag
                title = self.clean_text(title_tag.get_text()) if title_tag else ""
                
                desc_tag = card.find("p") or card.find(".desc")
                summary = self.clean_text(desc_tag.get_text()) if desc_tag else ""

                if title and len(title) > 15:
                    seen_links.add(link)
                    items.append({
                        "source_id": self.source_id,
                        "source_name": self.source_name,
                        "category": self.category,
                        "title": title,
                        "summary": summary,
                        "author": "Bloomberg HT",
                        "publish_date": self.extract_date_from_card(card) or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "link": link,
                        "veri_kaynagi": "Scraping"
                    })
        return items[:70]
