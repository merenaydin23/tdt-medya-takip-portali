from datetime import datetime
from bs4 import BeautifulSoup
from .base_adapter import BaseAdapter, is_junk_title
from config import CATEGORIES

class DHAAdapter(BaseAdapter):
    def __init__(self):
        super().__init__(
            source_id="dha",
            source_name="DHA | Demirören Haber Ajansı",
            category=CATEGORIES["RESMI"]
        )

    def fetch_latest_news(self) -> list:
        rss_urls = [
            "https://www.dha.com.tr/rss/sondakika.xml",
            "https://www.dha.com.tr/rss/gundem.xml",
            "https://www.dha.com.tr/rss/dunya.xml",
            "https://www.dha.com.tr/rss/ekonomi.xml",
            "https://www.dha.com.tr/rss/spor.xml",
            "https://news.google.com/rss/search?q=site:dha.com.tr&hl=tr&gl=TR&ceid=TR:tr"
        ]
        items = []
        seen_links = set()
        for url in rss_urls:
            try:
                rss_items = self.parse_rss_feed(url, max_items=100)
                for it in rss_items:
                    link = it.get("link", "")
                    title = it.get("title", "")
                    if is_junk_title(title):
                        continue
                    if link and link not in seen_links:
                        seen_links.add(link)
                        it["source_id"] = self.source_id
                        it["source_name"] = self.source_name
                        it["category"] = self.category
                        items.append(it)
            except Exception as e:
                self.logger.debug(f"DHA RSS error ({url}): {e}")

        # Combine with Category Scraping
        scrape_urls = ["https://www.dha.com.tr/gundem", "https://www.dha.com.tr/dunya", "https://www.dha.com.tr/son-dakika"]
        for url in scrape_urls:
            try:
                html = self.fetch_url(url)
                if not html:
                    continue
                soup = BeautifulSoup(html, "html.parser")
                cards = soup.select(".card, article, a[href*='dha.com.tr/'], a[href*='/haber/']")
                for card in cards[:30]:
                    link_tag = card if card.name == "a" else card.find("a")
                    if not link_tag or not link_tag.get("href"):
                        continue
                    link = link_tag.get("href")
                    if not link.startswith("http"):
                        link = "https://www.dha.com.tr" + link

                    if link in seen_links:
                        continue

                    title_tag = card.find(["h2", "h3", "h4", "strong", "span"]) or link_tag
                    title = self.clean_text(title_tag.get_text()) if title_tag else ""
                    if is_junk_title(title):
                        continue

                    desc_tag = card.find("p")
                    summary = self.clean_text(desc_tag.get_text()) if desc_tag else ""

                    if title and len(title) > 10:
                        seen_links.add(link)
                        items.append({
                            "source_id": self.source_id,
                            "source_name": self.source_name,
                            "category": self.category,
                            "title": title,
                            "summary": summary,
                            "author": "DHA",
                            "publish_date": self.extract_date_from_card(card),
                            "link": link,
                            "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })
            except Exception as e:
                self.logger.debug(f"DHA scrape error ({url}): {e}")

        return items
