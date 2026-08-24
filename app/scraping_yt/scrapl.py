import asyncio
import random
import re
import json
from functools import partial
from datetime import datetime, timedelta
from playwright.async_api import Page
from scrapling.fetchers import AsyncStealthySession
from dateutil.relativedelta import relativedelta

async def scrape_comments(search_text="", max_videos=1, type=1, scroll=10):
    watched = {}
    videos_info = {}
    if type == 1:
        url = f"https://www.youtube.com/@{search_text}/shorts"
    else:
        url = f"https://www.youtube.com/results?search_query={search_text}"
    try:
        async with AsyncStealthySession(headless=False) as session:     
            await session.fetch(
                url,
                network_idle=False,
                page_action=partial(
                    flujo_completo,
                    content_type=type,
                    videos_cant=max_videos,
                    scrolls=scroll,
                    watched=watched,
                    videos_info=videos_info
                ),
            )
            return list(watched.values()), list(videos_info.values())
    except Exception as e:
        print(f"Error en sesión de YouTube: {e}")
        return list(watched.values()), list(videos_info.values())

async def flujo_completo(page: Page, *, content_type, videos_cant, scrolls, watched, videos_info):

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
                            "date": transf_date(props.get("publishedTime", "")),
                            "likes": c.get("toolbar", {}).get("likeCountLiked", "0"),
                            "media": "",
                            "video_id": page.url
                        }
            except Exception:
                pass
        if "reel_item_watch?" in response.url:
            try:
                data = await response.json()
                extracted = get_comments_from_json(data)
                for c in extracted:
                    view_model = (
                    data["overlay"]["reelPlayerOverlayRenderer"]["playerOverlay"]
                    ["reelPlayerOverlayViewModel"])

                    metadata = view_model["metapanel"]["reelMetapanelViewModel"]["metadataItems"]

                    channel_item = next(
                        item["reelChannelBarViewModel"]
                        for item in metadata
                        if "reelChannelBarViewModel" in item
                    )
                    user = channel_item["channelName"]["content"]

                    buttons = (
                        view_model["actionBar"]["reelActionBarViewModel"]["buttonViewModels"]
                    )

                    like_item = next(
                        item["likeButtonViewModel"]
                        for item in buttons
                        if "likeButtonViewModel" in item
                    )
                    like_button = (
                        like_item["toggleButtonViewModel"]["toggleButtonViewModel"]
                        ["defaultButtonViewModel"]["buttonViewModel"]
                    )

                    likes_text = like_button.get("accessibilityText", "")
                    likes_match = re.search(r"([\d.,]+)\s*[“\"]?Me gusta", likes_text)
                    likes = int(likes_match.group(1).replace(",", "").replace(".", "")) if likes_match else 0

                    comment_button = next(
                        item["buttonViewModel"]
                        for item in buttons
                        if item.get("buttonViewModel", {}).get("iconName") == "SHORTS_COMMENT"
                    )
                    q_comments = int(comment_button.get("title", "0").replace(",", ""))
                    date = (
                        data["overlay"]["reelPlayerOverlayRenderer"]
                        ["reelPlayerHeaderSupportedRenderers"]
                        ["reelPlayerHeaderRenderer"]
                        ["timestampText"]["simpleText"])
                    if page.url and page.url not in videos_info:
                        videos_info[page.url] = {
                            "url": page.url,
                            "user": user,
                            "likes": likes,
                            "comments": q_comments,
                            "date": transf_date(date=date),
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

    for _ in range(videos_cant):
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

def transf_date(date: str):
    date_t = ""
    if "d" in date:
        date_t = datetime.now() - timedelta(days= int(re.search(r"\d+", date).group()))
        date_t = datetime.strptime(str(date_t).split(" ")[0], "%Y-%m-%d").strftime("%Y-%m-%d")
    elif "w" in date:
       date_t = datetime.now() - timedelta(weeks= int(re.search(r"\d+", date).group()))
       date_t = datetime.strptime(str(date_t).split(" ")[0], "%Y-%m-%d").strftime("%Y-%m-%d")
    elif  "m" in date:
        date_t = datetime.now() - relativedelta(months= int(re.search(r"\d+", date).group()))
        date_t = datetime.strptime(str(date_t).split(" ")[0], "%Y-%m-%d").strftime("%Y-%m-%d")
    else:
        date_t = datetime.now().strftime("%Y-%m-%d")
    return date_t
