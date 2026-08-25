import sys
import logging
from config import PORT, HOST, DEBUG, LLM_BASE_URL, LLM_MODEL, LLM_API_KEY, ENABLE_AI_SUMMARY, ENABLE_LLM_STAGE2
from scheduler import start_background_scheduler
from web.app import create_app

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("Main")

if __name__ == "__main__":
    logger.info("=================================================================")
    logger.info("  Azerbaycan Büyükelçiliği - Türkiye Medya Takip Sistemi")
    logger.info(f"  AI Özet / Yorumlama : {'Aktif' if ENABLE_AI_SUMMARY else 'Devre Dışı (ENABLE_AI_SUMMARY=False)'}")
    logger.info(f"  LLM Sınıflandırma   : {'Aktif' if ENABLE_LLM_STAGE2 else 'Devre Dışı (ENABLE_LLM_STAGE2=False)'}")
    if ENABLE_AI_SUMMARY or ENABLE_LLM_STAGE2:
        logger.info(f"  LLM Servisi         : {LLM_BASE_URL} (Model: {LLM_MODEL})")
        logger.info(f"  LLM API Key         : {'Ayarlı' if LLM_API_KEY else 'Eksik (Lütfen .env dosyasını kontrol edin)'}")
    logger.info("=================================================================")

    # Initialize DB schema
    from db import init_db
    init_db()

    # Start daily background scheduler (07:30)
    start_background_scheduler()

    # Start Flask Web App
    app = create_app()
    logger.info(f"Web Arayüzü Başlatılıyor: http://{HOST}:{PORT}")
    app.run(host=HOST, port=PORT, debug=DEBUG, use_reloader=False, threaded=True)
