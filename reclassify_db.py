import sqlite3
from pathlib import Path
from classifier.stage1 import check_stage1_relevance

DB_PATH = Path(__file__).resolve().parent / "db" / "media_monitor.db"

def reclassify_existing_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("SELECT id, title, summary FROM news")
    rows = c.fetchall()
    print(f"Re-classifying {len(rows)} articles in database...")

    updated_relevant = 0
    updated_irrelevant = 0

    for r in rows:
        title = r["title"] or ""
        summary = r["summary"] or ""
        
        res = check_stage1_relevance(title, summary)
        
        if res.get("is_relevant"):
            aspect = res.get("aspect", "Doğrudan")
            c.execute("""
                UPDATE news 
                SET ilgili_mi = 1, 
                    ilgi_kategorisi = ?, 
                    relevance_status = 'Stage 1 (Anahtar Kelime)',
                    relevance_aspect = ?,
                    llm_relevance_explanation = ?
                WHERE id = ?
            """, (aspect, aspect, res.get("explanation", ""), r["id"]))
            updated_relevant += 1
        else:
            c.execute("""
                UPDATE news 
                SET ilgili_mi = 0, 
                    ilgi_kategorisi = 'İlgisiz', 
                    relevance_status = 'Genel (Filtresiz)',
                    relevance_aspect = 'Genel',
                    llm_relevance_explanation = ''
                WHERE id = ?
            """, (r["id"],))
            updated_irrelevant += 1

    conn.commit()
    print(f"Reclassification complete! Relevant: {updated_relevant}, Irrelevant: {updated_irrelevant}")
    
    print("\n--- CATEGORY BREAKDOWN IN DB ---")
    c.execute("SELECT ilgi_kategorisi, COUNT(*) FROM news WHERE ilgili_mi = 1 GROUP BY ilgi_kategorisi ORDER BY COUNT(*) DESC")
    for row in c.fetchall():
        print(f"  • {row[0]}: {row[1]} haber")

    conn.close()

if __name__ == "__main__":
    reclassify_existing_db()
