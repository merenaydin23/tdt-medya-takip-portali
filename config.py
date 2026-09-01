import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory
BASE_DIR = Path(__file__).resolve().parent

# Load environment variables
load_dotenv(BASE_DIR / ".env")

# LLM Configuration
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://llmstat.iletisim.gov.tr/v1").rstrip("/")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen-397b")

# AI / LLM Feature Toggles
ENABLE_AI_SUMMARY = os.getenv("ENABLE_AI_SUMMARY", "False").lower() in ("true", "1", "yes")
ENABLE_LLM_STAGE2 = os.getenv("ENABLE_LLM_STAGE2", "False").lower() in ("true", "1", "yes")

# SerpApi Configuration
SERPAPI_KEY = os.getenv("SERPAPI_KEY", "")

# Web Server Configuration
PORT = int(os.getenv("PORT", 5000))
HOST = os.getenv("HOST", "127.0.0.1")
DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")

# Database Configuration
DB_PATH = BASE_DIR / "db" / "media_monitor.db"

# Schedule Configuration
SCHEDULE_TIME = os.getenv("SCHEDULE_TIME", "07:30")

# Stage 1: Extended Keywords List (Case-insensitive matching with word boundaries)
KEYWORDS_STAGE_1 = [
    # Ülke, Şehir ve Bölge İsimleri
    "azerbaycan", "azerbaycan'ın", "azerbaycan'a", "azerbaycan'da", "azerbaycan'dan", "azerbaycanlı", "azerbaycanlılar",
    "bakü", "bakü'de", "bakü'ye", "bakü'nün", "bakü'den",
    "nahçıvan", "nahçivan", "nahcivan", "nahçıvan'a", "nahçıvan'da", "naxçıvan",
    "karabağ", "dağlık karabağ", "karabağ'da", "karabağ'ın", "karabağ'a",
    "şuşa", "şuşa'da", "şuşa'ya", "şuşa beyannamesi",
    "hankendi", "hocalı", "kelbecer", "laçın", "ağdam", "cebrayıl", "Fuzuli", "zengilan", "gubadlı",
    "gence", "gəncə", "terter", "barda", "lenkeran", "mingeçevir", "şemkir",
    "zengilan havalimanı", "fuzuli havalimanı", "fuzuli kenti", "laçın koridoru",

    # Sınır & Bölgesel İller, Kapılar ve Hatlar (Iğdır, Kars, Ardahan, Dilucu, Sederek)
    "dilucu", "dilucu sınır kapısı", "sederek", "sədərək", "çıldır-aktaş", "türkgözü",
    "ığdır-nahçıvan", "kars-nahçıvan", "kars başkonsolosluğu", "azerbaycan kars başkonsolosluğu",
    "mersin-kktc", "mersin kıbrıs", "girne", "gazimağusa", "güzelyurt", "iskele",

    # Kişi ve Lider İsimleri
    "ilham aliyev", "aliyev", "aliyev'in", "aliyev'den", "mehriban aliyeva",
    "haydar aliyev", "heydar aliyev", "ceyhun bayramov", "zakir hasanov", "reşad memmedov",
    "paşinyan", "ermenistan-azerbaycan", "azerbaycan-ermenistan",
    "kassym-jomart tokayev", "tokayev", "president tokayev",
    "shavkat mirziyoyev", "mirziyoyev", "president mirziyoyev",
    "sadyr japarov", "japarov", "caparov", "sadır caparov",
    "serdar berdimuhamedow", "gurbanguly berdimuhamedow",
    "ersin tatar", "ünal üstel",

    # Kurum, İttifak ve Diplomatik Projeler
    "türk devletleri teşkilatı", "tdt", "türk konseyi", "türksoy", "turkpa", "ots",
    "türk dövlətləri təşkilatı", "türk dünyası", "türk dünyası teşkilatı",
    "zangezur", "zengezur", "zangezur koridoru", "zengezur koridoru", "zəngəzur",
    "tanap", "trans anadolu", "şahdeniz", "şah deniz", "socar", "petkim",
    "güney kafkasya", "kafkasya barış", "3+3 formatı",
    "bakü-tiflis-ceyhan", "btc boru hattı", "bakü-tiflis-kars", "btk demiryolu",
    "bir millet iki devlet", "can azerbaycan",
    "azerbaycan büyükelçiliği", "azerbaycan konsolosluğu", "azerbaycan başkonsolosluğu",
    "azerbaycan dışişleri", "azerbaycan savunma bakanlığı", "azerbaycan milli meclisi", "azerbaycan ordusu",
    "azərbaycan respublikası", "milli məclis", "xarici işlər nazirliyi", "müdafiə nazirliyi",
    "қазақстан үкіметі", "kuzey kıbrıs türk cumhuriyeti", "kktc", "kuzey kıbrıs", "kıbrıs türk",

    # Ülkeler, Kentler ve Havzalar (Farklı dillerde)
    "azerbaycan", "azerbaijan", "azərbaycan", "baku", "bakı", "bakü",
    "qarabağ", "karabağ", "şuşa", "laçın", "hankendi", "xankəndi", "ağdam", "hocalı",
    "naxçıvan", "nahçıvan", "türk-azerbaycan", "azerbaycan-türkiye",
    "kazakistan", "kazakhstan", "қазақстан", "astana", "almaty", "almatı", "nursultan",
    "özbekistan", "uzbekistan", "o‘zbekistan", "taşkent", "tashkent",
    "kırgızistan", "kyrgyzstan", "кыргызстан", "bişkek", "bishkek",
    "türkmenistan", "turkmenistan", "aşgabat", "ashgabat",
    "lefkoşa", "nicosia", "kıbrıs", "cyprus", "northern cyprus", "doğu akdeniz",

    # Önemli Bölgesel Koridorlar, Yatırımlar ve Şirketler
    "orta koridor", "middle corridor", "trans-hazar", "trans-caspian",
    "hazar denizi", "hazar gölü", "tengiz", "kashagan", "kazmunaygas",
    "semerkant", "silk road", "ipek yolu", "manas üniversitesi", "türk-kırgız",
    "türkmen gazı", "turkmen gas", "aktau", "kuryk",

    # Kısa kodlar — Stage1 kelime sınırlı; tek başlarına zayıf sayılır
    "tap", "tdt", "btc",
]

# Stage 2: Relevant Context Topics (for fallback to LLM classification)
STAGE2_CONTEXT_TOPICS = [
    "dış politika", "dışişleri", "diplomasi", "savunma", "enerji", "doğalgaz", "boru hattı",
    "kafkasya", "orta asya", "türk dünyası", "ermenistan", "gürcistan", "iran", "hazar denizi", "kıbrıs"
]

# Source Categories
CATEGORIES = {
    "RESMI": "Resmi / Ana Akım",
    "IKTIDAR": "İktidar Yanlısı",
    "MUHALIF": "Muhalif",
    "YEREL": "Yerel / Bölgesel Basın",
    "OTHER": "Diğer / Sınıflandırılmamış"
}

# 20+ News Sources Metadata
SOURCES_CONFIG = [
    # 1. Resmi / Ana Akım
    {"id": "aa", "name": "Anadolu Ajansı (AA)", "category": CATEGORIES["RESMI"], "type": "scrape", "domain": "aa.com.tr"},
    {"id": "trt", "name": "TRT Haber", "category": CATEGORIES["RESMI"], "type": "rss/scrape", "domain": "trthaber.com"},
    {"id": "iha", "name": "İhlas Haber Ajansı (İHA)", "category": CATEGORIES["RESMI"], "type": "scrape", "domain": "iha.com.tr"},
    {"id": "dha", "name": "DHA | Demirören Haber Ajansı", "category": CATEGORIES["RESMI"], "type": "rss/scrape", "domain": "dha.com.tr"},
    {"id": "ntv", "name": "NTV Haber", "category": CATEGORIES["RESMI"], "type": "rss/scrape", "domain": "ntv.com.tr"},
    {"id": "haberturk", "name": "Habertürk", "category": CATEGORIES["RESMI"], "type": "rss/scrape", "domain": "haberturk.com"},
    {"id": "milliyet", "name": "Milliyet", "category": CATEGORIES["RESMI"], "type": "rss", "domain": "milliyet.com.tr"},
    {"id": "hurriyet", "name": "Hürriyet", "category": CATEGORIES["RESMI"], "type": "rss/scrape", "domain": "hurriyet.com.tr"},

    # 2. İktidar Yanlısı
    {"id": "ahaber", "name": "A Haber", "category": CATEGORIES["IKTIDAR"], "type": "rss/scrape", "domain": "ahaber.com.tr"},
    {"id": "yenisafak", "name": "Yeni Şafak", "category": CATEGORIES["IKTIDAR"], "type": "rss/scrape", "domain": "yenisafak.com"},
    {"id": "sabah", "name": "Sabah", "category": CATEGORIES["IKTIDAR"], "type": "rss", "domain": "sabah.com.tr"},
    {"id": "turkiyegazetesi", "name": "Türkiye Gazetesi", "category": CATEGORIES["IKTIDAR"], "type": "rss/scrape", "domain": "turkiyegazetesi.com.tr"},
    {"id": "yeniakit", "name": "Yeni Akit", "category": CATEGORIES["IKTIDAR"], "type": "rss/scrape", "domain": "yeniakit.com.tr"},
    {"id": "benguturk", "name": "Bengütürk TV", "category": CATEGORIES["IKTIDAR"], "type": "rss/scrape", "domain": "benguturk.com"},

    # 3. Muhalif
    {"id": "sozcu", "name": "Sözcü", "category": CATEGORIES["MUHALIF"], "type": "rss/scrape", "domain": "sozcu.com.tr"},
    {"id": "cumhuriyet", "name": "Cumhuriyet", "category": CATEGORIES["MUHALIF"], "type": "rss", "domain": "cumhuriyet.com.tr"},
    {"id": "halktv", "name": "Halk TV", "category": CATEGORIES["MUHALIF"], "type": "rss/scrape", "domain": "halktv.com.tr"},
    {"id": "t24", "name": "T24", "category": CATEGORIES["MUHALIF"], "type": "rss", "domain": "t24.com.tr"},
    {"id": "birgun", "name": "BirGün", "category": CATEGORIES["MUHALIF"], "type": "rss/scrape", "domain": "birgun.net"},

    # 4. Sınır, Yerel ve Bölgesel Basın
    {"id": "regional_border", "name": "Sınır & Kafkas Basını (Iğdır/Kars/Ardahan/Ağrı)", "category": CATEGORIES["YEREL"], "type": "rss/scrape", "domain": "kha.com.tr"},
    {"id": "mediterranean_local", "name": "Akdeniz Bölge Basını (Mersin/Adana/Hatay/Antalya)", "category": CATEGORIES["YEREL"], "type": "rss/scrape", "domain": "mersinhaber.com"},
    {"id": "anatolian_local", "name": "Anadolu İlleri Yerel Basını", "category": CATEGORIES["YEREL"], "type": "rss/scrape", "domain": "olay.com.tr"}
]
