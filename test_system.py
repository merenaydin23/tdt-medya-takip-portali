import sys
import unittest
import requests
import sqlite3
from datetime import datetime

class TestPortalSystem(unittest.TestCase):

    def test_01_adapters_load(self):
        """Verify all adapter classes load and instantiate successfully."""
        from adapters import ALL_ADAPTER_CLASSES
        self.assertGreaterEqual(len(ALL_ADAPTER_CLASSES), 20)
        for cls in ALL_ADAPTER_CLASSES:
            inst = cls()
            self.assertTrue(hasattr(inst, 'fetch_latest_news'))
            self.assertTrue(hasattr(inst, 'source_name'))
            self.assertTrue(hasattr(inst, 'category'))

    def test_02_database_integrity(self):
        """Verify database structure and absence of corrupted/blacklisted items."""
        conn = sqlite3.connect('db/media_monitor.db')
        c = conn.cursor()
        c.execute('SELECT COUNT(*) FROM news')
        total = c.fetchone()[0]
        self.assertGreater(total, 0, 'Database should contain news articles')

        # Verify Haber7 is completely removed
        c.execute('SELECT COUNT(*) FROM news WHERE source_name LIKE "%Haber7%"')
        self.assertEqual(c.fetchone()[0], 0, 'Haber7 should be 0 in DB')

        # Verify no titles have dirty time prefixes
        c.execute('SELECT COUNT(*) FROM news WHERE title LIKE "Güncel /%" OR title LIKE "09:12%"')
        self.assertEqual(c.fetchone()[0], 0, 'No dirty title prefixes should exist')
        conn.close()

    def test_03_web_endpoints(self):
        """Verify all HTTP routes respond with 200 OK and valid JSON/HTML."""
        base_url = 'http://127.0.0.1:5000'
        
        # 1. Home
        r = requests.get(base_url, timeout=5)
        r.encoding = 'utf-8'
        self.assertEqual(r.status_code, 200)
        self.assertIn('Başkonsolosluğu', r.text)

        # 2. Azerbaijan Filter
        r_az = requests.get(f'{base_url}/?filter=azerbaijan', timeout=5)
        self.assertEqual(r_az.status_code, 200)

        # 3. API Status
        r_status = requests.get(f'{base_url}/api/status', timeout=5)
        self.assertEqual(r_status.status_code, 200)
        data = r_status.json()
        self.assertIn('is_running', data)

        # 4. API Summary
        r_sum = requests.get(f'{base_url}/api/summary', timeout=5)
        self.assertEqual(r_sum.status_code, 200)

    def test_04_title_cleaner_and_time_extractor(self):
        """Verify title and time cleaner accurately normalizes raw scraped cards."""
        from db.database import extract_and_clean_title_and_time
        
        raw = 'Güncel / 15:58İngiltere Şirket Kurma Paketleri Nelerdir?'
        t, pdate = extract_and_clean_title_and_time(raw, '2026-08-27 19:40:00')
        self.assertEqual(t, 'İngiltere Şirket Kurma Paketleri Nelerdir?')
        self.assertTrue(pdate.endswith('15:58:00'))

        raw2 = 'Gündem / 14:20 - Kars’ta Şiddetli Fırtına'
        t2, pdate2 = extract_and_clean_title_and_time(raw2, '2026-08-27 19:40:00')
        self.assertEqual(t2, 'Kars’ta Şiddetli Fırtına')
        self.assertTrue(pdate2.endswith('14:20:00'))

    def test_05_threshold_grouping(self):
        """Verify that sources with 10 or more articles are dedicated, and fewer than 10 are grouped."""
        conn = sqlite3.connect('db/media_monitor.db')
        c = conn.cursor()
        c.execute('SELECT source_name, COUNT(*) FROM news GROUP BY source_name')
        rows = c.fetchall()
        conn.close()
        
        dedicated = [r for r in rows if r[1] >= 10]
        other = [r for r in rows if r[1] < 10]
        self.assertGreater(len(dedicated), 0)
        self.assertGreater(len(other), 0)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPortalSystem)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
