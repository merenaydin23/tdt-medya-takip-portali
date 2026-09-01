import sqlite3
import re

def clean_title(t):
    if not t:
        return ""
    # Remove leading time like "14:24 - "
    t = re.sub(r'^[0-2]?\d[:.][0-5]\d\s*[-–—:]?\s*', '', t)
    # Remove source suffixes like " - Haberler", " - Sözcü", " | TRT Haber"
    t = re.sub(r'\s*[-–—|]\s*(?:Haberler|Sözcü|Halk TV|TRT Haber|Yeni Şafak|Cumhuriyet|A Haber|NTV|DHA|İHA|Bengü Türk|Bengütürk).*$', '', t, flags=re.I)
    # Normalize alphanumeric characters
    return "".join(ch for ch in t.lower() if ch.isalnum())

def purge_duplicates():
    conn = sqlite3.connect("db/media_monitor.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, source_name, title, link, publish_date, ilgili_mi, veri_kaynagi 
        FROM news 
        ORDER BY id ASC
    """)
    rows = cursor.fetchall()
    
    seen = {}
    ids_to_delete = []

    for row in rows:
        n_id, source_name, title, link, pub_date, ilgili_mi, veri_kaynagi = row
        dt_day = (pub_date or "")[:10]
        norm_t = clean_title(title)
        
        # Deduplication key: within the SAME source and SAME date
        key = (source_name, dt_day, norm_t) if norm_t else (source_name, dt_day, link)

        if key in seen:
            prev_id, prev_link, prev_ilgili = seen[key]
            # If current item has a direct link (not news.google.com) and prev was google news, delete prev instead
            if "news.google.com" in prev_link and "news.google.com" not in (link or ""):
                ids_to_delete.append(prev_id)
                seen[key] = (n_id, link, ilgili_mi)
            elif prev_ilgili == 0 and ilgili_mi == 1:
                ids_to_delete.append(prev_id)
                seen[key] = (n_id, link, ilgili_mi)
            else:
                ids_to_delete.append(n_id)
        else:
            seen[key] = (n_id, link, ilgili_mi)

    print(f"Total duplicate records identified: {len(ids_to_delete)}")
    
    if ids_to_delete:
        cursor.executemany("DELETE FROM news WHERE id = ?", [(i,) for i in ids_to_delete])
        conn.commit()
        print(f"Successfully purged {len(ids_to_delete)} duplicate articles from database!")

    cursor.execute("SELECT COUNT(*) FROM news WHERE publish_date LIKE '2026-09-01%'")
    today_total = cursor.fetchone()[0]
    print(f"Remaining clean unique articles for today: {today_total}")

    conn.close()

if __name__ == "__main__":
    purge_duplicates()
