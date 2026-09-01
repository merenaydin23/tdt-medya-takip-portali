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
    - Iğdır (Direct Nakhchivan / Azerbaijan Border): Yeşil Iğdır, Iğdır Gazetesi, Iğdır Doğuş
    - Kars (Caucasus / Zengezur / BTK Hub): Kafkas Haber Ajansı, Kars Manşet, Gazete Kars, Kars Olay, Serhat TV
    - Ardahan: Ardahan Haber, Ardahan Medya
    - Ağrı: Ağrı'da Haber
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
            
            # 2. Kars (Kafkasya / Zengezur / BTK Hattı)
            {"id": "kafkashaber", "name": "Kafkas Haber Ajansı", "domain": "kha.com.tr", "scrape_url": "https://www.kha.com.tr", "city": "Kars"},
            {"id": "karsmanset", "name": "Kars Manşet", "domain": "karsmanset.com", "scrape_url": "https://www.karsmanset.com", "city": "Kars"},
            {"id": "gazetekars", "name": "Gazete Kars", "domain": "gazetekars.com", "scrape_url": "https://www.gazetekars.com", "city": "Kars"},
            {"id": "karsolay", "name": "Kars Olay", "domain": "karsolay.com", "scrape_url": "https://www.karsolay.com", "city": "Kars"},
            {"id": "serhattv", "name": "Serhat TV", "domain": "serhattv.com.tr", "scrape_url": "https://www.serhattv.com.tr", "city": "Kars"},

            # 3. Ardahan
            {"id": "ardahanhaber", "name": "Ardahan Haber", "domain": "ardahanhaber.com.tr", "scrape_url": "https://www.ardahanhaber.com.tr", "city": "Ardahan"},

            # 4. Ağrı
            {"id": "agridahaber", "name": "Ağrı'da Haber", "domain": "agridahaber.com", "scrape_url": "https://www.agridahaber.com", "city": "Ağrı"}
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
                    
                    if len(title) < 20 or any(s in title.lower() for s in ["foto galeri", "video", "reklam", "resmi ilandır", "nöbetçi"]):
                        continue

                    if href.startswith("/"):
                        href = outlet["scrape_url"] + href

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

    def fetch_latest_news(self) -> list:
        all_items = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            results = executor.map(self._fetch_outlet_news, self.outlets)
            for outlet_items in results:
                all_items.extend(outlet_items)

        logger.info(f"RegionalBorderAdapter fetched {len(all_items)} total border articles across {len(self.outlets)} local outlets.")
        return all_items
