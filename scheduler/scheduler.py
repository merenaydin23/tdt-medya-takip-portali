import re
import logging
import threading
import time
from datetime import datetime, timedelta
import schedule

_last_general_serp_run = None

from concurrent.futures import ThreadPoolExecutor
from config import SCHEDULE_TIME, SOURCES_CONFIG, CATEGORIES, SERPAPI_KEY, ENABLE_AI_SUMMARY, ENABLE_LLM_STAGE2
from db import init_db, save_news_item, get_connection, clean_leading_time, update_news_relevance_classification, update_news_summary
from adapters.runner import run_all_adapters
from adapters.serpapi_adapter import SerpApiAdapter
from classifier import (
    check_stage1_relevance,
    check_stage2_llm_relevance,
    generate_az_agenda_brief,
)

logger = logging.getLogger("MediaPipeline")

# Stopwords list for Jaccard similarity calculations
STOPWORDS = {
    'daha', 'kadar', 'sonra', 'once', 'gibi', 'icin', 'olan', 'olarak', 'veya',
    'kendi', 'tarafından', 'uzere', 'altı', 'yeni', 'göre', 'gore', 'yoksa',
    'yıllık', 'yılda', 'tarihli', 'sayılı', 'konu', 'haber', 'haberleri',
    'gelen', 'gecen', 'geçen', 'böyle', 'boyle', 'şöyle', 'soyle', 'hakkında',
    'hakkinda', 'çünkü', 'cunku', 'ancak', 'lakin', 'fakat', 'yine', 'hala'
}

def _get_word_set(text: str, min_len=5) -> set:
    if not text:
        return set()
    import re
    norm = text.lower().replace('ı', 'i').replace('ö', 'o').replace('ü', 'u').replace('ş', 's').replace('ç', 'c').replace('ğ', 'g')
    words = re.findall(rf'[a-z]{{{min_len},}}', norm)
    return {w for w in words if w not in STOPWORDS}

def _jaccard_sim(set1: set, set2: set) -> float:
    if not set1 or not set2:
        return 0.0
    return len(set1.intersection(set2)) / len(set1.union(set2))


_is_running_lock = threading.Lock()
_pipeline_status = {
    "is_running": False,
    "last_run": None,
    "last_count": 0,
    "last_error": None
}
def _clean_title_for_dedup(t: str) -> str:
    if not t:
        return ""
    t = re.sub(r'^[0-2]?\d[:.][0-5]\d\s*[-–—:]?\s*', '', t)
    t = re.sub(r'\s*[-–—|]\s*(?:Haberler|Sözcü|Halk TV|TRT Haber|Yeni Şafak|Cumhuriyet|A Haber|NTV|DHA|İHA|Bengü Türk|Bengütürk).*$', '', t, flags=re.I)
    return "".join(ch for ch in t.lower() if ch.isalnum())

def _clean_title_words(s: str) -> set:
    if not s:
        return set()
    s = re.sub(r'^[0-2]?\d[:.][0-5]\d\s*[-–—:]?\s*', '', s)
    s = re.sub(r'^(?:gündem|son dakika|resmi ilan|haberler|flaş)\s*[-–—:]?\s*', '', s, flags=re.I)
    s = re.sub(r'\s*[-–—|]\s*(?:Haberler|Sözcü|Halk TV|TRT Haber|Yeni Şafak|Cumhuriyet|A Haber|NTV|DHA|İHA|Bengü Türk|Bengütürk).*$', '', s, flags=re.I)
    words = re.findall(r'[a-zA-ZğüşıöçĞÜŞİÖÇ0-9]{3,}', s.lower())
    stopwords = {"ve", "ile", "bir", "icin", "bu", "da", "de", "den", "dan", "son", "dakika", "haber", "haberi"}
    return {w for w in words if w not in stopwords}

def _get_global_dedup_sets():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT source_name, title, link, publish_date, SUBSTR(publish_date, 1, 10) as dt FROM news WHERE link IS NOT NULL AND link != ''")
    db_rows = cursor.fetchall()
    conn.close()
    existing_links = {row["link"] for row in db_rows if row["link"]}
    existing_source_titles = {(row["source_name"], row["dt"], _clean_title_for_dedup(row["title"])) for row in db_rows if row["title"]}
    
    from collections import defaultdict
    existing_source_word_sets = defaultdict(list)
    for row in db_rows:
        if row["title"]:
            w_set = _clean_title_words(row["title"])
            if w_set:
                existing_source_word_sets[(row["source_name"], row["dt"])].append((w_set, row["publish_date"]))

    return existing_links, existing_source_titles, existing_source_word_sets

def get_pipeline_status() -> dict:
    return _pipeline_status

def run_media_monitoring_pipeline() -> dict:
    """
    Full pipeline execution:
    1. Fetch news from 14 sources
    2. Stage 1 Keyword Classification
    3. Stage 2 LLM Relevance Classification (for candidate articles)
    4. Save to DB
    5. Run Cross-Comparison & Inconsistency Detection with LLM
    """
    global _pipeline_status

    if not _is_running_lock.acquire(blocking=False):
        logger.warning("Pipeline is already running! Skipping duplicate trigger.")
        return {"status": "already_running"}

    try:
        _pipeline_status["is_running"] = True
        _pipeline_status["last_error"] = None
        start_time = datetime.now()
        logger.info(f"=== Starting Media Monitoring Pipeline at {start_time} ===")

        # Ensure DB is initialized
        # Step 1: Scrape all 14 sources
        raw_articles = run_all_adapters()
        
        # Tag native sources with 'RSS' / 'Scraping'
        for item in raw_articles:
            matched_config = next((c for c in SOURCES_CONFIG if c["name"] == item.get("source_name")), None)
            if matched_config:
                item["veri_kaynagi"] = "RSS" if "rss" in matched_config.get("type", "") else "Scraping"
            else:
                item["veri_kaynagi"] = "Scraping"
                
        # Step 1.5: Run SerpApi backup search if key is set
        if SERPAPI_KEY:
            try:
                serp_adapter = SerpApiAdapter()
                # Run source-specific search concurrently
                sources_with_domain = [src for src in SOURCES_CONFIG if src.get("domain")]
                def _fetch_src(src):
                    return serp_adapter.fetch_source_backup(src["name"], src["domain"], src["category"])

                with ThreadPoolExecutor(max_workers=8) as executor:
                    for items in executor.map(_fetch_src, sources_with_domain):
                        raw_articles.extend(items)
                
                # Run general search once per day
                global _last_general_serp_run
                today_date = datetime.now().date()
                if _last_general_serp_run != today_date:
                    general_items = serp_adapter.fetch_general_news()
                    raw_articles.extend(general_items)
                    _last_general_serp_run = today_date
            except Exception as serp_err:
                logger.error(f"SerpApi backup crawling failed: {serp_err}")

        logger.info(f"Step 1 Complete: Fetched {len(raw_articles)} total articles (including SerpApi).")

        # Step 2: Instant RAM deduplication by unique URL link & source-level title uniqueness
        existing_links, existing_source_titles, existing_source_word_sets = _get_global_dedup_sets()

        import email.utils
        def parse_publish_date(date_str: str) -> datetime:
            if not date_str:
                return datetime.now()
            raw_str = date_str.strip()
            dt_obj = None
            try:
                parsed_tuple = email.utils.parsedate_tz(raw_str)
                if parsed_tuple:
                    dt_obj = datetime.fromtimestamp(email.utils.mktime_tz(parsed_tuple))
            except:
                pass
            if not dt_obj:
                try:
                    dt_obj = datetime.fromisoformat(raw_str.split(".")[0].replace("Z", ""))
                except:
                    pass
            if not dt_obj:
                for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%d.%m.%Y %H:%M:%S", "%d.%m.%Y %H:%M"):
                    try:
                        dt_obj = datetime.strptime(raw_str, fmt)
                        break
                    except:
                        pass
            if not dt_obj:
                dt_obj = datetime.now()
            # Cap to current local time so no future timestamps occur
            now_dt = datetime.now()
            if dt_obj > now_dt:
                dt_obj = now_dt
            return dt_obj

        # Strict Today Filter: Only retain articles published today (00:00:00 to now)
        cutoff_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        relevant_articles_saved = []

        # Prepare deduplicated list for Stage 1 & Stage 2 processing
        items_to_process = []
        for item in raw_articles:
            raw_title = item.get("title", "")
            # Check if title has time prefix (e.g. "14:24 - ...")
            import re
            m_time = re.match(r'^([0-2]?\d)[:.]([0-5]\d)\s*[-–—:]?\s*', raw_title)
            
            pub_date_str = item.get("publish_date", "")
            pub_dt = parse_publish_date(pub_date_str)
            
            # If pub_dt has default time but title had specific time, apply it
            if m_time and pub_dt.strftime("%H:%M:%S") == "00:00:00":
                h, m = int(m_time.group(1)), int(m_time.group(2))
                pub_dt = pub_dt.replace(hour=h, minute=m, second=0)

            # Skip if older than today 00:00:00
            if pub_dt.replace(tzinfo=None) < cutoff_date.replace(tzinfo=None):
                continue

            # Standardize date format in DB
            item["publish_date"] = pub_dt.strftime("%Y-%m-%d %H:%M:%S")

            # Deduplication & Junk checks
            link = item.get("link", "")
            title = clean_leading_time(raw_title)
            
            from adapters.base_adapter import is_junk_title
            if is_junk_title(title):
                continue

            if not link or link in existing_links:
                continue

            s_name = item.get("source_name", "")
            dt_day = pub_dt.strftime("%Y-%m-%d")
            clean_t = _clean_title_for_dedup(title)
            w_set = _clean_title_words(title)

            # Prevent same source from inserting the exact same article multiple times
            if clean_t and (s_name, dt_day, clean_t) in existing_source_titles:
                continue

            # Prevent same source from inserting near-duplicate headline revisions
            is_near_dup = False
            if w_set and len(w_set) >= 3:
                for prev_w_set, prev_dt_str in existing_source_word_sets[(s_name, dt_day)]:
                    sim = _jaccard_sim(w_set, prev_w_set)
                    if sim >= 0.65 or w_set.issubset(prev_w_set) or prev_w_set.issubset(w_set):
                        is_near_dup = True
                        break
            if is_near_dup:
                continue

            existing_links.add(link)
            if clean_t:
                existing_source_titles.add((s_name, dt_day, clean_t))
            if w_set:
                existing_source_word_sets[(s_name, dt_day)].append((w_set, item["publish_date"]))

            items_to_process.append(item)

        # Smart parallel scraping of full article body texts ONLY when summary is missing
        needed_body_scrape = [item for item in items_to_process if not item.get("summary") or len(item.get("summary", "").strip()) < 50]
        if needed_body_scrape:
            from adapters.base_adapter import scrape_article_text
            logger.info(f"Fast scraping full content for {len(needed_body_scrape)} articles with missing summary...")
            
            def _scrape_worker(item):
                link = item.get("link")
                if link:
                    res = scrape_article_text(link, timeout=2.0)
                    if res:
                        if res.get("text"):
                            item["summary"] = res["text"]
                        if res.get("publish_date"):
                            pub_dt = parse_publish_date(res["publish_date"])
                            item["publish_date"] = pub_dt.strftime("%Y-%m-%d %H:%M:%S")

            with ThreadPoolExecutor(max_workers=12) as executor:
                list(executor.map(_scrape_worker, needed_body_scrape))

        # Strict Second-Pass Cutoff: Drop any articles whose scraped date is older than today 00:00:00
        clean_today_items = []
        for it in items_to_process:
            pub_dt = parse_publish_date(it.get("publish_date", ""))
            if pub_dt.replace(tzinfo=None) < cutoff_date.replace(tzinfo=None):
                continue
            clean_today_items.append(it)
        items_to_process = clean_today_items

        logger.info(f"Link-based deduplication complete. Total unique articles to categorize: {len(items_to_process)}.")


        # Stage 1 keyword matching
        stage2_candidates = []
        for item in items_to_process:
            title = clean_leading_time(item.get("title", ""))
            summary = item.get("summary", "")
            s1_result = check_stage1_relevance(title, summary)
            is_candidate = s1_result.get("is_relevant", False)

            if is_candidate:
                item["ilgili_mi"] = 1
                item["ilgi_kategorisi"] = s1_result.get("aspect") or "Doğrudan"
                item["guven_skoru"] = 0.95
                item["gerekce"] = s1_result.get("explanation") or "Anahtar kelime eşleşmesi."
                item["relevance_status"] = s1_result["stage"]
                item["relevance_aspect"] = item["ilgi_kategorisi"]
                item["llm_relevance_explanation"] = item["gerekce"]
            elif s1_result.get("is_candidate_for_stage2"):
                stage2_candidates.append(item)
            else:
                item["ilgili_mi"] = 0
                item["ilgi_kategorisi"] = "İlgisiz"
                item["guven_skoru"] = 0.0
                item["gerekce"] = ""
                item["relevance_status"] = "Genel (Filtresiz)"
                item["relevance_aspect"] = "Genel"
                item["llm_relevance_explanation"] = ""

        # Run Stage 2 LLM relevance concurrently for stage2_candidates if enabled
        if stage2_candidates:
            if ENABLE_LLM_STAGE2:
                logger.info(f"Running Stage 2 LLM evaluation concurrently for {len(stage2_candidates)} candidates...")
                def _eval_stage2(item):
                    title = clean_leading_time(item.get("title", ""))
                    summary = item.get("summary", "")
                    s2 = check_stage2_llm_relevance(
                        title,
                        summary,
                        source_name=item.get("source_name", ""),
                        category=item.get("category", "Genel"),
                    )
                    if s2.get("is_relevant") or s2.get("ilgili_mi"):
                        item["ilgili_mi"] = 1
                        item["ilgi_kategorisi"] = s2.get("ilgi_kategorisi") or s2.get("aspect") or "Doğrudan"
                        item["guven_skoru"] = float(s2.get("guven_skoru") or 0.7)
                        item["gerekce"] = s2.get("gerekce") or s2.get("explanation") or ""
                        item["relevance_status"] = "Stage 2 (LLM)"
                        item["relevance_aspect"] = item["ilgi_kategorisi"]
                        item["llm_relevance_explanation"] = item["gerekce"]
                    else:
                        item["ilgili_mi"] = 0
                        item["ilgi_kategorisi"] = "İlgisiz"
                        item["guven_skoru"] = 0.0
                        item["gerekce"] = ""
                        item["relevance_status"] = "Genel (Filtresiz)"
                        item["relevance_aspect"] = "Genel"
                        item["llm_relevance_explanation"] = ""

                with ThreadPoolExecutor(max_workers=4) as executor:
                    list(executor.map(_eval_stage2, stage2_candidates))
            else:
                for item in stage2_candidates:
                    item["ilgili_mi"] = 0
                    item["ilgi_kategorisi"] = "İlgisiz"
                    item["guven_skoru"] = 0.0
                    item["gerekce"] = ""
                    item["relevance_status"] = "Genel (Filtresiz)"
                    item["relevance_aspect"] = "Genel"
                    item["llm_relevance_explanation"] = ""

        # Save processed items to DB
        for item in items_to_process:
            news_id = save_news_item(item)
            item["id"] = news_id
            relevant_articles_saved.append(item)

        logger.info(f"Step 2 Complete: Saved and categorized {len(relevant_articles_saved)} new articles.")

        # Step 3: Azerbaycan gündemi içerik özetleri (yalnızca ENABLE_AI_SUMMARY açık ise)
        if ENABLE_AI_SUMMARY:
            az_for_brief = [a for a in relevant_articles_saved if a.get("ilgili_mi") in (1, True, "1")]
            def run_background_ai_tasks():
                try:
                    summarize_azerbaijan_agenda(az_for_brief)
                    backfill_azerbaijan_briefs()
                except Exception as e:
                    logger.error(f"Error summarizing Azerbaijan agenda briefs: {e}")

            threading.Thread(target=run_background_ai_tasks, daemon=True, name="BackgroundAITasks").start()
        else:
            logger.info("AI ile özetleme ve yorumlama devre dışı (ENABLE_AI_SUMMARY=False).")

        duration = (datetime.now() - start_time).total_seconds()
        _pipeline_status["last_run"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        _pipeline_status["last_count"] = len(relevant_articles_saved)
        logger.info(f"=== Pipeline Completed in {duration:.1f}s. Relevant articles saved: {len(relevant_articles_saved)} ===")

        return {
            "status": "success",
            "relevant_count": len(relevant_articles_saved),
            "total_fetched": len(raw_articles),
            "duration_seconds": duration
        }

    except Exception as e:
        logger.error(f"Error during pipeline execution: {e}", exc_info=True)
        _pipeline_status["last_error"] = str(e)
        return {"status": "error", "message": str(e)}
    finally:
        _pipeline_status["is_running"] = False
        _is_running_lock.release()


def _needs_az_brief(summary: str) -> bool:
    s = (summary or "").strip()
    if len(s) < 60:
        return True
    if s in ("...", "` and `"):
        return True
    if s.endswith("...") or s.endswith("…"):
        return True
    return False


def summarize_azerbaijan_agenda(articles: list, max_workers: int = 4):
    """Yalnızca Azerbaycan Gündemi haberleri için genel içerik açıklama özeti üretir (paralel)."""
    if not articles:
        return

    logger.info(f"Generating content briefs concurrently (workers={max_workers}) for {len(articles)} Azerbaijan agenda articles...")
    
    def _process_single(item):
        try:
            news_id = item.get("id")
            if not news_id:
                return
            title = item.get("title") or ""
            raw = item.get("summary") or ""
            content = title if _needs_az_brief(raw) else raw
            brief = generate_az_agenda_brief(
                title,
                content,
                item.get("ilgi_kategorisi") or "",
            )
            if brief:
                update_news_summary(news_id, brief)
                item["summary"] = brief
                logger.info(f"AZ brief saved for article ID {news_id}")
        except Exception as e:
            logger.error(f"Error creating AZ brief for {item.get('id')}: {e}")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        list(executor.map(_process_single, articles))

    logger.info("Azerbaijan agenda briefing complete.")


def backfill_azerbaijan_briefs():
    """Eksik özeti olan mevcut Azerbaycan gündemi haberlerini tamamlar."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, title, summary, ilgi_kategorisi FROM news
        WHERE ilgili_mi = 1
          AND (
            summary IS NULL OR summary = '' OR summary = '...' OR summary = '` and `'
            OR summary LIKE '%...'
            OR length(summary) < 60
          )
        ORDER BY publish_date DESC
        LIMIT 40
    """)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    if not rows:
        return
    logger.info(f"Backfilling {len(rows)} existing Azerbaijan agenda briefs...")
    summarize_azerbaijan_agenda(rows)


def trigger_manual_refresh():
    """Triggers manual pipeline execution in background thread."""
    thread = threading.Thread(target=run_media_monitoring_pipeline, daemon=True)
    thread.start()
    return thread

def _scheduler_loop():
    logger.info("Background scheduler initiated. Auto-scanning sources every 3 minutes.")
    schedule.every(3).minutes.do(run_media_monitoring_pipeline)

    while True:
        try:
            schedule.run_pending()
        except Exception as e:
            logger.error(f"Scheduler exception: {e}")
        time.sleep(5)

def start_background_scheduler():
    """Starts the daily cron scheduler. Keep python run.py running for scans to continue."""
    scheduler_thread = threading.Thread(target=_scheduler_loop, daemon=True, name="MediaSchedulerThread")
    scheduler_thread.start()
    # Mevcut AZ gündemi haberleri için özetleri arka planda tamamla (Kullanıcı isteğiyle kapatıldı)
    # threading.Thread(target=backfill_azerbaijan_briefs, daemon=True, name="AZBriefBackfill").start()
    return scheduler_thread
