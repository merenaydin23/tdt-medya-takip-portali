from datetime import datetime
from bs4 import BeautifulSoup
from .base_adapter import BaseAdapter, is_junk_title
from config import CATEGORIES

class BenguturkAdapter(BaseAdapter):
    def __init__(self):
        super().__init__(
            source_id="benguturk",
            source_name="Bengütürk TV",
            category=CATEGORIES["IKTIDAR"]
        )

    def fetch_latest_news(self) -> list:
        items = []
        seen_links = set()

        # 1. Official RSS Feed
        rss_urls = [
            "https://www.benguturk.com/rss",
            "https://news.google.com/rss/search?q=site:benguturk.com&hl=tr&gl=TR&ceid=TR:tr"
        ]
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
                        it["veri_kaynagi"] = "RSS"
                        items.append(it)
            except Exception as e:
                self.logger.debug(f"RSS error for Bengütürk ({url}): {e}")

        # 2. Direct HTML Category Scraping for Fresh Articles
        category_urls = [
            "https://www.benguturk.com/gundem",
            "https://www.benguturk.com/dunya",
            "https://www.benguturk.com/siyaset",
            "https://www.benguturk.com/ekonomi"
        ]
        for cat_url in category_urls:
            try:
                html = self.fetch_url(cat_url)
                if not html:
                    continue
                soup = BeautifulSoup(html, "html.parser")
                for a in soup.find_all("a", href=True):
                    href = a["href"]
                    title_elem = a.find(["h2", "h3", "h4", "div", "p"]) or a
                    title = self.clean_text(title_elem.get_text())
                    
                    for prefix in ("Gündem", "Dünya", "Siyaset", "Ekonomi", "Spor", "Haber"):
                        if title.startswith(prefix + " "):
                            title = title[len(prefix):].strip()

                    if is_junk_title(title):
                        continue

                    if href.startswith("/"):
                        href = "https://www.benguturk.com" + href

                    # Bengütürk article URLs usually end with h.htm or digits + h
                    if ("benguturk.com/" in href or href.startswith("/")) and href not in seen_links:
                        # Avoid pure category links
                        if any(c == href.rstrip("/") for c in category_urls):
                            continue
                        
                        # Check publication date from article page
                        art_pub_date = None
                        try:
                            art_res = self.fetch_url(href, timeout=2.0)
                            if art_res:
                                art_soup = BeautifulSoup(art_res, "html.parser")
                                from .base_adapter import extract_pub_date_from_html
                                art_pub_date = extract_pub_date_from_html(art_soup)
                        except:
                            pass

                        if not art_pub_date:
                            continue

                        today_prefix = datetime.now().strftime("%Y-%m-%d")
                        if not art_pub_date.startswith(today_prefix):
                            continue

                        seen_links.add(href)
                        items.append({
                            "source_id": self.source_id,
                            "source_name": self.source_name,
                            "category": self.category,
                            "title": title,
                            "summary": "",
                            "author": "Bengütürk TV",
                            "publish_date": art_pub_date,
                            "link": href,
                            "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "veri_kaynagi": "Scraping"
                        })
            except Exception as e:
                self.logger.debug(f"Direct scrape error for {cat_url}: {e}")

        return items
