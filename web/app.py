import os
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for
from config import BASE_DIR, PORT, HOST, DEBUG, CATEGORIES, LLM_MODEL, SCHEDULE_TIME, SOURCES_CONFIG, ENABLE_AI_SUMMARY, ENABLE_LLM_STAGE2
from db import init_db, get_news_by_date, get_available_dates, get_daily_summary
from scheduler import start_background_scheduler, trigger_manual_refresh, get_pipeline_status

def turkish_lower(s: str) -> str:
    if not s:
        return ""
    return s.replace("İ", "i").replace("I", "ı").replace("Ə", "ə").lower()

TRANSLATIONS = {
    "tr": {
        "title": "Türk Dünyası Medya Portalı",
        "subtitle": "Türkiye Basını Canlı Medya Takip Portalı",
        "all_news": "Tüm Haberler (Filtresiz)",
        "az_oriented": "🌐 Odaklı Gündem",
        "date_label": "Tarih:",
        "refresh_btn": "Kaynakları Yeniden Tara",
        "refresh_btn_scanning": "Taranıyor...",
        "scanning_banner": "Medya Tarama ve Yapay Zeka Analizi Devam Ediyor...",
        "scanning_banner_sub": "Tüm medya kaynaklarından ve Google News üzerinden veriler toplanıyor ve Qwen LLM ile analiz ediliyor. Tamamlandığında sayfa otomatik güncellenecektir.",
        "displayed_total": "Görüntülenen Toplam Haber",
        "az_related_total": "İlgili Toplam Haber",
        "resmi": "Resmi / Ana Akım",
        "iktidar": "İktidar Yanlısı",
        "muhalif": "Muhalif Basın",
        "disclaimer_title": "Filtre Durumu:",
        "disclaimer_all": "Şu anda tüm haberler filtresiz olarak listelenmektedir. Yalnızca odaklı haberleri görmek için üstteki 'Odaklı Gündem' butonuna basabilirsiniz.",
        "disclaimer_az": "Şu anda sadece Türk Dünyası (Azerbaycan, Kazakistan, Kırgızistan, Özbekistan, Türkmenistan, KKTC) ile ilgili haberler gösterilmektedir.",
        "empty_state": "Bu kategoride haber bulunamadı.",
        "footer_embassy": "Türk Dünyası Canlı Medya Takip ve İletişim Koordinasyonu",
        "footer_schedule": "Otomatik Tarama:",
        "footer_ai": "Yapay Zeka:",
        "footer_sources": "Geniş Kapsamlı Canlı Medya Takibi",
        "original_link": "Orijinali Gör",
        "keyword_badge": "🔍 Anahtar Kelime",
        "llm_badge": "🤖 Yapay Zeka (Qwen)",
        "genel_badge": "📰 Genel Akış",
        "aspect_label": "📌 İlgi Açısı:",
        "all_sources": "Hepsi",
        "sources_title": "Haber Kaynakları",
        "all_sources_sidebar": "Tüm Kaynaklar",
        "other_sources": "Diğer Kaynaklar",
        "search_placeholder": "Haber başlığı veya anahtar kelime ara...",
        "search_btn": "Ara",
        "tab_all_media": "Tüm Medya Akışı",
        "tab_az_agenda": "Odaklı Gündem",
        "tab_azerbaycan": "Azerbaycan",
        "tab_kazakistan": "Kazakistan",
        "tab_kirgizistan": "Kırgızistan",
        "tab_ozbekistan": "Özbekistan",
        "tab_turkmenistan": "Türkmenistan",
        "tab_kktc": "KKTC",
        "az_filter_all": "Tümü",
        "az_filter_ermenistan": "Ermenistan Hattı",
        "az_filter_diplomasi": "Diplomasi & Siyaset",
        "az_filter_turk_devletleri": "Türk Devletleri / Bölgesel",
        "az_filter_enerji": "Enerji / Ekonomi",
        "az_filter_guvenlik": "Güvenlik / Savunma",
        "az_filter_spor": "Spor",
        "az_filter_kazakistan": "🇰🇿 Kazakistan",
        "az_filter_kirgizistan": "🇰🇬 Kırgızistan",
        "az_filter_ozbekistan": "🇺🇿 Özbekistan",
        "az_filter_turkmenistan": "🇹🇲 Türkmenistan",
        "az_filter_kktc": "🇹🇷 KKTC",
        "az_empty_state": "Bu kategoride ilgili haber bulunamadı.",
        "az_brief_label": "İçerik özeti",
        "sort_label": "Zaman Sıralaması:",
        "sort_newest": "🕒 En Yeni İlk",
        "sort_oldest": "🕒 En Eski İlk"
    },
    "az": {
        "title": "Türk Dünyası Media Portalı",
        "subtitle": "Türkiyə Mətbuatı Canlı Media Təqib Portalı",
        "all_news": "Bütün Xəbərlər (Filtrsiz)",
        "az_oriented": "🌐 Seçilmiş Gündəm",
        "date_label": "Tarix:",
        "refresh_btn": "Mənbələri Yenidən Tara",
        "refresh_btn_scanning": "Tarama gedir...",
        "scanning_banner": "Media Tarama və Süni İntellekt Təhlili Davam Edir...",
        "scanning_banner_sub": "Bütün media mənbələrindən və Google News üzərindən məlumatlar toplanır və Qwen LLM ilə təhlil edilir. Tamamlandıqda səhifə avtomatik yenilənəcəkdir.",
        "displayed_total": "Göstərilən Ümumi Xəbər",
        "az_related_total": "Bağlı Ümumi Xəbər",
        "resmi": "Rəsmi / Əsas Medya",
        "iktidar": "İqtidaryönlü Medya",
        "muhalif": "Müxalif Mətbuat",
        "disclaimer_title": "Filtr Statusu:",
        "disclaimer_all": "Hazırda bütün xəbərlər filtrsiz olaraq siyahıya alınır. Yalnız seçilmiş ölkələrlə bağlı xəbərləri görmək üçün yuxarıdakı 'Seçilmiş Gündəm' düyməsinə basa bilərsiniz.",
        "disclaimer_az": "Hazırda yalnız Türk Dünyası (Azərbaycan, Qazaxıstan, Qırğızıstan, Özbəkistan, Türkmənistan, KKTC) ilə bağlı xəbərlər göstərilir.",
        "empty_state": "Bu kateqoriyada xəbər tapılmadı.",
        "footer_embassy": "Türk Dünyası Canlı Media Təqib və İnteqrasiya Koordinasiyası",
        "footer_schedule": "Avtomatik Tarama:",
        "footer_ai": "Süni İntellekt:",
        "footer_sources": "Geniş Əhatəli Canlı Media Təqibi",
        "original_link": "Orijinalı Gör",
        "keyword_badge": "🔍 Açar Söz",
        "llm_badge": "🤖 Süni İntellekt (Qwen)",
        "genel_badge": "📰 Ümumi Axın",
        "aspect_label": "📌 Mövzu:",
        "all_sources": "Hamısı",
        "sources_title": "Xəbər Mənbələri",
        "all_sources_sidebar": "Bütün Mənbələr",
        "other_sources": "Digər Mənbələr",
        "search_placeholder": "Xəbər başlığı və ya açar söz axtar...",
        "search_btn": "Axtar",
        "tab_all_media": "Bütün Media Axını",
        "tab_az_agenda": "Seçilmiş Gündəm",
        "tab_azerbaycan": "Azərbaycan",
        "tab_kazakistan": "Qazaxıstan",
        "tab_kirgizistan": "Qırğızıstan",
        "tab_ozbekistan": "Özbəkistan",
        "tab_turkmenistan": "Türkmənistan",
        "tab_kktc": "ŞKTC / KKTC",
        "az_filter_all": "Hamısı",
        "az_filter_ermenistan": "Ermənistan Xətti",
        "az_filter_diplomasi": "Diplomatiya və Siyasət",
        "az_filter_turk_devletleri": "Türk Dövlətləri / Regional",
        "az_filter_enerji": "Enerji / İqtisadiyyat",
        "az_filter_guvenlik": "Təhlükəsizlik / Müdafiə",
        "az_filter_spor": "İdman",
        "az_filter_kazakistan": "🇰🇿 Qazaxıstan",
        "az_filter_kirgizistan": "🇰🇬 Qırğızıstan",
        "az_filter_ozbekistan": "🇺🇿 Özbəkistan",
        "az_filter_turkmenistan": "🇹🇲 Türkmənistan",
        "az_filter_kktc": "🇹🇷 ŞKTC / KKTC",
        "az_empty_state": "Bu kateqoriyada bağlı xəbər tapılmadı.",
        "az_brief_label": "Məzmun xülasəsi",
        "sort_label": "Zaman Sıralaması:",
        "sort_newest": "🕒 Ən Yeni İlkin",
        "sort_oldest": "🕒 Ən Köhnə İlkin"
    }
}

MEDIA_OUTLET_CATEGORIES = {
    # Resmi / Ana Akım
    "anadolu ajansı (aa)": "Resmi / Ana Akım",
    "aa": "Resmi / Ana Akım",
    "trt haber": "Resmi / Ana Akım",
    "ihlas haber ajansı (iha)": "Resmi / Ana Akım",
    "i̇hlas haber ajansı (i̇ha)": "Resmi / Ana Akım",
    "iha": "Resmi / Ana Akım",
    "dha | demirören haber ajansı": "Resmi / Ana Akım",
    "dha": "Resmi / Ana Akım",
    "milliyet": "Resmi / Ana Akım",
    "hürriyet": "Resmi / Ana Akım",
    "ntv haber": "Resmi / Ana Akım",
    "ntv": "Resmi / Ana Akım",
    "habertürk": "Resmi / Ana Akım",
    "cnn türk": "Resmi / Ana Akım",
    "cnnturk.com": "Resmi / Ana Akım",
    "bloomberght": "Resmi / Ana Akım",
    "ekonomim": "Resmi / Ana Akım",

    # İktidar Yanlısı
    "a haber": "İktidar Yanlısı",
    "ahaber": "İktidar Yanlısı",
    "yeni şafak": "İktidar Yanlısı",
    "yenisafak.com": "İktidar Yanlısı",
    "sabah": "İktidar Yanlısı",
    "türkiye gazetesi": "İktidar Yanlısı",
    "akşam": "İktidar Yanlısı",
    "aksam.com.tr": "İktidar Yanlısı",
    "star - haberler": "İktidar Yanlısı",
    "star": "İktidar Yanlısı",
    "ülke tv": "İktidar Yanlısı",
    "diriliş postası": "İktidar Yanlısı",
    "türkgün": "İktidar Yanlısı",
    "superhaber": "İktidar Yanlısı",

    # Muhalif
    "sözcü": "Muhalif",
    "sozcu.com.tr": "Muhalif",
    "cumhuriyet": "Muhalif",
    "halk tv": "Muhalif",
    "t24": "Muhalif",
    "t24.com.tr": "Muhalif",
    "birgün": "Muhalif",
    "birgun.net": "Muhalif",
    "gazete duvar": "Muhalif",
    "odatv": "Muhalif",
    "karar": "Muhalif",
    "aydınlık": "Muhalif",
    "yeniçağ": "Muhalif",
    "evrensel": "Muhalif",
    "anka": "Muhalif",
}

def resolve_source_category(source_name: str, current_cat: str = None) -> str:
    clean = (source_name or "").lower().strip()
    if clean in MEDIA_OUTLET_CATEGORIES:
        return MEDIA_OUTLET_CATEGORIES[clean]
    for k, v in MEDIA_OUTLET_CATEGORIES.items():
        if k in clean or clean in k:
            return v
    if current_cat and current_cat != CATEGORIES["OTHER"]:
        return current_cat
    return CATEGORIES["OTHER"]

def create_app():
    templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
    app = Flask(
        __name__,
        template_folder=templates_dir,
        static_folder=static_dir
    )

    @app.route("/")
    def index():
        selected_date = request.args.get("date")
        today_str = datetime.now().strftime("%Y-%m-%d")
        
        if not selected_date:
            selected_date = today_str

        # Show all news by default as requested (or allow filter via ?filter=azerbaijan)
        filter_mode = request.args.get("filter", "all")  # 'all' or 'azerbaijan'
        only_relevant = (filter_mode == "azerbaijan")

        # Get language selection (TR or AZ)
        lang = request.args.get("lang", "tr").lower()
        if lang not in TRANSLATIONS:
            lang = "tr"
        
        t = TRANSLATIONS[lang]

        # Get news for selected date (SQL returns items pre-sorted by publish_date DESC at RAM speed)
        all_news = get_news_by_date(selected_date, only_relevant=only_relevant)

        # Calculate counts per source
        raw_source_counts = {}
        for n in all_news:
            s_name = n.get("source_name", "Bilinmeyen")
            raw_source_counts[s_name] = raw_source_counts.get(s_name, 0) + 1

        # Dynamic 10-Article Threshold:
        # If a platform has >= 10 articles -> shown as a dedicated sidebar tab.
        # If a platform has < 10 articles -> grouped into "Diğer Kaynaklar".
        prominent_sources = []
        prominent_source_names = set()
        other_count = 0
        az_gundemi_count = 0

        for s_name, count in sorted(raw_source_counts.items(), key=lambda x: x[1], reverse=True):
            if count >= 10:
                s_id = "".join(ch for ch in s_name.lower() if ch.isalnum())[:16]
                s_cat = resolve_source_category(s_name, None)
                prominent_sources.append({
                    "id": s_id,
                    "name": s_name,
                    "category": s_cat,
                    "count": count
                })
                prominent_source_names.add(s_name)
            else:
                other_count += count

        sidebar_sources = prominent_sources
        main_sources = prominent_sources
        extra_sources = []

        # Initialize country counts
        country_counts = {
            "azerbaycan": 0,
            "kazakistan": 0,
            "kirgizistan": 0,
            "ozbekistan": 0,
            "turkmenistan": 0,
            "kktc": 0
        }

        # Tag each news item
        for n in all_news:
            s_name = n.get("source_name", "Bilinmeyen")
            is_prominent = s_name in prominent_source_names
            
            # If not >= 10 articles -> mark as other source
            n["is_other_source"] = not is_prominent
            n["category"] = resolve_source_category(s_name, n.get("category"))
            
            if n.get("ilgili_mi") in (1, True, "1"):
                az_gundemi_count += 1
                cat = turkish_lower(n.get("ilgi_kategorisi") or "").strip()

                if "azerbaycan" in cat:
                    country_counts["azerbaycan"] += 1
                if "kazakistan" in cat:
                    country_counts["kazakistan"] += 1
                if "kırgızistan" in cat or "kirgizistan" in cat:
                    country_counts["kirgizistan"] += 1
                if "özbekistan" in cat or "ozbekistan" in cat:
                    country_counts["ozbekistan"] += 1
                if "türkmenistan" in cat or "turkmenistan" in cat:
                    country_counts["turkmenistan"] += 1
                if "kktc" in cat:
                    country_counts["kktc"] += 1

        # Group news by source — order by article count (highest first)
        items_by_source = {}
        other_items = []
        for n in all_news:
            if n.get("is_other_source"):
                other_items.append(n)
                continue
            s_name = n.get("source_name", "Bilinmeyen")
            items_by_source.setdefault(s_name, []).append(n)

        news_groups = []
        for src in sidebar_sources:
            articles = items_by_source.get(src["name"], [])
            if not articles:
                continue
            news_groups.append({
                "id": src["id"],
                "name": src["name"],
                "category": src["category"],
                "is_other": False,
                "articles": articles,
            })
        if other_items:
            news_groups.append({
                "id": "other",
                "name": t["other_sources"],
                "category": CATEGORIES["OTHER"],
                "is_other": True,
                "articles": other_items,
            })

        named_total = len(all_news)

        summary = get_daily_summary(selected_date)
        available_dates = get_available_dates()
        if today_str not in available_dates:
            available_dates.insert(0, today_str)

        pipeline_status = get_pipeline_status()

        return render_template(
            "index.html",
            selected_date=selected_date,
            today_str=today_str,
            available_dates=available_dates,
            filter_mode=filter_mode,
            news_items=all_news,
            news_groups=news_groups,
            main_sources=main_sources,
            extra_sources=extra_sources,
            sidebar_sources=sidebar_sources,
            other_count=other_count,
            az_gundemi_count=az_gundemi_count,
            country_counts=country_counts,
            total_displayed=named_total,
            summary=summary,
            pipeline_status=pipeline_status,
            llm_model=LLM_MODEL,
            schedule_time=SCHEDULE_TIME,
            enable_ai_summary=ENABLE_AI_SUMMARY,
            enable_llm_stage2=ENABLE_LLM_STAGE2,
            lang=lang,
            t=t
        )

    @app.route("/api/refresh", methods=["POST"])
    def refresh_news():
        status = get_pipeline_status()
        if status.get("is_running"):
            return jsonify({"status": "already_running", "message": "Tarama işlemi zaten devam ediyor."})
        
        trigger_manual_refresh()
        return jsonify({"status": "started", "message": "14 haber kaynağından tarama başlatıldı."})

    @app.route("/api/status", methods=["GET"])
    def pipeline_status_api():
        return jsonify(get_pipeline_status())

    @app.route("/api/summary", methods=["GET"])
    def daily_summary_api():
        date_str = request.args.get("date", datetime.now().strftime("%Y-%m-%d"))
        return jsonify(get_daily_summary(date_str))

    return app

if __name__ == "__main__":
    app = create_app()
    start_background_scheduler()
    app.run(host=HOST, port=PORT, debug=DEBUG)
