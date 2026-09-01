import sys
import time
import sqlite3
from datetime import datetime
from adapters import ALL_ADAPTER_CLASSES

def main():
    today_str = datetime.now().strftime("%Y-%m-%d")
    print("=" * 75)
    print(f"  TDT MEDYA TAKIP PORTALI - TUM KAYNAKLAR CANLI SAGLIK KONTROLU ({today_str})")
    print("=" * 75)
    
    total_fetched_all = 0
    total_today_all = 0
    results = []

    for cls in ALL_ADAPTER_CLASSES:
        adapter = cls()
        t0 = time.time()
        try:
            items = adapter.fetch_latest_news()
            elapsed = time.time() - t0
            today_cnt = sum(1 for i in items if (i.get("publish_date") or "").startswith(today_str))
            total_fetched_all += len(items)
            total_today_all += today_cnt
            status = "AKTIF [OK]" if len(items) > 0 else "BOS"
            results.append({
                "name": adapter.source_name,
                "fetched": len(items),
                "today": today_cnt,
                "time": f"{elapsed:.2f}s",
                "status": status
            })
            print(f"  [+] {adapter.source_name:<45} | Cekilen: {len(items):>3} | Bugun: {today_cnt:>3} | Sure: {elapsed:.2f}s | {status}")
        except Exception as e:
            print(f"  [-] {adapter.source_name:<45} | HATA: {e}")

    print("=" * 75)
    print(f"  GENEL TOPLAM: {total_fetched_all} Canli Haber Cekildi (Bugune Ait: {total_today_all})")
    print("=" * 75)

    # Check Database Status
    conn = sqlite3.connect("db/media_monitor.db")
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM news WHERE publish_date LIKE ?", (f"{today_str}%",))
    db_today_count = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM news WHERE publish_date LIKE ? AND ilgili_mi = 1", (f"{today_str}%",))
    db_today_relevant = c.fetchone()[0]

    c.execute("SELECT source_name, COUNT(*) FROM news WHERE publish_date LIKE ? GROUP BY source_name ORDER BY COUNT(*) DESC", (f"{today_str}%",))
    db_sources = c.fetchall()
    conn.close()

    print(f"\n  [VERITABANI DURUMU]")
    print(f"  • Bugunku Toplam Haber: {db_today_count}")
    print(f"  • Bugunku Odakli/Ilgili Haber: {db_today_relevant}")
    print(f"  • Aktif Kaynak Sayisi: {len(db_sources)}")
    print(f"\n  [KAYNAK BAZINDA DAGILIM]")
    for s_name, cnt in db_sources[:15]:
        print(f"    - {s_name:<40}: {cnt} haber")

if __name__ == "__main__":
    main()
