# core/req_config.py
# HTTP request helper với proxy rotation và retry khi gặp 429
# Không dùng CloudFlare bypass vì metruyenchu.co không có CloudFlare

import time
import asyncio
import requests
import httpx

from core.config import MTC_HEADERS, get_next_proxy

# Backend rate limit: 100 req/min => khi 429 đợi 60s rồi thử lại
RATE_LIMIT_WAIT = 60  # giây


def proxy_get(url: str, headers: dict = None, timeout: int = 60, **kwargs) -> requests.Response:
    """
    Sync GET với proxy rotation.
    - Khi bị 429: đợi RATE_LIMIT_WAIT giây rồi thử lại (vô hạn số lần).
    - Khi lỗi mạng: đổi proxy và thử lại.
    """
    req_headers = {**MTC_HEADERS, **(headers or {})}

    while True:
        proxy = get_next_proxy()
        try:
            resp = requests.get(
                url,
                headers=req_headers,
                proxies=proxy,
                timeout=timeout,
                **kwargs
            )
            if resp.status_code == 429:
                print(f"  [proxy_get] 429 Rate Limit ({url[:60]}...). Đợi {RATE_LIMIT_WAIT}s...")
                time.sleep(RATE_LIMIT_WAIT)
                continue  # thử lại không giới hạn
            return resp
        except Exception as e:
            print(f"  [proxy_get] Lỗi ({url[:60]}): {e.__class__.__name__} - {e}")
            print(f"  [proxy_get] Thử lại sau 5s...")
            time.sleep(5)


def proxy_post(
    url: str,
    headers: dict = None,
    data=None,
    json_body=None,
    timeout: int = 60,
    use_proxy: bool = False,
    **kwargs,
) -> requests.Response:
    """
    Sync POST với tuỳ chọn proxy.
    - Dùng cho backend API (localhost:3000) -> use_proxy=False.
    - Dùng cho MTC site -> use_proxy=True.
    - Khi bị 429: đợi RATE_LIMIT_WAIT giây rồi thử lại (vô hạn số lần).
    """
    req_headers = {**MTC_HEADERS, **(headers or {})}
    proxy = get_next_proxy() if use_proxy else None

    while True:
        try:
            resp = requests.post(
                url,
                headers=req_headers,
                data=data,
                json=json_body,
                proxies=proxy,
                timeout=timeout,
                **kwargs
            )
            if resp.status_code == 429:
                print(f"  [proxy_post] 429 Rate Limit ({url[:60]}). Đợi {RATE_LIMIT_WAIT}s...")
                time.sleep(RATE_LIMIT_WAIT)
                if use_proxy:
                    proxy = get_next_proxy()
                continue
            return resp
        except Exception as e:
            print(f"  [proxy_post] Lỗi ({url[:60]}): {e.__class__.__name__} - {e}")
            print(f"  [proxy_post] Thử lại sau 5s...")
            time.sleep(5)
            if use_proxy:
                proxy = get_next_proxy()


async def proxy_get_async(
    url: str,
    headers: dict = None,
    timeout: int = 60,
    **kwargs,
) -> httpx.Response:
    """
    Async GET với proxy rotation.
    - Khi bị 429: đợi RATE_LIMIT_WAIT giây rồi thử lại (vô hạn số lần).
    - Khi lỗi mạng: đổi proxy và thử lại.
    """
    req_headers = {**MTC_HEADERS, **(headers or {})}

    while True:
        proxy = get_next_proxy()
        # httpx dùng proxy_url dạng string
        proxy_url = proxy["http"] if proxy else None

        try:
            async with httpx.AsyncClient(
                proxy=proxy_url,
                timeout=timeout,
                follow_redirects=True,
            ) as client:
                resp = await client.get(url, headers=req_headers, **kwargs)

            if resp.status_code == 429:
                print(f"  [async_get] 429 Rate Limit ({url[:60]}). Đợi {RATE_LIMIT_WAIT}s...")
                await asyncio.sleep(RATE_LIMIT_WAIT)
                continue
            return resp
        except Exception as e:
            print(f"  [async_get] Lỗi ({url[:60]}): {e.__class__.__name__} - {e}")
            print(f"  [async_get] Thử lại sau 5s...")
            await asyncio.sleep(5)


async def proxy_post_async(
    url: str,
    headers: dict = None,
    data=None,
    json_body=None,
    timeout: int = 60,
    use_proxy: bool = False,
    **kwargs,
) -> httpx.Response:
    """
    Async POST với tuỳ chọn proxy.
    use_proxy=False cho backend API (localhost:3000).
    use_proxy=True cho MTC site.
    """
    req_headers = {**MTC_HEADERS, **(headers or {})}

    while True:
        proxy = get_next_proxy() if use_proxy else None
        proxy_url = proxy["http"] if proxy else None

        try:
            async with httpx.AsyncClient(
                proxy=proxy_url,
                timeout=timeout,
                follow_redirects=True,
            ) as client:
                resp = await client.post(
                    url,
                    headers=req_headers,
                    data=data,
                    json=json_body,
                    **kwargs,
                )

            if resp.status_code == 429:
                print(f"  [async_post] 429 Rate Limit ({url[:60]}). Đợi {RATE_LIMIT_WAIT}s...")
                await asyncio.sleep(RATE_LIMIT_WAIT)
                continue
            return resp
        except Exception as e:
            print(f"  [async_post] Lỗi ({url[:60]}): {e.__class__.__name__} - {e}")
            print(f"  [async_post] Thử lại sau 5s...")
            await asyncio.sleep(5)
