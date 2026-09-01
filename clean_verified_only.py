#!/usr/bin/env python3
"""
Sets ONLY 100% genuine Azerbaijan-focused news to ilgili_mi = 1.
All other news (including other Turkic states and false friends) are set to ilgili_mi = 0.
"""
import sqlite3
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "db" / "media_monitor.db"

# Compiled regex patterns for direct Azerbaijan keywords with strict boundaries
AZ_PATTERNS = [
    re.compile(r"(?<![\wçğıöşüÇĞİÖŞÜƏə])azerbaycan(?:'?(?:ın|a|da|dan|lı|lılar))?(?![\wçğıöşüÇĞİÖŞÜƏə])", re.I),
    re.compile(r"(?<![\wçğıöşüÇĞİÖŞÜƏə])azərbaycan(?:'?(?:ın|a|da|dan|lı))?(?![\wçğıöşüÇĞİÖŞÜƏə])", re.I),
    re.compile(r"(?<![\wçğıöşüÇĞİÖŞÜƏə])azerbaijan(?![\wçğıöşüÇĞİÖŞÜƏə])", re.I),
    re.compile(r"(?<![\wçğıöşüÇĞİÖŞÜƏə])azeri(?:ler|lerden|lere)?(?![\wçğıöşüÇĞİÖŞÜƏə])", re.I),
    re.compile(r"(?<![\wçğıöşüÇĞİÖŞÜƏə])bakü(?:'?(?:de|ye|nün|den|nü))?(?![\wçğıöşüÇĞİÖŞÜƏə])", re.I),
    re.compile(r"(?<![\wçğıöşüÇĞİÖŞÜƏə])Bakı(?:'?(?:da|ya|nın|dan))?(?![\wçğıöşüÇĞİÖŞÜƏə])"),  # Strictly Capitalized Bakı
    re.compile(r"(?<![\wçğıöşüÇĞİÖŞÜƏə])ilham aliyev(?:'?(?:in|e|i|den))?(?![\wçğıöşüÇĞİÖŞÜƏə])", re.I),
    re.compile(r"(?<![\wçğıöşüÇĞİÖŞÜƏə])aliyev(?:'?(?:in|e|i|den))?(?![\wçğıöşüÇĞİÖŞÜƏə])", re.I),
    re.compile(r"(?<![\wçğıöşüÇĞİÖŞÜƏə])(?:mehriban|mihriban)\s+aliyeva(?:'?(?:nın|ya|yı))?(?![\wçğıöşüÇĞİÖŞÜƏə])", re.I),
    re.compile(r"(?<![\wçğıöşüÇĞİÖŞÜƏə])aliyeva(?:'?(?:nın|ya|yı))?(?![\wçğıöşüÇĞİÖŞÜƏə])", re.I),
    re.compile(r"(?<![\wçğıöşüÇĞİÖŞÜƏə])karabağ(?:'?(?:da|a|ın|dan|ı))?(?![\wçğıöşüÇĞİÖŞÜƏə])", re.I),
    re.compile(r"(?<![\wçğıöşüÇĞİÖŞÜƏə])qarabağ(?![\wçğıöşüÇĞİÖŞÜƏə])", re.I),
    re.compile(r"(?<![\wçğıöşüÇĞİÖŞÜƏə])şuşa(?:'?(?:da|ya|nın|dan))?(?![\wçğıöşüÇĞİÖŞÜƏə])", re.I),
    re.compile(r"(?<![\wçğıöşüÇĞİÖŞÜƏə])nahçıvan(?:'?(?:a|da|dan|ın))?(?![\wçğıöşüÇĞİÖŞÜƏə])", re.I),
    re.compile(r"(?<![\wçğıöşüÇĞİÖŞÜƏə])hankendi(?![\wçğıöşüÇĞİÖŞÜƏə])", re.I),
    re.compile(r"(?<![\wçğıöşüÇĞİÖŞÜƏə])hocalı(?![\wçğıöşüÇĞİÖŞÜƏə])", re.I),
    re.compile(r"(?<![\wçğıöşüÇĞİÖŞÜƏə])kelbecer(?![\wçğıöşüÇĞİÖŞÜƏə])", re.I),
    re.compile(r"(?<![\wçğıöşüÇĞİÖŞÜƏə])laçın(?![\wçğıöşüÇĞİÖŞÜƏə])", re.I),
    re.compile(r"(?<![\wçğıöşüÇĞİÖŞÜƏə])fuzuli(?:\s+havalimanı)?(?![\wçğıöşüÇĞİÖŞÜƏə])", re.I),
    re.compile(r"(?<![\wçğıöşüÇĞİÖŞÜƏə])zengezur(?:\s+koridoru)?(?![\wçğıöşüÇĞİÖŞÜƏə])", re.I),
    re.compile(r"(?<![\wçğıöşüÇĞİÖŞÜƏə])zangezur(?:\s+koridoru)?(?![\wçğıöşüÇĞİÖŞÜƏə])", re.I),
    re.compile(r"(?<![\wçğıöşüÇĞİÖŞÜƏə])socar(?![\wçğıöşüÇĞİÖŞÜƏə])", re.I),
    re.compile(r"(?<![\wçğıöşüÇĞİÖŞÜƏə])tanap(?![\wçğıöşüÇĞİÖŞÜƏə])", re.I),
    re.compile(r"(?<![\wçğıöşüÇĞİÖŞÜƏə])ermenistan-azerbaycan(?![\wçğıöşüÇĞİÖŞÜƏə])", re.I),
    re.compile(r"(?<![\wçğıöşüÇĞİÖŞÜƏə])azerbaycan-ermenistan(?![\wçğıöşüÇĞİÖŞÜƏə])", re.I),
    re.compile(r"(?<![\wçğıöşüÇĞİÖŞÜƏə])karabağ fk(?![\wçğıöşüÇĞİÖŞÜƏə])", re.I),
    re.compile(r"(?<![\wçğıöşüÇĞİÖŞÜƏə])sabah fk(?![\wçğıöşüÇĞİÖŞÜƏə])", re.I),
    re.compile(r"(?<![\wçğıöşüÇĞİÖŞÜƏə])neftçi(?![\wçğıöşüÇĞİÖŞÜƏə])", re.I),
]

FALSE_FRIENDS = [
    re.compile(r"\bkarabağlar\b", re.I),
    re.compile(r"\bdiyarbakır\b", re.I),
    re.compile(r"\bbakırköy\b", re.I),
]

def run():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Reset all to 0
    c.execute("UPDATE news SET ilgili_mi = 0, ilgi_kategorisi = 'İlgisiz'")

    # Select all news
    c.execute("SELECT id, title, summary, source_name FROM news")
    rows = c.fetchall()

    relevant_ids = []
    for r in rows:
        title = r["title"] or ""
        summary_lead = (r["summary"] or "")[:250]

        # Ignore false friends
        if any(fp.search(title) for fp in FALSE_FRIENDS):
            continue

        # 1. Primary: Match in Title
        title_matched = any(p.search(title) for p in AZ_PATTERNS)
        
        # 2. Secondary: Title is sports or leadership AND lead summary explicitly mentions Azerbaijan/Baku/Karabakh
        lead_matched = False
        if not title_matched and any(p.search(summary_lead) for p in AZ_PATTERNS):
            if any(k in title.lower() for k in ("sabah", "kulüp", "şampiyonlar ligi", "avrupa ligi", "liderler", "görüşme", "ziyaret", "anlaşma")):
                lead_matched = True

        if title_matched or lead_matched:
            title_lower = title.lower()
            aspect = "Diplomasi ve Dış Politika"
            if any(k in title_lower for k in ("şampiyonlar ligi", "avrupa ligi", "avrupa şampiyonası", "futbol", "karabağ fk", "sabah fk", "neftçi", "spor", "kulüp", "voleybol", "maç", "maçı", "filenin sultanları", "çeyrek final", "yarı final")):
                aspect = "Spor"
            elif any(k in title_lower for k in ("ermenistan", "paşinyan", "sınır", "barış")):
                aspect = "Ermenistan / Barış Süreci"
            elif any(k in title_lower for k in ("karabağ zaferi", "karabağ", "şuşa", "ordu", "savunma", "tatbikat", "askeri")):
                aspect = "Güvenlik ve Savunma"
            elif any(k in title_lower for k in ("socar", "tanap", "enerji", "petrol", "gaz", "ticaret", "ekonomi", "boru hattı")):
                aspect = "Enerji ve Ekonomi"
            elif any(k in title_lower for k in ("koridor", "zengezur", "zangezur", "bölgesel", "3+3", "kafkasya")):
                aspect = "Bölgesel Gelişmeler"

            relevant_ids.append((aspect, r["id"]))

    print(f"Total 100% Genuine Azerbaijan News: {len(relevant_ids)}")
    c.executemany("UPDATE news SET ilgili_mi = 1, ilgi_kategorisi = ?, relevance_status = 'Stage 1 (Kavram Tespiti)' WHERE id = ?", relevant_ids)
    conn.commit()

    c.execute("SELECT id, source_name, title, ilgi_kategorisi FROM news WHERE ilgili_mi = 1 ORDER BY id DESC")
    final_rows = c.fetchall()
    print("\n=== FINAL VERIFIED AZERBAIJAN AGENDA ===")
    for r in final_rows:
        print(f"[{r['source_name']}] {r['title']} -> {r['ilgi_kategorisi']}")

    conn.close()

if __name__ == "__main__":
    run()
