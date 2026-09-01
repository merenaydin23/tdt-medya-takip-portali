from datetime import datetime
from bs4 import BeautifulSoup
from .base_adapter import BaseAdapter, is_junk_title
from config import CATEGORIES

class YeniSafakAdapter(BaseAdapter):
    def __init__(self):
        super().__init__(
            source_id="yenisafak",
            source_name="Yeni Şafak",
            category=CATEGORIES["IKTIDAR"]
        )

    def fetch_latest_news(self) -> list:
        rss_urls = [
            "https://www.yenisafak.com/rss?xml=gundem",
            "https://www.yenisafak.com/rss?xml=dunya",
            "https://www.yenisafak.com/rss?xml=politika",
            "https://www.yenisafak.com/rss?xml=ekonomi",
            "https://www.yenisafak.com/rss?xml=spor",
            "https://news.google.com/rss/search?q=site:yenisafak.com&hl=tr&gl=TR&ceid=TR:tr"
        ]
        items = []
        seen_links = set()
        for url in rss_urls:
            try:
                rss_items = self.parse_rss_feed(url, max_items=100)
                for it in rss_items:
                    link = it.get("link", "")
                    title = it.get("title", "")
                    if " - Yeni Şafak" in title:
                        title = title.replace(" - Yeni Şafak", "").strip()
                        it["title"] = title

                    if is_junk_title(title):
                        continue

                    if link and link not in seen_links:
                        seen_links.add(link)
                        it["source_id"] = self.source_id
                        it["source_name"] = self.source_name
                        it["category"] = self.category
                        items.append(it)
            except Exception as e:
                self.logger.debug(f"Yeni Şafak RSS error ({url}): {e}")

        # Combine with Category Scraping
        scrape_urls = ["https://www.yenisafak.com/gundem", "https://www.yenisafak.com/dunya"]
        for url in scrape_urls:
            try:
                html = self.fetch_url(url)
                if not html:
                    continue
                soup = BeautifulSoup(html, "html.parser")
                cards = soup.select(".card, .news-item, a[href*='/gundem/'], a[href*='/dunya/']")
                for card in cards[:30]:
                    link_tag = card if card.name == "a" else card.find("a")
                    if not link_tag or not link_tag.get("href"):
                        continue
                    link = link_tag.get("href")
                    if not link.startswith("http"):
                        link = "https://www.yenisafak.com" + link

                    if link in seen_links:
                        continue

                    title_tag = card.find(["h2", "h3", "h4", "span", "p"]) or link_tag
                    title = self.clean_text(title_tag.get_text()) if title_tag else ""
                    if " - Yeni Şafak" in title:
                        title = title.replace(" - Yeni Şafak", "").strip()
                    if is_junk_title(title):
                        continue

                    if title and len(title) > 10:
                        seen_links.add(link)
                        items.append({
                            "source_id": self.source_id,
                            "source_name": self.source_name,
                            "category": self.category,
                            "title": title,
                            "summary": "",
                            "author": "Yeni Şafak",
                            "publish_date": self.extract_date_from_card(card),
                            "link": link,
                            "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })
            except Exception as e:
                self.logger.debug(f"Yeni Şafak scrape error ({url}): {e}")

        return items
