import sqlite3
import re
from collections import defaultdict

def clean_title_words(s):
    if not s:
        return set()
    s = re.sub(r'^[0-2]?\d[:.][0-5]\d\s*[-–—:]?\s*', '', s)
    s = re.sub(r'^(?:gündem|son dakika|resmi ilan|haberler|flaş)\s*[-–—:]?\s*', '', s, flags=re.I)
    s = re.sub(r'\s*[-–—|]\s*(?:Haberler|Sözcü|Halk TV|TRT Haber|Yeni Şafak|Cumhuriyet|A Haber|NTV|DHA|İHA|Bengü Türk|Bengütürk).*$', '', s, flags=re.I)
    words = re.findall(r'[a-zA-ZğüşıöçĞÜŞİÖÇ0-9]{3,}', s.lower())
    stopwords = {"ve", "ile", "bir", "icin", "bu", "da", "de", "den", "dan", "son", "dakika", "haber", "haberi"}
    return {w for w in words if w not in stopwords}

def jaccard(s1, s2):
    if not s1 or not s2: return 0.0
    return len(s1 & s2) / len(s1 | s2)

def clean_all_history():
    conn = sqlite3.connect("db/media_monitor.db")
    c = conn.cursor()
    
    # Query ALL news across the entire database history
    c.execute("SELECT id, source_name, title, publish_date, link, ilgili_mi, ilgi_kategorisi FROM news ORDER BY id ASC")
    rows = c.fetchall()
    print(f"Total articles in DB before full historical purge: {len(rows)}")

    by_source_date = defaultdict(list)
    for r in rows:
        n_id, source_name, title, pub_date, link, ilgili, cat = r
        dt_day = (pub_date or "")[:10]
        by_source_date[(source_name, dt_day)].append(r)

    ids_to_delete = set()

    for (s_name, dt_day), group_rows in by_source_date.items():
        kept = []
        for r in group_rows:
            n_id, _, title, pub_date, link, ilgili, cat = r
            w_set = clean_title_words(title)
            
            # Skip KAP stock notifications
            if "BISTECH" in title and "KAP" in title:
                continue

            is_dup = False
            for k in list(kept):
                k_id, _, k_title, k_date, k_link, k_ilgili, k_cat = k
                k_w_set = clean_title_words(k_title)

                sim = jaccard(w_set, k_w_set)
                
                # Check exact normalized title or high similarity
                is_near_dup = (sim >= 0.60)
                if not is_near_dup and (w_set.issubset(k_w_set) or k_w_set.issubset(w_set)) and min(len(w_set), len(k_w_set)) >= 3:
                    is_near_dup = True

                if is_near_dup:
                    is_dup = True
                    # Keep the one with direct link (not news.google.com) or relevant or longer
                    if "news.google.com" in (k_link or "") and "news.google.com" not in (link or ""):
                        ids_to_delete.add(k_id)
                        kept.remove(k)
                        kept.append(r)
                    elif k_ilgili == 0 and ilgili == 1:
                        ids_to_delete.add(k_id)
                        kept.remove(k)
                        kept.append(r)
                    elif len(title) > len(k_title) and k_ilgili == ilgili and ("news.google.com" not in (link or "")):
                        ids_to_delete.add(k_id)
                        kept.remove(k)
                        kept.append(r)
                    else:
                        ids_to_delete.add(n_id)
                    break

            if not is_dup:
                kept.append(r)

    print(f"Total duplicate historical records identified across all dates: {len(ids_to_delete)}")
    if ids_to_delete:
        c.executemany("DELETE FROM news WHERE id = ?", [(i,) for i in ids_to_delete])
        conn.commit()
        print(f"Successfully purged {len(ids_to_delete)} duplicate articles from entire database history!")

    c.execute("SELECT COUNT(*) FROM news")
    total_remaining = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM news WHERE publish_date LIKE '2026-09-01%'")
    today_remaining = c.fetchone()[0]
    print(f"Final DB Counts -> Total: {total_remaining}, Today: {today_remaining}")
    conn.close()

if __name__ == "__main__":
    clean_all_history()
