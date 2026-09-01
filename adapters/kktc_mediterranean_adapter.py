import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
from .base_adapter import BaseAdapter
from config import CATEGORIES

logger = logging.getLogger("Adapter.KKTC_Mediterranean")

class KKTC_MediterraneanAdapter(BaseAdapter):
    """
    Dedicated crawler for Northern Cyprus (KKTC) and Mediterranean Border/Port Media:
    - KKTC: Kıbrıs Postası, Kıbrıs Gazetesi, Haber Kıbrıs, Yenidüzen, BRTK, Gündem Kıbrıs
    - Mersin & Mediterranean: Mersin Haber, Mersin Portal, Güney Gazetesi, Çukurova Barış, Akdeniz Postası
    """
    def __init__(self):
        super().__init__(
            source_id="kktc_mediterranean",
            source_name="KKTC ve Akdeniz Basını",
            category=CATEGORIES.get("YEREL", CATEGORIES["OTHER"])
        )

        self.outlets = [
            # 1. KKTC / Kıbrıs Basını
            {"id": "kibrispostasi", "name": "Kıbrıs Postası", "domain": "kibrispostasi.com", "scrape_url": "https://www.kibrispostasi.com", "city": "Lefkoşa (KKTC)"},
            {"id": "kibrisgazetesi", "name": "Kıbrıs Gazetesi", "domain": "kibrisgazetesi.com", "scrape_url": "https://www.kibrisgazetesi.com", "city": "Lefkoşa (KKTC)"},
            {"id": "haberkibris", "name": "Haber Kıbrıs", "domain": "haberkibris.com", "scrape_url": "https://haberkibris.com", "city": "Lefkoşa (KKTC)"},
            {"id": "yeniduzen", "name": "Yenidüzen", "domain": "yeniduzen.com", "scrape_url": "https://www.yeniduzen.com", "city": "Lefkoşa (KKTC)"},
            {"id": "brtk", "name": "BRTK", "domain": "brtk.net", "scrape_url": "https://www.brtk.net", "city": "Lefkoşa (KKTC)"},
            {"id": "gundemkibris", "name": "Gündem Kıbrıs", "domain": "gundemkibris.com", "scrape_url": "https://gundemkibris.com", "city": "Lefkoşa (KKTC)"},

            # 2. Mersin & Akdeniz Bölge Basını (Kıbrıs deniz/hava kapısı ve Doğu Akdeniz merkezi)
            {"id": "mersinhaber", "name": "Mersin Haber", "domain": "mersinhaber.com", "scrape_url": "https://www.mersinhaber.com", "city": "Mersin"},
            {"id": "mersinportal", "name": "Mersin Portal", "domain": "mersinportal.com", "scrape_url": "https://www.mersinportal.com", "city": "Mersin"},
            {"id": "guneygazetesi", "name": "Güney Gazetesi", "domain": "guneygazetesi.com", "scrape_url": "https://guneygazetesi.com", "city": "Mersin"},
            {"id": "cukurovabaris", "name": "Çukurova Barış", "domain": "cukurovabaris.com.tr", "scrape_url": "https://www.cukurovabaris.com.tr", "city": "Adana / Mersin"},
            {"id": "akdenizpostasi", "name": "Akdeniz Postası", "domain": "akdenizpostasi.com.tr", "scrape_url": "https://akdenizpostasi.com.tr", "city": "Mersin"}
        ]

        # Targeted regional thematic search queries
        self.regional_queries = [
            ("Mersin KKTC", "Mersin / KKTC"),
            ("Mersin Kıbrıs", "Mersin / Kıbrıs"),
            ("KKTC Türk Devletleri", "KKTC / TDT"),
            ("Doğu Akdeniz KKTC", "Doğu Akdeniz / KKTC"),
            ("Mersin Azerbaycan", "Mersin / Azerbaycan")
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

        # 2. Direct HTML scraping on homepage
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
                source = parts[1].strip() if len(parts) > 1 else f"Yerel Basın ({label})"
                it["title"] = title
                it["source_name"] = f"{source} ({label})"
                it["source_id"] = "kktc_med_query"
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

        logger.info(f"KKTC_MediterraneanAdapter fetched {len(all_items)} articles across {len(self.outlets)} outlets and {len(self.regional_queries)} queries.")
        return all_items
