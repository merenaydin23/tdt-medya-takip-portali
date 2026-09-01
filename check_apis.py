import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
import json
from config import LLM_BASE_URL, LLM_API_KEY, LLM_MODEL, SERPAPI_KEY, ENABLE_AI_SUMMARY, ENABLE_LLM_STAGE2, PORT, HOST

def check_all_apis():
    print("==================================================")
    print("             API SAĞLIK VE DURUM KONTROLÜ        ")
    print("==================================================")
    
    # 1. Flask Web REST API Endpoints
    base_url = f"http://{HOST}:{PORT}"
    endpoints = [
        ("Ana Sayfa (GET /)", f"{base_url}/", "GET", None),
        ("Azerbaycan Filtresi (GET /?filter=azerbaijan)", f"{base_url}/?filter=azerbaijan", "GET", None),
        ("Durum API (GET /api/status)", f"{base_url}/api/status", "GET", None),
        ("Günlük Özet API (GET /api/summary)", f"{base_url}/api/summary", "GET", None),
        ("Yenileme Tetikleyici (POST /api/refresh)", f"{base_url}/api/refresh", "POST", {}),
    ]

    print("\n--- 1. WEB REST API UÇ NOKTALARI ---")
    for name, url, method, body in endpoints:
        try:
            if method == "GET":
                res = requests.get(url, timeout=5)
            else:
                res = requests.post(url, json=body, timeout=5)
            
            status = "CALISIYOR (200 OK)" if res.status_code == 200 else f"HATA ({res.status_code})"
            print(f"[{status}] {name}")
            if "api" in url:
                try:
                    data = res.json()
                    sample = str(data)[:100] + "..." if len(str(data)) > 100 else str(data)
                    print(f"   ↳ Yanit: {sample}")
                except:
                    pass
        except Exception as e:
            print(f"[ERISILEMEDI] {name} -> Hata: {e}")

    # 2. LLM / Yapay Zeka Servisi (Qwen)
    print("\n--- 2. LLM / YAPAY ZEKA API (Qwen-397B) ---")
    print(f"LLM Base URL : {LLM_BASE_URL}")
    print(f"LLM Model    : {LLM_MODEL}")
    print(f"Feature Toggles: ENABLE_AI_SUMMARY={ENABLE_AI_SUMMARY}, ENABLE_LLM_STAGE2={ENABLE_LLM_STAGE2}")
    
    if not LLM_API_KEY:
        print("INFO: LLM API Key tanimlanmamis (.env dosyasinda bos). Sistem yuksek hizli kural tabanli analizle calisiyor.")
    else:
        try:
            headers = {"Authorization": f"Bearer {LLM_API_KEY}", "Content-Type": "application/json"}
            payload = {
                "model": LLM_MODEL,
                "messages": [{"role": "user", "content": "Merhaba, test mesaji."}],
                "max_tokens": 20
            }
            llm_res = requests.post(f"{LLM_BASE_URL}/chat/completions", headers=headers, json=payload, timeout=10)
            if llm_res.status_code == 200:
                print("CALISIYOR (200 OK): LLM API baglandi ve yanit verdi!")
                print(f"   ↳ LLM Yaniti: {llm_res.json().get('choices', [{}])[0].get('message', {}).get('content', '').strip()}")
            else:
                print(f"UYARI: LLM API Durum Kodu: {llm_res.status_code} -> {llm_res.text[:150]}")
        except Exception as e:
            print(f"HATA: LLM API Baglanti Hatasi: {e}")

    # 3. SerpApi (Google News API)
    print("\n--- 3. SERPAPI (Google News Arama Motoru) ---")
    if not SERPAPI_KEY or SERPAPI_KEY == "buraya_serpapi_anahtarinizi_girin":
        print("INFO: SerpApi Key istege bagli. Sistem 23 yerel ve ulusal gazete adaptoru ile %100 canli veri cekiyor.")
    else:
        try:
            serp_res = requests.get(f"https://serpapi.com/search.json?q=Azerbaycan&api_key={SERPAPI_KEY}", timeout=8)
            if serp_res.status_code == 200:
                print("CALISIYOR (200 OK): SerpApi baglandi ve sonuc dondu!")
            else:
                print(f"UYARI: SerpApi Durum Kodu: {serp_res.status_code} ({serp_res.json().get('error', '')})")
        except Exception as e:
            print(f"HATA: SerpApi Baglanti Hatasi: {e}")

    print("\n==================================================")
    print("Kontrol Tamamlandi.")

if __name__ == "__main__":
    check_all_apis()
