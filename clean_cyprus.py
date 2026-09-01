import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "db" / "media_monitor.db"

def clean_cyprus_news():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    query = """
        SELECT id, source_name, title FROM news 
        WHERE source_name LIKE '%KKTC%' 
           OR source_name LIKE '%Lefkoşa%' 
           OR source_name LIKE '%Lefkosa%' 
           OR link LIKE '%kibrispostasi.com%' 
           OR link LIKE '%kibrisgazetesi.com%' 
           OR link LIKE '%haberkibris.com%' 
           OR link LIKE '%yeniduzen.com%' 
           OR link LIKE '%brtk.net%' 
           OR link LIKE '%gundemkibris.com%'
           OR link LIKE '%kibrisnethaber.com%'
    """
    c.execute(query)
    rows = c.fetchall()
    print(f"Total Cyprus local news found to remove: {len(rows)}")

    delete_query = """
        DELETE FROM news 
        WHERE source_name LIKE '%KKTC%' 
           OR source_name LIKE '%Lefkoşa%' 
           OR source_name LIKE '%Lefkosa%' 
           OR link LIKE '%kibrispostasi.com%' 
           OR link LIKE '%kibrisgazetesi.com%' 
           OR link LIKE '%haberkibris.com%' 
           OR link LIKE '%yeniduzen.com%' 
           OR link LIKE '%brtk.net%' 
           OR link LIKE '%gundemkibris.com%'
           OR link LIKE '%kibrisnethaber.com%'
    """
    c.execute(delete_query)
    conn.commit()

    total_left = c.execute("SELECT COUNT(*) FROM news").fetchone()[0]
    print(f"Cyprus local news successfully removed! Total Türkiye articles in DB: {total_left}")
    conn.close()

if __name__ == "__main__":
    clean_cyprus_news()
