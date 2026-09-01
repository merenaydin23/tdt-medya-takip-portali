from datetime import datetime
from bs4 import BeautifulSoup
from .base_adapter import BaseAdapter
from config import CATEGORIES

class YeniAkitAdapter(BaseAdapter):
    def __init__(self):
        super().__init__(
            source_id="yeniakit",
            source_name="Yeni Akit",
            category=CATEGORIES["IKTIDAR"]
        )

    def fetch_latest_news(self) -> list:
        items = []
        seen_links = set()

        # 1. Native RSS Feeds + Google News verified mirror
        rss_urls = [
            "https://www.yeniakit.com.tr/rss/haber/gundem",
            "https://www.yeniakit.com.tr/rss/haber/dunya",
            "https://www.yeniakit.com.tr/rss/haber/siyaset",
            "https://www.yeniakit.com.tr/rss/haber/ekonomi",
            "https://news.google.com/rss/search?q=site:yeniakit.com.tr&hl=tr&gl=TR&ceid=TR:tr"
        ]

        for url in rss_urls:
            rss_items = self.parse_rss_feed(url, max_items=40)
            if rss_items:
                for item in rss_items:
                    link = item.get("link", "")
                    if link and link not in seen_links:
                        seen_links.add(link)
                        # Clean title suffix
                        if " - Yeni Akit" in item["title"]:
                            item["title"] = item["title"].replace(" - Yeni Akit", "").strip()
                        item["source_name"] = "Yeni Akit"
                        item["source_id"] = "yeniakit"
                        item["category"] = self.category
                        items.append(item)

        # 2. Direct HTML Fallback Web Scraping
        scrape_urls = [
            "https://www.yeniakit.com.tr/gundem",
            "https://www.yeniakit.com.tr/dunya"
        ]

        for url in scrape_urls:
            html = self.fetch_url(url)
            if not html:
                continue
            soup = BeautifulSoup(html, "html.parser")
            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"]
                if "/haber/" in href and any(c in href for c in ["/gundem/", "/dunya/", "/siyaset/"]):
                    if not href.startswith("http"):
                        href = "https://www.yeniakit.com.tr" + href
                    
                    if href in seen_links:
                        continue

                    title = self.clean_text(a_tag.get_text())
                    if len(title) < 20 or any(skip in title.lower() for skip in ["foto galeri", "video"]):
                        continue

                    seen_links.add(href)
                    items.append({
                        "source_id": "yeniakit",
                        "source_name": "Yeni Akit",
                        "category": self.category,
                        "title": title,
                        "summary": "",
                        "author": "Yeni Akit",
                        "publish_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "link": href,
                        "veri_kaynagi": "Scraping"
                    })

        return items[:60]
