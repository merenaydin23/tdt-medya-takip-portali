import sqlite3
import re
from collections import defaultdict

def normalize_title(t):
    if not t:
        return ""
    t = re.sub(r'^[0-2]?\d[:.][0-5]\d\s*[-–—:]?\s*', '', t)
    t = re.sub(r'^(?:gündem|son dakika|resmi ilan|haberler|flaş)\s*[-–—:]?\s*', '', t, flags=re.I)
    t = re.sub(r'\s*[-–—|]\s*(?:Haberler|Sözcü|Halk TV|TRT Haber|Yeni Şafak|Cumhuriyet|A Haber|NTV|DHA|İHA|Bengü Türk|Bengütürk).*$', '', t, flags=re.I)
    return "".join(ch for ch in t.lower() if ch.isalnum())

def purge_all_duplicates():
    conn = sqlite3.connect("db/media_monitor.db")
    c = conn.cursor()

    c.execute("SELECT id, source_name, title, link, publish_date, ilgili_mi, summary FROM news ORDER BY id ASC")
    rows = c.fetchall()
    print(f"Total articles in DB before purge: {len(rows)}")

    by_key = defaultdict(list)
    for r in rows:
        n_id, s_name, title, link, pub_date, ilgili_mi, summary = r
        dt_day = (pub_date or "")[:10]
        norm_t = normalize_title(title)
        
        # Unique key: source + date + normalized title
        key = (s_name, dt_day, norm_t) if norm_t else (s_name, dt_day, link)
        by_key[key].append(r)

    ids_to_delete = []
    for key, group in by_key.items():
        if len(group) > 1:
            # Sort group: prioritize direct domain link (not news.google.com), ilgili_mi = 1, longer summary
            def sort_key(item):
                n_id, s_name, title, link, pub_date, ilgili_mi, summary = item
                is_direct = 1 if "news.google.com" not in (link or "") else 0
                is_rel = 1 if ilgili_mi == 1 else 0
                sum_len = len(summary or "")
                return (is_rel, is_direct, sum_len, n_id)

            sorted_group = sorted(group, key=sort_key, reverse=True)
            # Keep sorted_group[0], delete all others
            for dup in sorted_group[1:]:
                ids_to_delete.append(dup[0])

    print(f"Identified {len(ids_to_delete)} duplicate records to delete.")
    if ids_to_delete:
        c.executemany("DELETE FROM news WHERE id = ?", [(i,) for i in ids_to_delete])
        conn.commit()
        print(f"Successfully deleted {len(ids_to_delete)} duplicate records from database!")

    # Verify zero duplicates remain
    c.execute("SELECT id, source_name, title, publish_date FROM news")
    remaining_rows = c.fetchall()
    check_dups = defaultdict(list)
    for r in remaining_rows:
        n_id, s_name, title, pub_date = r
        dt_day = (pub_date or "")[:10]
        norm_t = normalize_title(title)
        check_dups[(s_name, dt_day, norm_t)].append(n_id)

    dups_left = sum(len(v) - 1 for v in check_dups.values() if len(v) > 1)
    print(f"Total remaining articles in DB: {len(remaining_rows)} | Duplicates left: {dups_left}")

    conn.close()

if __name__ == "__main__":
    purge_all_duplicates()
