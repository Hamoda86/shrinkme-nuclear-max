import time
import threading
import random
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from proxy_scraper import get_working_proxy
from twocaptcha import TwoCaptcha
import os

# === إعدادات ===
TARGET_URL = "https://shrinkme.ink/KUZP"
TWO_CAPTCHA_API = "0a88f59668933a935f01996bd1624450"
CONCURRENT_VISITS = 5

def stealth_sync(page):
    page.evaluate("""
        () => {
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            window.chrome = { runtime: {} };
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3]});
        }
    """)

def close_popups(page):
    try:
        selectors = ["div.popup-close", "button.close", ".modal-close", "div#popup-ad"]
        for selector in selectors:
            elements = page.query_selector_all(selector)
            for el in elements:
                try:
                    el.click()
                    page.wait_for_timeout(500)
                except:
                    continue
    except Exception:
        pass

def solve_recaptcha(solver, site_key, url):
    try:
        print("🔐 reCAPTCHA ...")
        captcha_id = solver.recaptcha(sitekey=site_key, url=url)
        result = solver.get_result(captcha_id)
        return result.get('code')
    except Exception as e:
        print("❌ CAPTCHA Error:", e)
        return None

def log_visit(status):
    os.makedirs("logs", exist_ok=True)
    with open("logs/visits.log", "a") as f:
        f.write(f"[{time.ctime()}] {status}\n")

def visit_loop():
    solver = TwoCaptcha(TWO_CAPTCHA_API)
    with sync_playwright() as p:
        while True:
            proxy = get_working_proxy()
            print("🌐 استخدام بروكسي:", proxy)

            try:
                browser = p.chromium.launch(headless=True, proxy={"server": proxy})
                context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)...")
                page = context.new_page()

                stealth_sync(page)
                page.goto(TARGET_URL, timeout=60000)
                close_popups(page)

                page.mouse.move(100, 100)
                page.mouse.click(200, 200)
                page.keyboard.press("Tab")
                page.wait_for_timeout(random.randint(2000, 4000))

                recaptcha_frame = next((f for f in page.frames if "recaptcha" in f.url), None)
                if recaptcha_frame:
                    try:
                        site_key = page.eval_on_selector(".g-recaptcha", "el => el.getAttribute('data-sitekey')")
                        token = solve_recaptcha(solver, site_key, TARGET_URL)
                        if token:
                            page.evaluate(f'document.getElementById("g-recaptcha-response").innerHTML="{token}";')
                            page.wait_for_timeout(3000)
                    except:
                        print("⚠️ لا يمكن جلب sitekey")

                for btn in page.query_selector_all("a, button"):
                    try:
                        text = btn.inner_text().lower()
                        if any(k in text for k in ["skip", "get link", "continue"]):
                            btn.click()
                            break
                    except:
                        continue

                print("✅ زيارة مكتملة")
                log_visit("✅ زيارة ناجحة")
                page.wait_for_timeout(4000)

            except PlaywrightTimeoutError:
                print("🕒 مهلة انتهت")
                log_visit("❌ مهلة انتهت")
            except Exception as e:
                print("❌ خطأ:", e)
                log_visit(f"❌ خطأ: {e}")
            finally:
                try:
                    browser.close()
                except:
                    pass
                time.sleep(random.randint(5, 10))

# === تشغيل الجلسات ===
if __name__ == "__main__":
    print("🚀 بدء السكربت النووي بـ", CONCURRENT_VISITS, "جلسة...")
    for _ in range(CONCURRENT_VISITS):
        threading.Thread(target=visit_loop, daemon=True).start()
    while True:
        time.sleep(60)
