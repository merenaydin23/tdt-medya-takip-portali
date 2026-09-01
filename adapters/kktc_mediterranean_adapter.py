import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
from .base_adapter import BaseAdapter
from config import CATEGORIES

logger = logging.getLogger("Adapter.MediterraneanLocal")

class MediterraneanLocalAdapter(BaseAdapter):
    """
    Dedicated crawler for Turkey's Mediterranean Regional Media:
    - Mersin: Mersin Haber, Mersin Portal, Güney Gazetesi, Akdeniz Postası, Çukurova Expres
    - Adana: Çukurova Barış, Adana Haber, Bölge Gazetesi
    - Hatay / İskenderun: Antakya Gazetesi, İskenderun Ses
    - Antalya: Antalya Körfez, Akdeniz Manşet
    """
    def __init__(self):
        super().__init__(
            source_id="mediterranean_local",
            source_name="Akdeniz Bölge Basını (Mersin/Adana/Antalya/Hatay)",
            category=CATEGORIES.get("YEREL", CATEGORIES["OTHER"])
        )

        self.outlets = [
            # Mersin
            {"id": "mersinhaber", "name": "Mersin Haber", "domain": "mersinhaber.com", "scrape_url": "https://www.mersinhaber.com", "city": "Mersin"},
            {"id": "mersinportal", "name": "Mersin Portal", "domain": "mersinportal.com", "scrape_url": "https://www.mersinportal.com", "city": "Mersin"},
            {"id": "guneygazetesi", "name": "Güney Gazetesi", "domain": "guneygazetesi.com", "scrape_url": "https://guneygazetesi.com", "city": "Mersin"},
            {"id": "akdenizpostasi", "name": "Akdeniz Postası", "domain": "akdenizpostasi.com.tr", "scrape_url": "https://akdenizpostasi.com.tr", "city": "Mersin"},
            
            # Adana
            {"id": "cukurovabaris", "name": "Çukurova Barış", "domain": "cukurovabaris.com.tr", "scrape_url": "https://www.cukurovabaris.com.tr", "city": "Adana"},
            {"id": "bolgegazetesi", "name": "Bölge Gazetesi", "domain": "bolgegazetesi.com.tr", "scrape_url": "https://bolgegazetesi.com.tr", "city": "Adana"},

            # Hatay / İskenderun
            {"id": "antakyagazetesi", "name": "Antakya Gazetesi", "domain": "antakyagazetesi.com", "scrape_url": "https://antakyagazetesi.com", "city": "Hatay"},
            {"id": "iskenderunses", "name": "İskenderun Ses", "domain": "sesgazetesi-hatay.com", "scrape_url": "https://sesgazetesi-hatay.com", "city": "İskenderun"},

            # Antalya
            {"id": "antalyakorfez", "name": "Antalya Körfez", "domain": "korfezgazetesi.com", "scrape_url": "https://korfezgazetesi.com", "city": "Antalya"}
        ]

        # Türkiye Akdeniz liman, lojistik ve bölgesel arama sorguları
        self.regional_queries = [
            ("Mersin Limanı lojistik", "Mersin / Lojistik"),
            ("Mersin deniz ticaret", "Mersin / Ticaret"),
            ("Adana sanayi ihracat", "Adana / Ekonomi"),
            ("Hatay İskenderun liman", "Hatay / Liman"),
            ("Mersin Azerbaycan", "Mersin / Dış İlişkiler")
        ]

    def _fetch_outlet_news(self, outlet: dict) -> list:
        items = []
        seen_links = set()

        # 1. Google News verified RSS mirror for outlet domain
        gn_url = f"https://news.google.com/rss/search?q=site:{outlet['domain']}&hl=tr&gl=TR&ceid=TR:tr"
        try:
            rss_items = self.parse_rss_feed(gn_url, max_items=25)
            for it in rss_items:
                link = it.get("link", "")
                if link and link not in seen_links:
                    seen_links.add(link)
                    title = it.get("title", "").split(" - ")[0].strip()
                    it["title"] = title
                    it["source_name"] = f"{outlet['name']} ({outlet['city']})"
                    it["source_id"] = outlet["id"]
                    it["category"] = self.category
                    it["veri_kaynagi"] = "RSS"
                    items.append(it)
        except Exception as e:
            logger.debug(f"RSS error for {outlet['name']}: {e}")

        # 2. Direct HTML scraping
        try:
            html = self.fetch_url(outlet["scrape_url"])
            if html:
                soup = BeautifulSoup(html, "html.parser")
                for a in soup.find_all("a", href=True):
                    href = a["href"]
                    title = self.clean_text(a.get_text())

                    if len(title) < 20 or any(s in title.lower() for s in ["foto galeri", "video", "reklam", "resmi ilandır", "nöbetçi", "vefat", "künye", "iletişim"]):
                        continue

                    if href.startswith("/"):
                        href = outlet["scrape_url"].rstrip("/") + href

                    if href.startswith("http") and href not in seen_links:
                        seen_links.add(href)
                        items.append({
                            "source_id": outlet["id"],
                            "source_name": f"{outlet['name']} ({outlet['city']})",
                            "category": self.category,
                            "title": title,
                            "summary": "",
                            "author": outlet["name"],
                            "publish_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "link": href,
                            "veri_kaynagi": "Scraping"
                        })
        except Exception as e:
            logger.debug(f"Direct scrape error for {outlet['name']}: {e}")

        return items[:30]

    def _fetch_query_news(self, query_tuple: tuple) -> list:
        query, label = query_tuple
        items = []
        import urllib.parse
        encoded_q = urllib.parse.quote(f'"{query}"')
        gn_url = f"https://news.google.com/rss/search?q={encoded_q}&hl=tr&gl=TR&ceid=TR:tr"
        try:
            rss_items = self.parse_rss_feed(gn_url, max_items=20)
            for it in rss_items:
                raw_title = it.get("title", "")
                parts = raw_title.split(" - ")
                title = parts[0].strip()
                source = parts[1].strip() if len(parts) > 1 else f"Akdeniz Basını ({label})"
                it["title"] = title
                it["source_name"] = f"{source} ({label})"
                it["source_id"] = "med_local_query"
                it["category"] = self.category
                it["veri_kaynagi"] = "RSS"
                items.append(it)
        except Exception as e:
            logger.debug(f"Query search error for {query}: {e}")
        return items

    def fetch_latest_news(self) -> list:
        all_items = []
        with ThreadPoolExecutor(max_workers=12) as executor:
            outlets_results = executor.map(self._fetch_outlet_news, self.outlets)
            query_results = executor.map(self._fetch_query_news, self.regional_queries)

            for outlet_items in outlets_results:
                all_items.extend(outlet_items)
            for q_items in query_results:
                all_items.extend(q_items)

        logger.info(f"MediterraneanLocalAdapter fetched {len(all_items)} articles across {len(self.outlets)} Turkey Mediterranean outlets.")
        return all_items
