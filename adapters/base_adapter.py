import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from datetime import datetime
import re

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

# Global high-performance HTTP session with connection pooling
_SESSION = requests.Session()
_retries = Retry(total=1, backoff_factor=0.2, status_forcelist=[500, 502, 503, 504])
_adapter = HTTPAdapter(pool_connections=100, pool_maxsize=100, max_retries=_retries)
_SESSION.mount('http://', _adapter)
def is_junk_title(title: str) -> bool:
    if not title:
        return True
    # Normalize whitespace
    title_clean = re.sub(r'\s+', ' ', str(title)).strip()
    # Strip leading dates/times
    title_clean = re.sub(r'^\d{1,2}\s+[A-ZÇĞİÖŞÜa-zçğıöşü]+\s+\d{4}\s*\d{0,2}[:.]?\d{0,2}\s*[-–—]?\s*', '', title_clean)
    title_clean = re.sub(r'^\d{1,2}[:.]\d{2}(:\d{2})?\s*[-–—]?\s*', '', title_clean).strip()
    
    # Real news headlines must have at least 20 characters and at least 4 words
    words = [w for w in title_clean.split() if len(w) > 1]
    if len(title_clean) < 20 or len(words) < 4:
        return True
        
    title_lower = title_clean.lower()
    
    # Navigation / Category / UI Junk patterns
    junk_patterns = [
        "sayfa /", "sayfa 1", "sayfa 2", "foto galeri", "video galeri", "videolar",
        "yazarlarımız", "çerez politikası", "gizlilik politikası", "künye", "kunye",
        "kurumsal", "bize ulaşın", "iletişim", "site haritası", "whatsapp ihbar",
        "taziye ilanları", "vefat edenler", "nöbetçi eczane", "nobetci eczane",
        "sayısal loto", "süper loto", "on numara", "şans topu", "milli piyango",
        "çekiliş sonuçları", "bilet sorgulama", "günlük burç", "burç yorumları"
    ]
    if any(jp in title_lower for jp in junk_patterns):
        return True

    # Category / Menu titles that are not actual news headlines
    generic_categories = [
        "haberleri", "tüm haberler", "tum haberler", "son dakika haberleri",
        "manşet haberleri", "manset haberleri", "gündem haberleri", "asayiş haberleri",
        "ekonomi haberleri", "spor haberleri", "dünya haberleri", "yerel haberler",
        "kars haberleri", "ığdır haberleri", "ardahan haberleri", "mersin haberleri"
    ]
    if title_lower in generic_categories or (len(words) <= 4 and any(title_lower.endswith(gc) for gc in generic_categories)):
        return True

    if re.match(r'^(\d+\s+[A-Za-zÇĞİÖŞÜçğıöşü]+\s+\d{4}|\d+[\s.-]+\d+[\s.-]+\d+|\d{1,2}[:.]\d{2})+$', title_clean):
        return True

    return False

class BaseAdapter:
    def __init__(self, source_id: str, source_name: str, category: str):
        self.source_id = source_id
        self.source_name = source_name
        self.category = category
        self.logger = logging.getLogger(f"Adapter.{source_id}")
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://www.google.com/"
        }

    def fetch_url(self, url: str, timeout: float = 3.5) -> str:
        try:
            response = _SESSION.get(url, headers=self.headers, timeout=timeout)
            if response.status_code == 200:
                response.encoding = response.apparent_encoding or "utf-8"
                return response.text
            else:
                return ""
        except Exception as e:
            return ""

    def clean_text(self, text: str) -> str:
        if not text:
            return ""
        # Remove HTML tags if present
        text = re.sub(r'<[^>]+>', ' ', text)
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def extract_date_from_card(self, card) -> str:
        """Extracts publication date/time from HTML card elements or fallback to current date."""
        if not card:
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Check time/meta tags
        time_tag = card.find("time") or card.find("span", class_=re.compile(r"date|time|saat|tarih", re.I))
        if time_tag:
            dt_attr = time_tag.get("datetime") or time_tag.get("content") or time_tag.get_text()
            if dt_attr:
                dt_str = self.clean_text(dt_attr)
                m_time = re.search(r"\b([0-2]?\d[:.][0-5]\d)\b", dt_str)
                if m_time:
                    time_part = m_time.group(1).replace(".", ":")
                    if len(time_part.split(":")[0]) == 1:
                        time_part = "0" + time_part
                    today = datetime.now().strftime("%Y-%m-%d")
                    return f"{today} {time_part}:00"

        # Search anywhere in card text for HH:MM time pattern
        card_text = card.get_text()
        m_time = re.search(r"\b([0-2]?\d[:.][0-5]\d)\b", card_text)
        if m_time:
            time_part = m_time.group(1).replace(".", ":")
            if len(time_part.split(":")[0]) == 1:
                time_part = "0" + time_part
            today = datetime.now().strftime("%Y-%m-%d")
            return f"{today} {time_part}:00"

    def canonicalize_url(self, url: str) -> str:
        if not url:
            return ""
        try:
            import urllib.parse
            parsed = urllib.parse.urlparse(url)
            clean_query = []
            if parsed.query:
                for pair in parsed.query.split("&"):
                    if "=" in pair:
                        k, v = pair.split("=", 1)
                        if not any(t in k.lower() for t in ("utm", "amp", "ref", "rss", "fbclid", "gclid")):
                            clean_query.append(pair)
            new_query = "&".join(clean_query)
            path = parsed.path.rstrip("/")
            clean_url = urllib.parse.urlunparse((parsed.scheme, parsed.netloc.lower(), path, parsed.params, new_query, ""))
            return clean_url
        except:
            return url

    def is_junk_title(self, title: str) -> bool:
        return is_junk_title(title)

    def extract_explicit_date_from_title(self, title: str) -> str:
        if not title:
            return None
        import html
        t_clean = html.unescape(title)
        month_map = {
            "ocak": "01", "şubat": "02", "mart": "03", "nisan": "04", "mayıs": "05", "haziran": "06",
            "temmuz": "07", "ağustos": "08", "agustos": "08", "eylül": "09", "ekim": "10", "kasım": "11", "aralık": "12"
        }
        m = re.search(r'\b([0-3]?\d)\s+(Ocak|Şubat|Mart|Nisan|Mayıs|Haziran|Temmuz|Ağustos|Agustos|Eylül|Ekim|Kasım|Aralık)\s*(\d{4})?\b', t_clean, re.I)
        if m:
            day = int(m.group(1))
            month_str = m.group(2).lower()
            year = m.group(3) or datetime.now().strftime("%Y")
            month = month_map.get(month_str, "08")
            if 1 <= day <= 31:
                dt_str = f"{year}-{month}-{day:02d} 12:00:00"
                try:
                    dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
                    if dt <= datetime.now():
                        return dt_str
                except:
                    pass
        return None

    def parse_rss_feed(self, rss_url: str, max_items: int = 100) -> list:
        items = []
        xml_content = self.fetch_url(rss_url)
        if not xml_content:
            return items

        try:
            soup = BeautifulSoup(xml_content, "xml")
            entries = soup.find_all("item") or soup.find_all("entry")
            
            for entry in entries[:max_items]:
                title = ""
                link = ""
                summary = ""
                pub_date = ""
                author = ""

                # Title
                title_tag = entry.find("title")
                if title_tag:
                    title = self.clean_text(title_tag.get_text())
                    if " - " in title and len(title.rsplit(" - ", 1)[0].strip()) > 10:
                        title = title.rsplit(" - ", 1)[0].strip()

                # Link
                link_tag = entry.find("link")
                if link_tag:
                    link = link_tag.get_text() if link_tag.get_text() else link_tag.get("href", "")
                    link = link.strip()

                # Summary / Description
                desc_tag = entry.find("description") or entry.find("summary") or entry.find("content:encoded")
                if desc_tag:
                    summary = self.clean_text(desc_tag.get_text())

                # Author
                author_tag = entry.find("author") or entry.find("dc:creator")
                if author_tag:
                    author = self.clean_text(author_tag.get_text())

                # Pub Date (Parses RFC 822, ISO 8601, Atom, and custom formats)
                import email.utils
                pub_date_tag = entry.find("pubDate") or entry.find("published") or entry.find("dc:date") or entry.find("updated")
                if pub_date_tag:
                    raw_pub_date = self.clean_text(pub_date_tag.get_text())
                    dt_obj = None
                    try:
                        parsed_tuple = email.utils.parsedate_tz(raw_pub_date)
                        if parsed_tuple:
                            dt_obj = datetime.fromtimestamp(email.utils.mktime_tz(parsed_tuple))
                    except:
                        pass

                    if not dt_obj:
                        try:
                            clean_iso = raw_pub_date.split(".")[0].replace("Z", "")
                            dt_obj = datetime.fromisoformat(clean_iso)
                        except:
                            pass

                    if not dt_obj:
                        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%d.%m.%Y %H:%M:%S", "%d.%m.%Y %H:%M", "%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S GMT"):
                            try:
                                dt_obj = datetime.strptime(raw_pub_date, fmt)
                                break
                            except:
                                pass

                explicit_date = self.extract_explicit_date_from_title(title)
                if explicit_date:
                    pub_date = explicit_date
                elif dt_obj:
                    pub_date = dt_obj.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    pub_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                if title and link and not self.is_junk_title(title):
                    items.append({
                        "source_id": self.source_id,
                        "source_name": self.source_name,
                        "category": self.category,
                        "title": title,
                        "summary": summary,
                        "author": author,
                        "publish_date": pub_date,
                        "link": self.canonicalize_url(link),
                        "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
        except Exception as e:
            self.logger.error(f"Error parsing RSS feed from {rss_url}: {e}")

        return items

    def fetch_latest_news(self) -> list:
        """Subclasses should implement this method."""
        raise NotImplementedError("Each adapter must implement fetch_latest_news()")


def parse_date_string(date_str: str) -> datetime:
    if not date_str:
        return None
    # Remove timezone suffix like +03:00 or Z
    date_str = date_str.split(".")[0]  # remove milliseconds if any
    date_str = re.sub(r'([+-]\d{2}):?(\d{2})$', '', date_str) # remove timezone offset
    date_str = date_str.replace("Z", "").replace("T", " ").strip()
    
    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%dT%H:%M:%S",
        "%d.%m.%Y %H:%M:%S",
        "%d.%m.%Y %H:%M",
        "%Y/%m/%d %H:%M:%S"
    ):
        try:
            return datetime.strptime(date_str, fmt)
        except:
            pass
    return None


def extract_turkish_date_from_text(text: str) -> datetime:
    if not text:
        return None
    month_map = {
        "ocak": 1, "şubat": 2, "subat": 2, "mart": 3, "nisan": 4, "mayıs": 5, "mayis": 5, "haziran": 6,
        "temmuz": 7, "ağustos": 8, "agustos": 8, "eylül": 9, "eylul": 9, "ekim": 10, "kasım": 11, "kasim": 11, "aralık": 12, "aralik": 12
    }
    # Pattern 1: 31 Ağustos 2026 22:12 or 31 Ağustos 2026
    m = re.search(r'\b([0-3]?\d)\s+(Ocak|Şubat|Subat|Mart|Nisan|Mayıs|Mayis|Haziran|Temmuz|Ağustos|Agustos|Eylül|Eylul|Ekim|Kasım|Kasim|Aralık|Aralik)\s+(\d{4})(?:\s+([0-2]?\d)[:.]([0-5]\d))?\b', text, re.IGNORECASE)
    if m:
        day = int(m.group(1))
        month = month_map.get(m.group(2).lower(), 1)
        year = int(m.group(3))
        hour = int(m.group(4)) if m.group(4) else 12
        minute = int(m.group(5)) if m.group(5) else 0
        try:
            return datetime(year, month, day, hour, minute)
        except:
            pass

    # Pattern 2: 31.08.2026 22:12 or 31/08/2026 or 31-08-2026
    m2 = re.search(r'\b([0-3]?\d)[./-]([0-1]?\d)[./-](\d{4})(?:\s+([0-2]?\d)[:.]([0-5]\d))?\b', text)
    if m2:
        day = int(m2.group(1))
        month = int(m2.group(2))
        year = int(m2.group(3))
        hour = int(m2.group(4)) if m2.group(4) else 12
        minute = int(m2.group(5)) if m2.group(5) else 0
        try:
            return datetime(year, month, day, hour, minute)
        except:
            pass
    return None

def extract_pub_date_from_html(soup: BeautifulSoup) -> str:
    # 1. Check article:published_time and standard metas
    meta_pub = (
        soup.find("meta", property="article:published_time") or
        soup.find("meta", attrs={"name": "article:published_time"}) or
        soup.find("meta", attrs={"name": "datePublished"}) or
        soup.find("meta", attrs={"name": "datepublished"}) or
        soup.find("meta", attrs={"itemprop": "datePublished"}) or
        soup.find("meta", property="og:published_time") or
        soup.find("meta", attrs={"name": "publish-date"}) or
        soup.find("meta", attrs={"name": "publication_date"}) or
        soup.find("meta", attrs={"name": "release-date"}) or
        soup.find("meta", property="og:release_date")
    )
    if meta_pub and meta_pub.get("content"):
        date_str = meta_pub.get("content").strip()
        parsed_dt = parse_date_string(date_str)
        if parsed_dt:
            return parsed_dt.strftime("%Y-%m-%d %H:%M:%S")

    # 2. Check application/ld+json for datePublished
    import json
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string)
            if isinstance(data, dict):
                dt_str = data.get("datePublished") or data.get("dateCreated")
                if not dt_str and "@graph" in data:
                    for graph_item in data["@graph"]:
                        dt_str = graph_item.get("datePublished") or graph_item.get("dateCreated")
                        if dt_str:
                            break
                if dt_str:
                    parsed_dt = parse_date_string(dt_str)
                    if parsed_dt:
                        return parsed_dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            pass

    # 3. Check time tags with datetime attribute
    for time_tag in soup.find_all("time"):
        dt_str = time_tag.get("datetime")
        if dt_str:
            parsed_dt = parse_date_string(dt_str)
            if parsed_dt:
                return parsed_dt.strftime("%Y-%m-%d %H:%M:%S")
        # Also check inner text of time tag
        t_text = time_tag.get_text()
        parsed_t = extract_turkish_date_from_text(t_text)
        if parsed_t:
            return parsed_t.strftime("%Y-%m-%d %H:%M:%S")

    # 4. Check date classes in local newspapers (e.g. .date, .tarih, .news-date, .published)
    for selector in [".date", ".tarih", ".news-date", ".post-date", ".entry-date", ".haber-tarih", ".time", ".info-date", ".detay-tarih"]:
        for el in soup.select(selector):
            parsed_t = extract_turkish_date_from_text(el.get_text())
            if parsed_t:
                return parsed_t.strftime("%Y-%m-%d %H:%M:%S")

    # 5. Check first 1000 characters of whole body text for Turkish date pattern
    body_el = soup.find("body")
    if body_el:
        lead_text = body_el.get_text()[:1500]
        parsed_t = extract_turkish_date_from_text(lead_text)
        if parsed_t:
            return parsed_t.strftime("%Y-%m-%d %H:%M:%S")

    return None


def scrape_article_text(url: str, timeout: float = 2.5) -> dict:
    """
    Fetches the HTML of the given article URL and extracts the main body text and publication date.
    Cleans up boilerplate content like scripts, style sheets, and headers.
    Returns a dict with 'text' and 'publish_date'.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://www.google.com/"
    }
    result = {"text": "", "publish_date": None}
    try:
        response = _SESSION.get(url, headers=headers, timeout=timeout)
        if response.status_code == 200:
            response.encoding = response.apparent_encoding or "utf-8"
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Extract publication date before decomposing elements
            result["publish_date"] = extract_pub_date_from_html(soup)
            
            # Remove scripts, styles, and other non-content tags
            for tag in soup(["script", "style", "nav", "header", "footer", "aside", "noscript", "iframe"]):
                tag.decompose()
                
            # Common article body container selectors
            article_body = soup.find("article") or soup.find(class_=re.compile(r"article-body|article-content|news-content|story-body|post-content|entry-content|detay-icerik|news-detail|detay_icerik", re.I))
            
            target = article_body if article_body else soup
            paragraphs = target.find_all("p")
            
            text_blocks = []
            for p in paragraphs:
                txt = p.get_text().strip()
                if not txt:
                    continue
                # Skip typical cookie consents, newsletter subscriptions, or social share widgets
                if len(txt) < 35 and any(kw in txt.lower() for kw in ["çerez", "cookie", "takip et", "abone ol", "paylaş", "yorum yap", "tıklayın", "okumak için", "kabul ediyorum", "daha fazla"]):
                    continue
                text_blocks.append(txt)
                
            full_text = " ".join(text_blocks).strip()
            # Normalize multiple spaces
            full_text = re.sub(r'\s+', ' ', full_text)
            if len(full_text) > 100:
                result["text"] = full_text
    except Exception as e:
        logging.getLogger("ArticleScraper").error(f"Error scraping full article text from {url}: {e}")
    return result

