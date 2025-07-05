import requests
import random

def get_proxies():
    urls = [
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
        "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-http.txt"
    ]
    proxies = []
    for url in urls:
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                proxies += r.text.strip().split('\n')
        except:
            continue
    return list(set(proxies))

def get_working_proxy():
    proxies = get_proxies()
    random.shuffle(proxies)
    for proxy in proxies:
        try:
            r = requests.get("http://httpbin.org/ip", proxies={"http": f"http://{proxy}"}, timeout=5)
            if r.status_code == 200:
                return f"http://{proxy}"
        except:
            continue
    return None
