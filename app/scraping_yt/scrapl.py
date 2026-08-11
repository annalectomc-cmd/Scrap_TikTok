import asyncio
import random
import re
import json
from datetime import datetime, timedelta
from playwright.async_api import Page
from scrapling.fetchers import AsyncStealthySession

comments = []
videos_cant = 0
content_type = 1
scrolls = 1
search_content = ""
watched = {}

async def scrape_comments(search_text="", max_videos=1, type=1, scroll=10):
    global videos_cant, content_type, search_content, scrolls, comments, watched
    search_content = search_text 
    content_type = type
    videos_cant = max_videos
    scrolls = scroll
    comments = []
    watched = {}

    if type == 1:
        url = f"https://www.youtube.com/@{search_text}/shorts"
    else:
        url = f"https://www.youtube.com/results?search_query={search_text}"
   
    try:
        async with AsyncStealthySession(headless=False) as session:     
            page = await session.fetch(
                url,
                network_idle=False,
                page_action=flujo_completo,
            )
            return comments
    except Exception as e:
        print(f"Error en sesión de YouTube: {e}")
        return list(watched.values())

async def flujo_completo(page: Page):
    global comments, content_type, search_content, watched
    comments = []
    watched = {}

    # Interceptamos las respuestas de red para extraer comentarios directamente de los JSON de YouTube
    async def handle_response(response):
        if "browse?prettyPrint=false" in response.url or "next?prettyPrint=false" in response.url:
            try:
                data = await response.json()
                extracted = get_comments_from_json(data)
                for c in extracted:
                    props = c.get("commentEntityPayload", {}).get("properties", {})
                    cid = props.get("commentId")
                    if cid and cid not in watched:
                        watched[cid] = {
                            "user": props.get("authorButtonA11y", ""),
                            "comment": props.get("content", {}).get("content", ""),
                            "date": props.get("publishedTime", ""),
                            "likes": c.get("toolbar", {}).get("likeCountLiked", "0"),
                            "media": "",
                            "video_id": page.url
                        }
            except Exception:
                pass

    page.on("response", handle_response)
    
    await page.set_viewport_size({"width": 1280, "height": 720})
    await asyncio.sleep(random.uniform(2, 4))
    
    try:
        await page.wait_for_selector("a[href*='/shorts/']", timeout=15000)
    except Exception:
        print("No se encontraron elementos Shorts en la página.")
        return page

    first_video = await page.query_selector_all("a[href*='/shorts/']")
    if not first_video:
        return page

    target_video = first_video[1] if len(first_video) > 1 else first_video[0]
    await target_video.click()
    await asyncio.sleep(random.uniform(2, 4))

    # Abrir panel de comentarios
    elem_com_icon = await page.query_selector("button[aria-label*='comments'], button[aria-label*='Comentarios']")
    if elem_com_icon:
        try:
            await elem_com_icon.click()
            await asyncio.sleep(2)
        except Exception:
            pass

    for i in range(0, videos_cant):
        sc_com = True
        len_watched = len(watched)
        try_count = 0
        scroll_count = 0

        while sc_com:
            await asyncio.sleep(random.uniform(1.5, 2.5))
            
            # Scroll en el contenedor
            scroll_el = await page.query_selector_all("ytd-comment-thread-renderer[class*='ytd-item-section-renderer']")
            if scroll_el:
                try:
                    await scroll_el[-1].scroll_into_view_if_needed()
                except Exception:
                    pass

            await page.keyboard.press("PageDown")

            if len_watched == len(watched):
                try_count += 1
                if try_count > 5:
                    sc_com = False
            else:
                try_count = 0
                len_watched = len(watched)
            
            if scroll_count >= scrolls:
                sc_com = False
            
            scroll_count += 1

        # Siguiente video
        await page.keyboard.press("ArrowDown")
        await asyncio.sleep(random.uniform(3, 5))

    comments = list(watched.values())
    return page

def get_comments_from_json(obj):
    found = []
    def walk(node):
        if isinstance(node, dict):
            if "commentEntityPayload" in node:
                found.append(node)
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)
    walk(obj)
    return found