import sqlite3
import re
from collections import defaultdict
from datetime import datetime

def clean_title_words(s):
    if not s:
        return set()
    # Remove leading times, prefixes, suffixes
    s = re.sub(r'^[0-2]?\d[:.][0-5]\d\s*[-–—:]?\s*', '', s)
    s = re.sub(r'^(?:gündem|son dakika|resmi ilan|haberler|flaş)\s*[-–—:]?\s*', '', s, flags=re.I)
    s = re.sub(r'\s*[-–—|]\s*(?:Haberler|Sözcü|Halk TV|TRT Haber|Yeni Şafak|Cumhuriyet|A Haber|NTV|DHA|İHA|Bengü Türk|Bengütürk).*$', '', s, flags=re.I)
    words = re.findall(r'[a-zA-ZğüşıöçĞÜŞİÖÇ0-9]{3,}', s.lower())
    stopwords = {"ve", "ile", "bir", "icin", "icin", "bu", "da", "de", "den", "dan", "son", "dakika", "haber", "haberi", "kap", "uygulamasi", "bildirimi"}
    return {w for w in words if w not in stopwords}

def jaccard(s1, s2):
    if not s1 or not s2: return 0.0
    return len(s1 & s2) / len(s1 | s2)

def parse_time(dt_str):
    try:
        return datetime.strptime(dt_str[:19], "%Y-%m-%d %H:%M:%S")
    except:
        return None

def clean_near_duplicates():
    conn = sqlite3.connect("db/media_monitor.db")
    c = conn.cursor()
    c.execute("SELECT id, source_name, title, publish_date, link, ilgili_mi, ilgi_kategorisi, summary FROM news WHERE publish_date LIKE '2026-09-01%' ORDER BY id ASC")
    rows = c.fetchall()

    by_source = defaultdict(list)
    for r in rows:
        by_source[r[1]].append(r)

    ids_to_delete = set()
    total_found = 0

    for s_name, s_rows in by_source.items():
        kept = []
        for r in s_rows:
            n_id, _, title, pub_date, link, ilgili, cat, summary = r
            w_set = clean_title_words(title)
            t_obj = parse_time(pub_date)
            
            # Skip KAP generic notices
            if "BISTECH" in title and "KAP" in title:
                continue

            is_dup = False
            for k in list(kept):
                k_id, _, k_title, k_date, k_link, k_ilgili, k_cat, k_summary = k
                k_w_set = clean_title_words(k_title)
                k_t_obj = parse_time(k_date)

                sim = jaccard(w_set, k_w_set)
                
                # Check time proximity if both timestamps available
                time_diff_mins = None
                if t_obj and k_t_obj:
                    time_diff_mins = abs((t_obj - k_t_obj).total_seconds()) / 60.0

                # Duplicate condition:
                # 1. Very high title similarity (>= 0.65)
                # 2. Or moderate similarity (>= 0.50) when published within 60 minutes of each other
                # 3. Or exact phrase prefix match
                is_near_dup = (sim >= 0.65) or (sim >= 0.50 and time_diff_mins is not None and time_diff_mins <= 60)
                
                # Check for subset title match (one title is virtually inside the other)
                if not is_near_dup and (w_set.issubset(k_w_set) or k_w_set.issubset(w_set)) and min(len(w_set), len(k_w_set)) >= 3:
                    is_near_dup = True

                if is_near_dup:
                    is_dup = True
                    total_found += 1
                    # Decide which one to keep
                    # Prefer the one with relevance = 1 or direct link or longer title
                    if (k_ilgili == 0 and ilgili == 1) or (len(title) > len(k_title) and k_ilgili == ilgili):
                        ids_to_delete.add(k_id)
                        kept.remove(k)
                        kept.append(r)
                    else:
                        ids_to_delete.add(n_id)
                    break

            if not is_dup:
                kept.append(r)

    print(f"Total near duplicate revisions identified: {len(ids_to_delete)}")
    
    if ids_to_delete:
        c.executemany("DELETE FROM news WHERE id = ?", [(i,) for i in ids_to_delete])
        conn.commit()
        print(f"Successfully purged {len(ids_to_delete)} near-duplicate revisions from DB!")

    c.execute("SELECT COUNT(*), COUNT(CASE WHEN ilgili_mi = 1 THEN 1 END) FROM news WHERE publish_date LIKE '2026-09-01%'")
    total_now, relevant_now = c.fetchone()
    print(f"Updated clean database counts for today: Total={total_now}, Relevant={relevant_now}")
    conn.close()

if __name__ == "__main__":
    clean_near_duplicates()
