import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
from .base_adapter import BaseAdapter
from config import CATEGORIES

logger = logging.getLogger("Adapter.RegionalBorder")

class RegionalBorderAdapter(BaseAdapter):
    """
    Dedicated multi-source crawler for Eastern Border & Caucasus regional media:
    - Iğdır (Direct Nakhchivan / Azerbaijan Border): Yeşil Iğdır, Iğdır Gazetesi, Iğdır Haber, Iğdır Doğuş
    - Kars (Caucasus / Zengezur / BTK Hub): Kafkas Haber Ajansı, Kars Manşet, Gazete Kars, Kars Olay, Serhat TV
    - Ardahan: Ardahan Haber, Ardahan Medya, Çıldır Haber
    - Ağrı / Erzurum / Van: Ağrı'da Haber, Erzurum Ajans, Van Siyaseti
    """
    def __init__(self):
        super().__init__(
            source_id="regional_border",
            source_name="Yerel / Sınır Basını",
            category=CATEGORIES.get("YEREL", CATEGORIES["OTHER"])
        )

        self.outlets = [
            # 1. Iğdır (Nahçıvan / Azerbaycan Sınırı ⭐⭐⭐⭐⭐)
            {"id": "yesiligdir", "name": "Yeşil Iğdır", "domain": "yesiligdir.com", "scrape_url": "https://www.yesiligdir.com", "city": "Iğdır"},
            {"id": "igdirgazetesi", "name": "Iğdır Gazetesi", "domain": "igdirgazetesi.com", "scrape_url": "https://www.igdirgazetesi.com", "city": "Iğdır"},
            {"id": "igdirhaber", "name": "Iğdır Haber", "domain": "igdirhaber.com", "scrape_url": "https://www.igdirhaber.com", "city": "Iğdır"},
            {"id": "igdirdogus", "name": "Iğdır Doğuş", "domain": "igdirdogus.com", "scrape_url": "https://www.igdirdogus.com", "city": "Iğdır"},
            
            # 2. Kars (Kafkasya / Zengezur / BTK Hattı / Başkonsolosluk)
            {"id": "kafkashaber", "name": "Kafkas Haber Ajansı", "domain": "kha.com.tr", "scrape_url": "https://www.kha.com.tr", "city": "Kars"},
            {"id": "karsmanset", "name": "Kars Manşet", "domain": "karsmanset.com", "scrape_url": "https://www.karsmanset.com", "city": "Kars"},
            {"id": "gazetekars", "name": "Gazete Kars", "domain": "gazetekars.com", "scrape_url": "https://www.gazetekars.com", "city": "Kars"},
            {"id": "karsolay", "name": "Kars Olay", "domain": "karsolay.com", "scrape_url": "https://www.karsolay.com", "city": "Kars"},
            {"id": "serhattv", "name": "Serhat TV", "domain": "serhattv.com.tr", "scrape_url": "https://www.serhattv.com.tr", "city": "Kars"},

            # 3. Ardahan (Gürcistan / Kafkas Kapısı)
            {"id": "ardahanhaber", "name": "Ardahan Haber", "domain": "ardahanhaber.com.tr", "scrape_url": "https://www.ardahanhaber.com.tr", "city": "Ardahan"},
            {"id": "ardahanmedya", "name": "Ardahan Medya", "domain": "ardahanmedya.com", "scrape_url": "https://www.ardahanmedya.com", "city": "Ardahan"},

            # 4. Ağrı / Erzurum / Van (Doğu Anadolu Koridoru)
            {"id": "agridahaber", "name": "Ağrı'da Haber", "domain": "agridahaber.com", "scrape_url": "https://www.agridahaber.com", "city": "Ağrı"},
            {"id": "erzurumajans", "name": "Erzurum Ajans", "domain": "erzurumajans.com", "scrape_url": "https://www.erzurumajans.com", "city": "Erzurum"}
        ]

        # Targeted regional boundary & Nakhchivan/Azerbaijan queries
        self.regional_queries = [
            ("Iğdır Azerbaycan", "Iğdır / Azerbaycan"),
            ("Iğdır Nahçıvan", "Iğdır / Nahçıvan"),
            ("Iğdır Dilucu", "Iğdır / Dilucu Sınır Kapısı"),
            ("Kars Azerbaycan", "Kars / Azerbaycan"),
            ("Kars Başkonsolosluğu", "Kars / Başkonsolosluk"),
            ("Kars Nahçıvan", "Kars / Nahçıvan"),
            ("Ardahan Gürcistan Azerbaycan", "Ardahan / Kafkas"),
            ("Doğu Anadolu Zengezur", "Doğu Anadolu / Zengezur")
        ]

    def _fetch_outlet_news(self, outlet: dict) -> list:
        items = []
        seen_links = set()

        # 1. Google News verified real-time RSS mirror for the domain
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

        # 2. Direct HTML Web Scraping on portal homepage
        try:
            html = self.fetch_url(outlet["scrape_url"])
            if html:
                soup = BeautifulSoup(html, "html.parser")
                for a in soup.find_all("a", href=True):
                    href = a["href"]
                    title = self.clean_text(a.get_text())
                    
                    if len(title) < 20 or any(s in title.lower() for s in ["foto galeri", "video", "reklam", "resmi ilandır", "nöbetçi", "vefat", "künye"]):
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
                source = parts[1].strip() if len(parts) > 1 else f"Sınır Basını ({label})"
                it["title"] = title
                it["source_name"] = f"{source} ({label})"
                it["source_id"] = "border_query"
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

        logger.info(f"RegionalBorderAdapter fetched {len(all_items)} total border articles across {len(self.outlets)} outlets and {len(self.regional_queries)} queries.")
        return all_items
