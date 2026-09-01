import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
from .base_adapter import BaseAdapter
from config import CATEGORIES

logger = logging.getLogger("Adapter.AnatolianLocal")

class AnatolianLocalAdapter(BaseAdapter):
    """
    Dedicated crawler for Anatolian Provincial Media:
    - Marmara: Bursa (Olay, Bursa Hakimiyet), Kocaeli (Özgür Kocaeli)
    - Aegean: İzmir (Ege'de Sonsöz, İz Gazete), Denizli
    - Black Sea: Trabzon (61saat, Günebakış, Taka), Samsun (Hedef Halk)
    - Central Anatolia: Konya (Pusula, Yeni Meram), Kayseri (Kayseri Olay), Eskişehir
    - Southeastern / Eastern: Gaziantep (Gaziantep Pusula), Diyarbakır (Güneydoğu Güncel)
    """
    def __init__(self):
        super().__init__(
            source_id="anatolian_local",
            source_name="Anadolu Yerel Basını",
            category=CATEGORIES.get("YEREL", CATEGORIES["OTHER"])
        )

        self.outlets = [
            # Bursa
            {"id": "olaygazetesi", "name": "Olay Gazetesi", "domain": "olay.com.tr", "scrape_url": "https://www.olay.com.tr", "city": "Bursa"},
            {"id": "bursahakimiyet", "name": "Bursa Hakimiyet", "domain": "bursahakimiyet.com.tr", "scrape_url": "https://www.bursahakimiyet.com.tr", "city": "Bursa"},
            
            # Trabzon & Karadeniz
            {"id": "61saat", "name": "61saat", "domain": "61saat.com", "scrape_url": "https://www.61saat.com", "city": "Trabzon"},
            {"id": "gunebakis", "name": "Günebakış", "domain": "gunebakis.com.tr", "scrape_url": "https://www.gunebakis.com.tr", "city": "Trabzon"},

            # İzmir & Ege
            {"id": "egedesonsoz", "name": "Ege'de Sonsöz", "domain": "egedesonsoz.com", "scrape_url": "https://www.egedesonsoz.com", "city": "İzmir"},
            {"id": "izgazete", "name": "İz Gazete", "domain": "izgazete.net", "scrape_url": "https://www.izgazete.net", "city": "İzmir"},

            # Konya & İç Anadolu
            {"id": "pusulahaber", "name": "Pusula Haber", "domain": "pusulahaber.com.tr", "scrape_url": "https://www.pusulahaber.com.tr", "city": "Konya"},
            {"id": "kayseriolay", "name": "Kayseri Olay", "domain": "kayseriolay.com", "scrape_url": "https://www.kayseriolay.com", "city": "Kayseri"},

            # Samsun
            {"id": "hedefhalk", "name": "Hedef Halk", "domain": "hedefhalk.com", "scrape_url": "https://www.hedefhalk.com", "city": "Samsun"},

            # Gaziantep & Güneydoğu
            {"id": "gazianteppusula", "name": "Gaziantep Pusula", "domain": "gazianteppusula.com", "scrape_url": "https://www.gazianteppusula.com", "city": "Gaziantep"},
            {"id": "ozgurkocaeli", "name": "Özgür Kocaeli", "domain": "ozgurkocaeli.com.tr", "scrape_url": "https://www.ozgurkocaeli.com.tr", "city": "Kocaeli"}
        ]

        # Strategic thematic queries to discover Azerbaijan / Turkic / Cyprus news in all 81 provinces' local newspapers
        self.thematic_queries = [
            ("Yerel Basın Azerbaycan", "Anadolu / Azerbaycan"),
            ("Yerel Gazete Karabağ", "Anadolu / Karabağ"),
            ("Yerel Basın KKTC", "Anadolu / KKTC"),
            ("Belediye Azerbaycan Kardeş Şehir", "Belediye / Kardeş Şehir"),
            ("Türk Dünyası yerel haber", "Yerel / Türk Dünyası"),
            ("Orta Koridor lojistik yerel", "Bölgesel / Lojistik")
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

    def _fetch_thematic_news(self, query_tuple: tuple) -> list:
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
                source = parts[1].strip() if len(parts) > 1 else f"Anadolu Basını ({label})"
                it["title"] = title
                it["source_name"] = f"{source} ({label})"
                it["source_id"] = "anatolian_query"
                it["category"] = self.category
                it["veri_kaynagi"] = "RSS"
                items.append(it)
        except Exception as e:
            logger.debug(f"Thematic query error for {query}: {e}")
        return items

    def fetch_latest_news(self) -> list:
        all_items = []
        with ThreadPoolExecutor(max_workers=14) as executor:
            outlets_results = executor.map(self._fetch_outlet_news, self.outlets)
            query_results = executor.map(self._fetch_thematic_news, self.thematic_queries)

            for outlet_items in outlets_results:
                all_items.extend(outlet_items)
            for q_items in query_results:
                all_items.extend(q_items)

        logger.info(f"AnatolianLocalAdapter fetched {len(all_items)} articles across {len(self.outlets)} outlets and {len(self.thematic_queries)} queries.")
        return all_items
