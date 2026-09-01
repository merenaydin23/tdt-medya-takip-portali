import sqlite3
from pathlib import Path
from adapters.base_adapter import is_junk_title

DB_PATH = Path(__file__).resolve().parent / "db" / "media_monitor.db"

def purge_junk_titles():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("SELECT id, title, source_name FROM news")
    rows = c.fetchall()
    print(f"Checking {len(rows)} articles in database for junk titles...")

    junk_ids = []
    for r in rows:
        title = r["title"] or ""
        if is_junk_title(title):
            junk_ids.append((r["id"], r["source_name"], title))

    print(f"Found {len(junk_ids)} junk titles to remove.")
    for j_id, src, t in junk_ids[:20]:
        print(f"   [DELETED] [{src}] -> '{t}'")

    if junk_ids:
        c.executemany("DELETE FROM news WHERE id = ?", [(j[0],) for j in junk_ids])
        conn.commit()

    total_left = c.execute("SELECT COUNT(*) FROM news").fetchone()[0]
    print(f"Purge complete! Remaining clean news articles in DB: {total_left}")
    conn.close()

if __name__ == "__main__":
    purge_junk_titles()
