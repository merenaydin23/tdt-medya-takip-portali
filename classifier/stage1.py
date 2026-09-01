import re
from config import KEYWORDS_STAGE_1, STAGE2_CONTEXT_TOPICS

# Short / ambiguous tokens that must match as whole words only
WEAK_KEYWORDS = {"tap", "btc"}

# Strong keywords: direct Azerbaijan markers (substring OK only with word boundaries)
def _compile_kw(kw: str):
    # Use Unicode-aware word-ish boundaries: not letter/digit on either side
    k_lower = kw.lower()
    if k_lower in ("bakı", "barda", "gence", "laçın", "laçin"):
        # Match strictly capitalized versions of proper nouns that collide with:
        # - 'bakı' -> 'Baki' (Turkish name/word) or 'bakı açısı' typos
        # - 'barda' -> 'barda' (in the bar) locative noun in Turkish
        # - 'gence' -> 'gence' (to the young person) dative noun in Turkish
        # - 'laçın'/'laçin' -> 'laçin' (common noun meaning falcon/brave or name)
        # Proper nouns for cities/regions are always capitalized in professional news.
        cap_kw = kw[0].upper() + kw[1:]
        return re.compile(rf"(?<![\wçğıöşüÇĞİÖŞÜ]){cap_kw}(?![\wçğıöşüÇĞİÖŞÜ])")
    return re.compile(rf"(?<![\wçğıöşüÇĞİÖŞÜ]){re.escape(kw)}(?![\wçğıöşüÇĞİÖŞÜ])", re.IGNORECASE)

STAGE1_PATTERNS = [(_compile_kw(kw), kw) for kw in KEYWORDS_STAGE_1]
STAGE2_CONTEXT_PATTERNS = [(_compile_kw(topic), topic) for topic in STAGE2_CONTEXT_TOPICS]

# Aspect keyword groups (word-boundary safe)
ASPECT_ARMENIA = ["ermenistan", "paşinyan", "zangezur", "zengezur", "laçın", "hankendi", "hocalı", "sınır komisyonu", "barış anlaşması", "üçlü bildiri"]
ASPECT_SECURITY = ["şuşa beyannamesi", "savunma", "askeri", "tatbikat", "ordu", "mayın temizleme", "güvenlik", "savunma bakanlığı", "zakir hasanov", "silahlı kuvvetler"]
ASPECT_ENERGY = ["tanap", "tap", "petkim", "socar", "boru hattı", "enerji", "şahdeniz", "şah deniz", "btc", "doğalgaz", "petrol", "gaz", "ticaret", "yatırım", "ekonomi"]
ASPECT_TURKIC = ["türk devletleri teşkilatı", "tdt", "türk konverse", "türk konseyi", "türksoy", "turkpa", "orta asya", "türk dünyası"]
ASPECT_DIPLOMACY = ["diplomasi", "siyaset", "büyükelçi", "büyükelçilik", "başkonsolosluk", "konsolos", "ziyaret", "görüşme", "zirve", "dışişleri", "ceyhun bayramov", "reşad memmedov", "milli meclis"]
ASPECT_BORDER = ["dilucu", "sederek", "sədərək", "çıldır-aktaş", "türkgözü", "kars başkonsolosluğu", "azerbaycan kars başkonsolosluğu", "ığdır-nahçıvan", "kars-nahçıvan", "dilucu sınır kapısı"]
ASPECT_SPORTS = [
    "futbol", "futbolcu", "maç", "maçı", "maçlar", "maçları", "gol", "şampiyonlar ligi", "devler ligi", "avrupa ligi",
    "konferans ligi", "karabağ fk", "sabah fk", "neftçi", "spor", "skoru", "maç özeti", "stadyum", "şampiyona", "puan durumu",
    "maçın", "karşılaşma", "rakibi", "fikstür", "play-off", "kulübü", "transfer", "teknik direktör", "şampiyon", "şampiyonluk"
]

# Diğer Türk Devletleri
ASPECT_KAZAKHSTAN = [
    "kazakistan", "kazakistan'ın", "kazakistan'a", "kazakistan'da", "kazakistan'dan", 
    "kazakhstan", "қазақстан", "astana", "almaty", "almatı", "nursultan", 
    "kassym-jomart tokayev", "tokayev", "tokaev", "president tokayev", "қазақстан үкіметі",
    "middle corridor", "trans-caspian", "aktau", "kuryk", "çin-kazakistan", "avrupa-kazakistan",
    "tengiz", "kashagan", "kazmunaygas", "kazakistan-türkiye", "kazakistan-azerbaycan"
]
ASPECT_KYRGYZSTAN = [
    "kırgızistan", "kırgızistan'ın", "kırgızistan'a", "kırgızistan'da", "kırgızistan'dan",
    "kyrgyzstan", "кыргызстан", "bişkek", "bishkek", "sadyr japarov", "japarov", "caparov", "sadır caparov",
    "türkiye-kırgızistan", "kazakistan-kırgızistan", "özbekistan-kırgızistan", "issyk-kul", "issık göl",
    "manas üniversitesi", "türk-kırgız"
]
ASPECT_UZBEKISTAN = [
    "özbekistan", "özbekistan'ın", "özbekistan'a", "özbekistan'da", "özbekistan'dan",
    "uzbekistan", "o‘zbekistan", "taşkent", "tashkent", "shavkat mirziyoyev", "mirziyoyev", "president mirziyoyev",
    "türkiye-özbekistan", "azerbaycan-özbekistan", "kazakistan-özbekistan", "semerkant", "silk road", "ipek yolu"
]
ASPECT_TURKMENISTAN = [
    "türkmenistan", "türkmenistan'ın", "türkmenistan'a", "türkmenistan'da", "türkmenistan'dan",
    "turkmenistan", "aşgabat", "ashgabat", "serdar berdimuhamedow", "gurbanguly berdimuhamedow", "berdimuhamedov",
    "türkmen gazı", "turkmen gas", "trans-caspian", "türkiye-türkmenistan", "azerbaycan-türkmenistan", 
    "kazakistan-türkmenistan", "iran-türkmenistan"
]
ASPECT_KKTC = [
    "kuzey kıbrıs türk cumhuriyeti", "kktc", "kuzey kıbrıs", "kıbrıs türk", "lefkoşa", "ersin tatar", "ünal üstel",
    "northern cyprus", "turkish republic of northern cyprus", "nicosia", "türkiye-kktc", "azerbaycan-kktc",
    "doğu akdeniz", "kıbrıs", "cyprus", "mersin-kktc", "girne", "gazimağusa"
]

ASPECT_ARMENIA_PATTERNS = [_compile_kw(k) for k in ASPECT_ARMENIA]
ASPECT_SECURITY_PATTERNS = [_compile_kw(k) for k in ASPECT_SECURITY]
ASPECT_ENERGY_PATTERNS = [_compile_kw(k) for k in ASPECT_ENERGY]
ASPECT_TURKIC_PATTERNS = [_compile_kw(k) for k in ASPECT_TURKIC]
ASPECT_DIPLOMACY_PATTERNS = [_compile_kw(k) for k in ASPECT_DIPLOMACY]
ASPECT_BORDER_PATTERNS = [_compile_kw(k) for k in ASPECT_BORDER]
ASPECT_SPORTS_PATTERNS = [_compile_kw(k) for k in ASPECT_SPORTS]

ASPECT_KAZAKHSTAN_PATTERNS = [_compile_kw(k) for k in ASPECT_KAZAKHSTAN]
ASPECT_KYRGYZSTAN_PATTERNS = [_compile_kw(k) for k in ASPECT_KYRGYZSTAN]
ASPECT_UZBEKISTAN_PATTERNS = [_compile_kw(k) for k in ASPECT_UZBEKISTAN]
ASPECT_TURKMENISTAN_PATTERNS = [_compile_kw(k) for k in ASPECT_TURKMENISTAN]
ASPECT_KKTC_PATTERNS = [_compile_kw(k) for k in ASPECT_KKTC]

# Place-name false friends & Turkish homonym phrases (Turkish localities / common nouns ≠ Azerbaijan)
FALSE_FRIEND_PATTERNS = [
    _compile_kw("karabağlar"),  # İzmir Karabağlar ilçesi
    _compile_kw("karabağ mahallesi"),
    _compile_kw("karabağ caddesi"),
    _compile_kw("karabağ sokak"),
    _compile_kw("karabağ köyü"),

    # Turkish noun case homonym phrases ("genç-e" / young person ≠ Gence city)
    re.compile(r"\b(?:yerdeki|talihsiz|yaralı|genç|kavga|şiddet|video|haber)\s+gence\b", re.IGNORECASE),
    re.compile(r"\bgence\s+(?:saldırdı|tekmeler|bağırdı|vurdu|dehşet|dayak|kavga)\b", re.IGNORECASE),

    # Turkish noun case homonym phrases ("bar-da" / in the bar ≠ Barda city)
    re.compile(r"\bbarda\s+(?:kavga|dehşet|olay|cinayet|silahlı|eğlenen|tartışma)\b", re.IGNORECASE),
]


def turkish_lower(s: str) -> str:
    if not s:
        return ""
    return s.replace("İ", "i").replace("I", "ı").replace("Ə", "ə").lower()


def check_stage1_relevance(title: str, summary: str) -> dict:
    """
    Stage 1: Fast keyword matching with word boundaries (no substring false positives).
    """
    text = f"{title or ''} {summary or ''}"

    # Filter out Turkish locality false friends (e.g. İzmir Karabağlar)
    text_for_match = text
    for fp in FALSE_FRIEND_PATTERNS:
        if fp.search(text_for_match):
            text_for_match = fp.sub(" ", text_for_match)

    matched_keywords = []
    for pattern, kw in STAGE1_PATTERNS:
        if pattern.search(text_for_match):
            matched_keywords.append(kw)

    if matched_keywords:
        # If ONLY weak keywords matched, send to Stage 2 for verification
        strong = [k for k in matched_keywords if k.lower() not in WEAK_KEYWORDS]
        if not strong:
            return {
                "is_relevant": False,
                "stage": None,
                "is_candidate_for_stage2": True,
                "matched_keywords": matched_keywords[:5],
                "explanation": f"Zayıf anahtar kelime (LLM doğrulaması gerekli): {', '.join(matched_keywords[:3])}"
            }

        # Fine-grained Aspect Detection
        aspects = []
        if any(p.search(text_for_match) for p in ASPECT_KAZAKHSTAN_PATTERNS):
            aspects.append("Kazakistan")
        if any(p.search(text_for_match) for p in ASPECT_KYRGYZSTAN_PATTERNS):
            aspects.append("Kırgızistan")
        if any(p.search(text_for_match) for p in ASPECT_UZBEKISTAN_PATTERNS):
            aspects.append("Özbekistan")
        if any(p.search(text_for_match) for p in ASPECT_TURKMENISTAN_PATTERNS):
            aspects.append("Türkmenistan")
        if any(p.search(text_for_match) for p in ASPECT_KKTC_PATTERNS):
            aspects.append("KKTC")

        # Check if Azerbaijan is also in the text (either by name or strong local keywords)
        is_az_related = any(turkish_lower(k) in ("azerbaycan", "aliyev", "baku", "bakü") for k in matched_keywords) or any(
            x in turkish_lower(text_for_match) for x in ["azerbaycan", "aliyev", "bakü", "baku", "gence", "səfirliyi", "büyükelçiliği"]
        )

        if aspects:
            # If it relates to both Azerbaijan and other country(ies)
            if is_az_related:
                aspects.insert(0, "Azerbaycan")
            aspect = ", ".join(aspects)
        else:
            # Check other categories if no other specific countries matched
            if any(p.search(text_for_match) for p in ASPECT_ARMENIA_PATTERNS) or any(k in ("ermenistan-azerbaycan", "azerbaycan-ermenistan", "paşinyan", "karabağ", "dağlık karabağ", "zangezur", "zengezur") for k in matched_keywords):
                aspect = "Ermenistan Hattı"
            elif any(p.search(text_for_match) for p in ASPECT_SPORTS_PATTERNS):
                aspect = "Spor"
            elif any(p.search(text_for_match) for p in ASPECT_SECURITY_PATTERNS):
                aspect = "Güvenlik/Savunma"
            elif any(p.search(text_for_match) for p in ASPECT_ENERGY_PATTERNS):
                aspect = "Enerji/Ekonomi"
            elif any(p.search(text_for_match) for p in ASPECT_TURKIC_PATTERNS):
                aspect = "Türk Devletleri/Bölgesel"
            elif any(p.search(text_for_match) for p in ASPECT_BORDER_PATTERNS):
                aspect = "Sınır Hattı & Bölgesel Diplomasi"
            elif any(p.search(text_for_match) for p in ASPECT_DIPLOMACY_PATTERNS):
                aspect = "Diplomasi & Siyaset"
            else:
                aspect = "Diplomasi & Siyaset"

        return {
            "is_relevant": True,
            "stage": "Stage 1 (Anahtar Kelime)",
            "aspect": aspect,
            "matched_keywords": matched_keywords[:5],
            "explanation": f"Metinde doğrudan anahtar kelime eşleşmesi bulundu: {', '.join(matched_keywords[:3])}"
        }

    is_candidate_for_stage2 = any(p.search(text) for p, _ in STAGE2_CONTEXT_PATTERNS)

    return {
        "is_relevant": False,
        "stage": None,
        "is_candidate_for_stage2": is_candidate_for_stage2,
        "matched_keywords": [],
        "explanation": ""
    }
