import asyncio, random, re
from functools import partial
from playwright.async_api import Page
from scrapling.fetchers import AsyncStealthySession
from datetime import datetime, timedelta
from contextlib import suppress

CAPTCHA_SELECTOR = "div[id*='captcha']"

async def scrape_comments(search_text="", max_videos=100, type=1, scroll=10):
    watched = {}
    videos_info = {}
    
    url="https://www.tiktok.com/"
   
    try:   
        async with AsyncStealthySession(headless=False) as session:     
            await session.fetch(
                url,                  #URL
                network_idle=True,
                page_action=partial(
                    flujo_completo,
                    content_type=type,
                    search_content=search_text,
                    videos_cant=max_videos,
                    scrolls=scroll,
                    watched=watched,
                    videos_info=videos_info
                ),
            )
            return list(watched.values()), list(videos_info.values())
    except Exception as e:
        print(f"Error en sesión de TikTok: {e}")
        return list(watched.values()), list(videos_info.values())

async def flujo_completo(page: Page, *, content_type, search_content, videos_cant, scrolls, watched, videos_info):

    captcha_detected = asyncio.Event()
    stop_watcher = asyncio.Event()

    watcher = asyncio.create_task(
        watch_captcha(page, captcha_detected, stop_watcher)
    )

    await page.set_viewport_size({"width": 1280, "height": 720})
    await asyncio.sleep(random.uniform(1, 2))
    await handle_captcha(page, captcha_detected)
    if content_type==1:
        login_cont = await page.query_selector("div[id*='loginContainer']")
        search_button = await page.wait_for_selector("button[data-e2e='nav-search']")
        await asyncio.sleep(random.uniform(1, 2))
        login_cont = await page.query_selector("div[id*='loginContainer']")
        await search_button.click()
        login_cont = await page.query_selector("div[id*='loginContainer']")
        await asyncio.sleep(random.uniform(5, 10))
        login_cont = await page.query_selector("div[id*='loginContainer']")
        if login_cont:
            close_modal = await page.query_selector("div[data-e2e='modal-close-inner-button']")
            await close_modal.click()
            await asyncio.sleep(random.uniform(1, 3))
        await page.keyboard.type(search_content)
        await asyncio.sleep(random.uniform(0, 1))
        await page.keyboard.press("Enter")
        await asyncio.sleep(random.uniform(5, 10))

        for x in range(50):
            div_error = await page.query_selector_all("div[class*='DivContainer']:has(h2[data-e2e='search-error-title'])")
            await asyncio.sleep(random.uniform(0, 1))

            if div_error:    
                button = await page.query_selector("div[class*='DivContainer']:has(h2[data-e2e='search-error-title']) button")
                await button.hover()
                await asyncio.sleep(random.uniform(1, 2))
                await button.click()
            else:
                break
        tab_bar = await page.query_selector("[class*='tabbar__item-container']")
        divs = await tab_bar.query_selector_all(":scope > div")
        await divs[1].hover()
        await divs[1].click()
        await asyncio.sleep(random.uniform(2, 4))
        list_us = await page.query_selector_all("[class*='DivPanelContainer'] a")
        await list_us[0].click()
        await asyncio.sleep(random.uniform(1, 2))
        await page.wait_for_selector("div[data-e2e='user-post-item']")
        first_video = await page.query_selector("div[data-e2e='user-post-item'] a")
        await asyncio.sleep(random.uniform(1, 3))

        if not first_video:
            return page
        await first_video.click()
        await asyncio.sleep(random.uniform(1, 3))
    else:
        search_button = await page.wait_for_selector("button[data-e2e='nav-search']")
        await asyncio.sleep(random.uniform(1, 2))
        await search_button.click()
        await asyncio.sleep(random.uniform(1, 2))
        await page.keyboard.type(search_content)
        await asyncio.sleep(random.uniform(0, 1))
        await page.keyboard.press("Enter")
        await asyncio.sleep(random.uniform(2, 5))

        for x in range(50):
            div_error = await page.query_selector_all("div[class*='DivContainer']:has(h2[data-e2e='search-error-title'])")
            await asyncio.sleep(random.uniform(0, 1))

            if div_error:    
                button = await page.query_selector("div[class*='DivContainer']:has(h2[data-e2e='search-error-title']) button")
                await button.hover()
                await asyncio.sleep(random.uniform(1, 2))
                await button.click()
            else:
                break
        first_video = await page.query_selector("div[data-e2e='search_top-item'] a")
        await asyncio.sleep(random.uniform(1, 3))

        if not first_video:
            return page
        await first_video.click()
        await asyncio.sleep(random.uniform(1, 3))
    for _ in range(videos_cant):
        await handle_captcha(page, captcha_detected)
        video_id = page.url
        sc_com = True
        len_watched = len(watched)
        try_count = 0
        scroll_count = 0
        await asyncio.sleep(random.uniform(5, 10))
        #vista modo cine, cambia el DOM
        cine_view = False
        cinema_elm = await page.query_selector_all("div[class*='CinemaMode']")

        if cinema_elm:
            cine_view = True
        if cine_view:
            user_video = await page.query_selector("div[class*='CreatorInfo'] a")
            likes_video = await page.query_selector("[data-e2e*='like-count']")
            q_comments = await page.query_selector("[data-e2e*='comment-count']")
            date_video = await page.query_selector("div[class*='CreatorInfo'] span")
            date = transf_date(await date_video.inner_text(), True) if date_video else ""
        else:
            user_video = await page.query_selector("a[data-e2e='browse-user-avatar']")
            likes_video = await page.query_selector("[data-e2e='browse-like-count']")
            q_comments = await page.query_selector("[data-e2e='browse-comment-count']")
            date_video = await page.query_selector_all("div[data-cinema-mode-player-root='true'] span")
            date = transf_date(await date_video[2].inner_text()) if len(date_video) > 2 else ""
        
        if video_id and video_id not in videos_info:
            videos_info[video_id] = {
                "url": video_id,
                "user": await user_video.get_attribute("href") if user_video else "",
                "likes": await likes_video.inner_text() if likes_video else "",
                "comments": await q_comments.inner_text() if q_comments else "",
                "date": date
            }
        while sc_com:
            await handle_captcha(page, captcha_detected)
            if cine_view:
                elements = await page.query_selector_all("div[class*='DivCommentObjectWrapper']")
            else:
                
                elements = await page.query_selector_all("div[data-comment-ui-enabled='true']")
            for el in elements:
                
                try:
                    
                    if cine_view:
                        user_key = await el.query_selector("[class*='DivAvatarWrapper']")
                        # user_key = await user_key.get_attribute("href")if user else ""
                        cid = video_id
                        print(await user_key+" llave")
                        
                    else:    
                        cid = await el.get_attribute("id")
                    
                    if not cid or cid in watched:
                        continue
                    print(cid)
                    if cine_view:
                        user = await el.query_selector("[class*='DivAvatarWrapper'] a")
                        # text = await el.query_selector("[data-e2e='comment-level-1'] span")
                        # date = await el.query_selector("[class*='DivCommentSubContentWrapper'] span")
                        # likes = await el.query_selector("[class*='DivLikeContainer'] span")
                    else:
                        user = await el.query_selector("[data-e2e='comment-avatar-1']")
                        text = await el.query_selector("[data-e2e='comment-level-1']")
                        date = await el.query_selector("[data-e2e='comment-time-1']")
                        likes = await el.query_selector("[data-e2e='comment-like-count']")
                    img = await el.query_selector("[data-e2e='comment-thumbnail']")
                    watched[cid] = {
                    "user": await user.get_attribute("href")if user else "",
                    "comment": await text.inner_text() if text else "",
                    "date": transf_date(await date.inner_text()) if date else "",
                    "likes": await likes.inner_text() if likes else "",
                    "media": await img.get_attribute("src") if img else "",
                    "video_id":  video_id
                    }
                    
                except Exception as e:
                    continue
            await asyncio.sleep(random.uniform(5, 8))
            if elements:
                try:
                    await elements[-1].scroll_into_view_if_needed()                    
                except:
                    continue

            if len_watched == len(watched):
                try_count += 1
                
                if try_count > 5:
                    sc_com = False
            else:
                try_count = 0
                len_watched = len(watched)
            
            if scroll_count > scrolls:
                sc_com = False
            scroll_count += 1
        #elem_com = await page.query_selector("button[data-e2e='arrow-right']")
        await page.keyboard.press("ArrowDown")
        await asyncio.sleep(random.uniform(5, 8))
    stop_watcher.set()
    watcher.cancel()

    with suppress(asyncio.CancelledError):
        await watcher

    return page

def transf_date(date: str, cine=False):
    date_t = ""
    if cine:
        date = date.split()[1]
    if "d" in date:
        date_t = datetime.now() - timedelta(days= int(re.search(r"\d+", date).group()))
        date_t = datetime.strptime(str(date_t).split(" ")[0], "%Y-%m-%d").strftime("%Y-%m-%d")
    elif "w" in date:
        date_t = datetime.now() - timedelta(weeks= int(re.search(r"\d+", date).group()))
        date_t = datetime.strptime(str(date_t).split(" ")[0], "%Y-%m-%d").strftime("%Y-%m-%d")
    elif date.count("-") == 1:
        month = date.split("-")[1]
        day = date.split("-")[0]
        
        if int(month) < 10:
            month = "0"+month
        if int(day) < 10:
            day = "0"+day
        date_t = f"{datetime.now().year}-{month}-{day}"
    elif date.count("-") > 1:
        date_t = datetime.strptime(date, "%Y-%d-%m").strftime("%Y-%m-%d")
    else:
        date_t = datetime.now().strftime("%Y-%m-%d")
    return date_t

async def watch_captcha(page:Page, captcha_detected, stop_watcher):
    while not stop_watcher.is_set():
        try:
            if await page.query_selector(CAPTCHA_SELECTOR):
                captcha_detected.set()

            await asyncio.sleep(10)
        except Exception:
            return


async def wait_until_captcha_disappears(page:Page):
    while await page.query_selector(CAPTCHA_SELECTOR):
        await asyncio.sleep(1)

async def handle_captcha(page:Page, captcha_detected, timeout_seconds=300):
    if not captcha_detected.is_set():
        return
    print("captcha")
    checks = timeout_seconds // 30

    for _ in range(checks):
        await asyncio.sleep(20)

        captcha = await page.query_selector(CAPTCHA_SELECTOR)
        if not captcha:
            captcha_detected.clear()
            return

    raise TimeoutError("El CAPTCHA sigue activo después de 5 minutos.")
