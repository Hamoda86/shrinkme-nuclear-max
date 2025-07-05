import time
import threading
import random
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from twocaptcha import TwoCaptcha
import os

TARGET_URL = "https://shrinkme.ink/KUZP"
TWO_CAPTCHA_API = "0a88f59668933a935f01996bd1624450"
CONCURRENT_VISITS = 10
MAX_PROXY_ATTEMPTS = 1  # ما في بروكسي، تجربة واحدة كافية

def stealth_sync(page):
    page.evaluate("""
        () => {
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            window.chrome = { runtime: {} };
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3]});
        }
    """)

def random_user_action(page):
    width, height = page.viewport_size["width"], page.viewport_size["height"]
    for _ in range(random.randint(2, 5)):
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        page.mouse.move(x, y, steps=random.randint(5, 15))
        page.wait_for_timeout(random.randint(300, 700))
    page.evaluate(f"window.scrollTo(0, {random.randint(100, height)});")
    page.wait_for_timeout(random.randint(500, 1500))

def close_popups(page):
    try:
        selectors = ["div.popup-close", "button.close", ".modal-close", "div#popup-ad"]
        for selector in selectors:
            elements = page.query_selector_all(selector)
            for el in elements:
                try:
                    el.click()
                    page.wait_for_timeout(random.randint(300, 700))
                except:
                    continue
    except:
        pass

def solve_recaptcha(solver, site_key, url):
    try:
        print("🔐 solving reCAPTCHA ...")
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

def try_ad_click(page):
    selectors = [
        "iframe", "a[href*='ad']", ".adsbygoogle", ".sponsored", ".ad", "a[href*='click']"
    ]
    for selector in selectors:
        ads = page.query_selector_all(selector)
        for ad in ads:
            try:
                ad.scroll_into_view_if_needed()
                ad.click()
                print("💥 إعلان تم الضغط عليه!")
                log_visit("💥 ضغط إعلان ناجح")
                page.wait_for_timeout(random.randint(2000, 4000))
                return True
            except:
                continue
    print("⚠️ لم يتم العثور على إعلان قابل للضغط")
    return False

def visit_loop():
    solver = TwoCaptcha(TWO_CAPTCHA_API)
    with sync_playwright() as p:
        while True:
            for attempt in range(MAX_PROXY_ATTEMPTS):
                proxy = None  # لا يوجد بروكسي
                
                print(f"🌐 زيارة بدون بروكسي (محاولة {attempt + 1})")
                try:
                    browser = p.chromium.launch(headless=True)
                    context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)...")
                    page = context.new_page()

                    stealth_sync(page)
                    page.goto(TARGET_URL, timeout=60000)
                    close_popups(page)
                    random_user_action(page)

                    recaptcha_frame = next((f for f in page.frames if "recaptcha" in f.url), None)
                    if recaptcha_frame:
                        try:
                            site_key = page.eval_on_selector(".g-recaptcha", "el => el.getAttribute('data-sitekey')")
                            token = solve_recaptcha(solver, site_key, TARGET_URL)
                            if token:
                                page.evaluate(f'document.getElementById("g-recaptcha-response").innerHTML=\"{token}\";')
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

                    page.wait_for_timeout(random.randint(2000, 4000))
                    try_ad_click(page)

                    break  # نجاح الزيارة

                except Exception as e:
                    print(f"❌ خطأ: {e}")
                    log_visit(f"❌ خطأ: {e}")

                finally:
                    try:
                        browser.close()
                    except:
                        pass

            time.sleep(random.randint(5, 10))

if __name__ == "__main__":
    print("🚀 بدء السكربت بـ", CONCURRENT_VISITS, "جلسة بدون بروكسي...")
    for _ in range(CONCURRENT_VISITS):
        threading.Thread(target=visit_loop, daemon=True).start()
    while True:
        time.sleep(60)
