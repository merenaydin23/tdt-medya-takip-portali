import sqlite3
from pathlib import Path
from datetime import datetime
from adapters.base_adapter import extract_turkish_date_from_text

DB_PATH = Path(__file__).resolve().parent / "db" / "media_monitor.db"

def purge_outdated_local_news():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    cutoff_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    print(f"Purging articles published before {cutoff_date.strftime('%Y-%m-%d %H:%M:%S')}...")

    c.execute("SELECT id, title, summary, source_name, publish_date FROM news")
    rows = c.fetchall()

    deleted_ids = []
    for r in rows:
        title = r["title"] or ""
        summary = r["summary"] or ""
        pub_str = r["publish_date"] or ""
        
        # 1. Check DB publish_date column
        try:
            db_dt = datetime.strptime(pub_str, "%Y-%m-%d %H:%M:%S")
            if db_dt < cutoff_date:
                deleted_ids.append((r["id"], r["source_name"], title, f"DB date was {pub_str}"))
                continue
        except:
            pass

        # 2. Check title text for explicit past date (e.g. 31 Ağustos, 30 Ağustos)
        t_date = extract_turkish_date_from_text(title)
        if t_date and t_date < cutoff_date:
            deleted_ids.append((r["id"], r["source_name"], title, f"Title contained {t_date.strftime('%Y-%m-%d')}"))
            continue

        # 3. Check lead summary for explicit past date
        s_date = extract_turkish_date_from_text(summary[:500])
        if s_date and s_date < cutoff_date:
            deleted_ids.append((r["id"], r["source_name"], title, f"Summary contained {s_date.strftime('%Y-%m-%d')}"))
            continue

    print(f"Found {len(deleted_ids)} outdated news items.")
    for d_id, src, t, reason in deleted_ids[:25]:
        print(f"   [DELETED OLD NEWS] [{src}] -> '{t}' ({reason})")

    if deleted_ids:
        c.executemany("DELETE FROM news WHERE id = ?", [(d[0],) for d in deleted_ids])
        conn.commit()

    total_left = c.execute("SELECT COUNT(*) FROM news").fetchone()[0]
    print(f"Purge complete! Clean verified today's articles remaining in DB: {total_left}")
    conn.close()

if __name__ == "__main__":
    purge_outdated_local_news()
