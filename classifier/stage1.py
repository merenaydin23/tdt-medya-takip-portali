import re
from config import KEYWORDS_STAGE_1, STAGE2_CONTEXT_TOPICS

# Short / ambiguous tokens that must match as whole words only
WEAK_KEYWORDS = {"tap", "btc"}

# Strong keywords: direct markers (substring OK only with word boundaries)
def _compile_kw(kw: str):
    k_lower = kw.lower()
    if k_lower in ("bakı", "barda", "gence", "laçın", "laçin"):
        cap_kw = kw[0].upper() + kw[1:]
        return re.compile(rf"(?<![\wçğıöşüÇĞİÖŞÜ]){cap_kw}(?![\wçğıöşüÇĞİÖŞÜ])")
    return re.compile(rf"(?<![\wçğıöşüÇĞİÖŞÜ]){re.escape(kw)}(?![\wçğıöşüÇĞİÖŞÜ])", re.IGNORECASE)

STAGE1_PATTERNS = [(_compile_kw(kw), kw) for kw in KEYWORDS_STAGE_1]
STAGE2_CONTEXT_PATTERNS = [(_compile_kw(topic), topic) for topic in STAGE2_CONTEXT_TOPICS]

# 1. AZERBAIJAN
ASPECT_AZERBAIJAN = [
    "azerbaycan", "azerbaycan'ın", "azerbaycan'a", "azerbaycan'da", "azerbaycan'dan", "azerbaycanlı", "azerbaycanlılar",
    "azərbaycan", "azerbaijan", "ilham aliyev", "aliyev", "mehriban aliyeva", "bakü", "baku", "bakı",
    "karabağ", "qarabağ", "şuşa", "hankendi", "xankəndi", "laçın", "kelbecer", "ağdam", "hocalı", "cebrayıl",
    "fuzuli", "zengilan", "gence", "socar", "tanap", "şahdeniz", "zengezur", "zangezur", "nahçıvan", "naxçıvan",
    "dilucu", "kars başkonsolosluğu", "ceyhun bayramov", "zakir hasanov", "reşad memmedov", "azeri"
]

# 2. ARMENIA / CORRIDOR / REGIONAL PEACE
ASPECT_ARMENIA = [
    "ermenistan", "paşinyan", "zangezur", "zengezur", "laçın", "hankendi", "hocalı", "sınır komisyonu",
    "barış anlaşması", "üçlü bildiri", "ermenistan-azerbaycan", "azerbaycan-ermenistan"
]

# 3. KKTC / CYPRUS
ASPECT_KKTC = [
    "kuzey kıbrıs türk cumhuriyeti", "kktc", "kuzey kıbrıs", "kıbrıs türk", "lefkoşa", "ersin tatar", "ünal üstel",
    "northern cyprus", "turkish republic of northern cyprus", "nicosia", "türkiye-kktc", "azerbaycan-kktc",
    "girne", "gazimağusa", "güzelyurt", "iskele", "doğu akdeniz", "kıbrıs barış harekatı", "kıbrıs meselesi", "mersin-kktc"
]

# 4. KAZAKHSTAN
ASPECT_KAZAKHSTAN = [
    "kazakistan", "kazakistan'ın", "kazakistan'a", "kazakistan'da", "kazakistan'dan", 
    "kazakhstan", "қазақстан", "astana", "almaty", "almatı", "nursultan", 
    "kassym-jomart tokayev", "tokayev", "tokaev", "president tokayev", "қазақстан үкіметі",
    "aktau", "kuryk", "tengiz", "kashagan", "kazmunaygas", "kazakistan-türkiye", "kazakistan-azerbaycan"
]

# 5. KYRGYZSTAN
ASPECT_KYRGYZSTAN = [
    "kırgızistan", "kırgızistan'ın", "kırgızistan'a", "kırgızistan'da", "kırgızistan'dan",
    "kyrgyzstan", "кыргызстан", "bişkek", "bishkek", "sadyr japarov", "japarov", "caparov", "sadır caparov",
    "türkiye-kırgızistan", "kazakistan-kırgızistan", "özbekistan-kırgızistan", "issyk-kul", "issık göl",
    "manas üniversitesi", "türk-kırgız"
]

# 6. UZBEKISTAN
ASPECT_UZBEKISTAN = [
    "özbekistan", "özbekistan'ın", "özbekistan'a", "özbekistan'da", "özbekistan'dan",
    "uzbekistan", "o‘zbekistan", "taşkent", "tashkent", "shavkat mirziyoyev", "mirziyoyev", "president mirziyoyev",
    "türkiye-özbekistan", "azerbaycan-özbekistan", "kazakistan-özbekistan", "semerkant", "silk road", "ipek yolu"
]

# 7. TURKMENISTAN
ASPECT_TURKMENISTAN = [
    "türkmenistan", "türkmenistan'ın", "türkmenistan'a", "türkmenistan'da", "türkmenistan'dan",
    "turkmenistan", "aşgabat", "ashgabat", "serdar berdimuhamedow", "gurbanguly berdimuhamedow", "berdimuhamedov",
    "türkmen gazı", "turkmen gas", "trans-caspian", "türkiye-türkmenistan", "azerbaycan-türkmenistan", 
    "kazakistan-türkmenistan", "iran-türkmenistan"
]

# 8. TDT / TÜRK DÜNYASI
ASPECT_TURKIC = [
    "türk devletleri teşkilatı", "tdt", "türk konverse", "türk konseyi", "türksoy", "turkpa", "türk dünyası", "orta koridor", "middle corridor"
]

# Thematic Sub-Aspects
ASPECT_SECURITY = ["şuşa beyannamesi", "savunma", "askeri", "tatbikat", "ordu", "mayın temizleme", "güvenlik", "savunma bakanlığı", "zakir hasanov", "silahlı kuvvetler"]
ASPECT_ENERGY = ["tanap", "tap", "petkim", "socar", "boru hattı", "enerji", "şahdeniz", "şah deniz", "btc", "doğalgaz", "petrol", "gaz", "ticaret", "yatırım", "ekonomi"]
ASPECT_DIPLOMACY = ["diplomasi", "siyaset", "büyükelçi", "büyükelçilik", "başkonsolosluk", "konsolos", "ziyaret", "görüşme", "zirve", "dışişleri", "ceyhun bayramov", "reşad memmedov", "milli meclis"]
ASPECT_BORDER = ["dilucu", "sederek", "sədərək", "çıldır-aktaş", "türkgözü", "kars başkonsolosluğu", "azerbaycan kars başkonsolosluğu", "ığdır-nahçıvan", "kars-nahçıvan", "dilucu sınır kapısı"]
ASPECT_SPORTS = [
    "futbol", "futbolcu", "maç", "maçı", "maçlar", "maçları", "gol", "şampiyonlar ligi", "devler ligi", "avrupa ligi",
    "konferans ligi", "karabağ fk", "sabah fk", "neftçi", "spor", "skoru", "maç özeti", "stadyum", "şampiyona", "puan durumu",
    "maçın", "karşılaşma", "rakibi", "fikstür", "play-off", "kulübü", "transfer", "teknik direktör", "şampiyon", "şampiyonluk"
]

ASPECT_AZERBAIJAN_PATTERNS = [_compile_kw(k) for k in ASPECT_AZERBAIJAN]
ASPECT_ARMENIA_PATTERNS = [_compile_kw(k) for k in ASPECT_ARMENIA]
ASPECT_KKTC_PATTERNS = [_compile_kw(k) for k in ASPECT_KKTC]
ASPECT_KAZAKHSTAN_PATTERNS = [_compile_kw(k) for k in ASPECT_KAZAKHSTAN]
ASPECT_KYRGYZSTAN_PATTERNS = [_compile_kw(k) for k in ASPECT_KYRGYZSTAN]
ASPECT_UZBEKISTAN_PATTERNS = [_compile_kw(k) for k in ASPECT_UZBEKISTAN]
ASPECT_TURKMENISTAN_PATTERNS = [_compile_kw(k) for k in ASPECT_TURKMENISTAN]
ASPECT_TURKIC_PATTERNS = [_compile_kw(k) for k in ASPECT_TURKIC]

ASPECT_SECURITY_PATTERNS = [_compile_kw(k) for k in ASPECT_SECURITY]
ASPECT_ENERGY_PATTERNS = [_compile_kw(k) for k in ASPECT_ENERGY]
ASPECT_DIPLOMACY_PATTERNS = [_compile_kw(k) for k in ASPECT_DIPLOMACY]
ASPECT_BORDER_PATTERNS = [_compile_kw(k) for k in ASPECT_BORDER]
ASPECT_SPORTS_PATTERNS = [_compile_kw(k) for k in ASPECT_SPORTS]

# False friends
FALSE_FRIEND_PATTERNS = [
    _compile_kw("karabağlar"),  # İzmir Karabağlar ilçesi
    _compile_kw("karabağ mahallesi"),
    _compile_kw("karabağ caddesi"),
    _compile_kw("karabağ sokak"),
    _compile_kw("karabağ köyü"),
    re.compile(r"\b(?:yerdeki|talihsiz|yaralı|genç|kavga|şiddet|video|haber)\s+gence\b", re.IGNORECASE),
    re.compile(r"\bgence\s+(?:saldırdı|tekmeler|bağırdı|vurdu|dehşet|dayak|kavga)\b", re.IGNORECASE),
    re.compile(r"\bbarda\s+(?:kavga|dehşet|olay|cinayet|silahlı|eğlenen|tartışma)\b", re.IGNORECASE),
]

def turkish_lower(s: str) -> str:
    if not s:
        return ""
    return s.replace("İ", "i").replace("I", "ı").replace("Ə", "ə").lower()

def check_stage1_relevance(title: str, summary: str) -> dict:
    """
    Strict country and strategic relevance classifier.
    Operates on title and the first 350 characters of lead summary to prevent footer pollution.
    """
    title_clean = title or ""
    lead_summary = (summary or "")[:350]
    text = f"{title_clean} {lead_summary}"

    # Filter out false friends
    text_for_match = text
    for fp in FALSE_FRIEND_PATTERNS:
        if fp.search(text_for_match):
            text_for_match = fp.sub(" ", text_for_match)

    matched_keywords = []
    for pattern, kw in STAGE1_PATTERNS:
        if pattern.search(text_for_match):
            matched_keywords.append(kw)

    if not matched_keywords:
        return {
            "is_relevant": False,
            "stage": None,
            "is_candidate_for_stage2": False,
            "matched_keywords": [],
            "explanation": ""
        }

    strong = [k for k in matched_keywords if k.lower() not in WEAK_KEYWORDS]
    if not strong:
        return {
            "is_relevant": False,
            "stage": None,
            "is_candidate_for_stage2": True,
            "matched_keywords": matched_keywords[:5],
            "explanation": f"Zayıf anahtar kelime (LLM doğrulaması gerekli): {', '.join(matched_keywords[:3])}"
        }

    # 1. Check TDT / Türk Dünyası General news (Applies to all member states)
    is_tdt_general = any(p.search(text_for_match) for p in ASPECT_TURKIC_PATTERNS) or any(
        k in ("türk devletleri teşkilatı", "tdt", "türk konseyi", "türksoy", "turkpa", "türk dünyası", "orta koridor", "middle corridor") 
        for k in matched_keywords
    )

    # 2. Check each country explicitly and independently
    matched_countries = []

    has_az = any(p.search(text_for_match) for p in ASPECT_AZERBAIJAN_PATTERNS) or \
             any(p.search(text_for_match) for p in ASPECT_ARMENIA_PATTERNS) or \
             any(p.search(text_for_match) for p in ASPECT_BORDER_PATTERNS)

    has_kktc = any(p.search(text_for_match) for p in ASPECT_KKTC_PATTERNS)
    has_kz = any(p.search(text_for_match) for p in ASPECT_KAZAKHSTAN_PATTERNS)
    has_kg = any(p.search(text_for_match) for p in ASPECT_KYRGYZSTAN_PATTERNS)
    has_uz = any(p.search(text_for_match) for p in ASPECT_UZBEKISTAN_PATTERNS)
    has_tm = any(p.search(text_for_match) for p in ASPECT_TURKMENISTAN_PATTERNS)

    if has_az:
        matched_countries.append("Azerbaycan")
    if has_kktc:
        matched_countries.append("KKTC")
    if has_kz:
        matched_countries.append("Kazakistan")
    if has_kg:
        matched_countries.append("Kırgızistan")
    if has_uz:
        matched_countries.append("Özbekistan")
    if has_tm:
        matched_countries.append("Türkmenistan")

    # 3. Determine final aspect
    if is_tdt_general:
        aspect = "TDT / Türk Dünyası (Azerbaycan, Kazakistan, Kırgızistan, Özbekistan, Türkmenistan, KKTC)"
    elif len(matched_countries) > 1:
        # Multi-country news (e.g. "Azerbaycan, KKTC" or "Azerbaycan, Kazakistan") -> tagged for both/all!
        aspect = ", ".join(matched_countries)
    elif len(matched_countries) == 1:
        single_country = matched_countries[0]
        if single_country == "Azerbaycan":
            if any(p.search(text_for_match) for p in ASPECT_ARMENIA_PATTERNS):
                aspect = "Azerbaycan, Ermenistan Hattı"
            elif any(p.search(text_for_match) for p in ASPECT_BORDER_PATTERNS):
                aspect = "Azerbaycan, Sınır Hattı & Bölgesel Diplomasi"
            elif any(p.search(text_for_match) for p in ASPECT_SPORTS_PATTERNS):
                aspect = "Azerbaycan, Spor"
            elif any(p.search(text_for_match) for p in ASPECT_SECURITY_PATTERNS):
                aspect = "Azerbaycan, Güvenlik/Savunma"
            elif any(p.search(text_for_match) for p in ASPECT_ENERGY_PATTERNS):
                aspect = "Azerbaycan, Enerji/Ekonomi"
            else:
                aspect = "Azerbaycan, Diplomasi & Siyaset"
        else:
            aspect = single_country
    else:
        # None of the target countries or TDT matched
        return {
            "is_relevant": False,
            "stage": None,
            "is_candidate_for_stage2": False,
            "matched_keywords": [],
            "explanation": ""
        }

    return {
        "is_relevant": True,
        "stage": "Stage 1 (Anahtar Kelime)",
        "aspect": aspect,
        "matched_keywords": matched_keywords[:5],
        "explanation": f"Tespit edildi: {aspect}"
    }
