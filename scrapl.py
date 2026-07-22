import asyncio, random, re
from playwright.async_api import Page
from scrapling.fetchers import AsyncStealthySession
from datetime import datetime, timedelta

comments = []
videos_cant = 0
content_type = 1
search_content = ""

async def scrape_comments(perfil_url="", max_videos=100, type=1):
    global videos_cant
    global content_type
    global search_content
    search_content = perfil_url 
    content_type = type
    videos_cant = max_videos
    url = ""

    if type==1:
        url="https://www.tiktok.com/@"+perfil_url
    else:
        url="https://www.tiktok.com"   
    async with AsyncStealthySession(headless=False) as session:     
        page = await session.fetch(
            url,                  #URL
            network_idle=True,
            page_action=flujo_completo,  # flujo 
        )
        return comments       

async def flujo_completo(page: Page):
    global comments
    global content_type
    global search_content
    comments = []
    
    await page.set_viewport_size({"width": 1280, "height": 720})
    
    for x in range(50):    
        if content_type==1:
            div_error = await page.query_selector_all("div[class*='DivErrorContainer']")
            await asyncio.sleep(random.uniform(0, 1))
            
            if div_error:    
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                boton = await page.query_selector("div[class*='DivErrorContainer'] button")
                await boton.hover()
                await boton.click()
        
    
    if content_type==1:
        await page.wait_for_selector("div[data-e2e='user-post-item']")
        await asyncio.sleep(random.uniform(1, 3))
        first_video = await page.query_selector("div[data-e2e='user-post-item'] a")
        await asyncio.sleep(random.uniform(1, 3))

        if not first_video:
            return page
        await first_video.click()
        await asyncio.sleep(random.uniform(1, 3))
    else:
        search_button = await page.wait_for_selector("button[data-e2e='nav-search']")
        await asyncio.sleep(random.uniform(1, 3))
        await search_button.click()
        await asyncio.sleep(random.uniform(1, 2))
        await page.keyboard.type(search_content)
        await page.keyboard.press("Enter")
        await asyncio.sleep(random.uniform(2, 5))
        for x in range(50):
            div_error = await page.query_selector_all("div[class*='DivContainer']:has(h2[data-e2e='search-error-title'])")
            await asyncio.sleep(random.uniform(0, 1))
            
            if div_error:    
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                button = await page.query_selector("div[class*='DivContainer']:has(h2[data-e2e='search-error-title']) button")
                await button.hover()
                await button.click()
        first_video = await page.query_selector("div[data-e2e='search_top-item'] a")
        await asyncio.sleep(random.uniform(1, 3))

        if not first_video:
            return page
        await first_video.click()
        await asyncio.sleep(random.uniform(1, 3))
    watched = {}

    for i in range(0, videos_cant):
        video_id = page.url
        sc_com = True
        len_watched = len(watched)
        try_count = 0
        scroll_count = 0
        while sc_com:
            cine_view = False
            elem_com_icon = await page.query_selector_all("button[aria-label*='comentario']")
            
            if elem_com_icon:
                elem_com_icon.click()
                await asyncio.sleep(random.uniform(1, 5))
                cine_view = True
            elements = await page.query_selector_all("div[data-comment-ui-enabled='true']")
            
            if not elements:
                elements = await page.query_selector_all("div[class*='DivCommentObjectWrapper']")
            
            for el in elements:
                try:
                    cid = await el.get_attribute("id")
                    
                    if not cid or cid in watched:
                        continue

                    if cine_view:
                        user = await el.query_selector("[class*='DivAvatarWrapper'] a")
                        text = await el.query_selector("[data-e2e='comment-level-1'] span")
                        date = await el.query_selector("[class*='DivCommentSubContentWrapper'] span")
                        likes = await el.query_selector("[class*='DivLikeContainer'] span")
                    
                    else:
                        user = await el.query_selector("[data-e2e='comment-avatar-1']")
                        text = await el.query_selector("[data-e2e='comment-level-1']")
                        date = await el.query_selector("[data-e2e='comment-time-1']")
                        likes = await el.query_selector("[data-e2e='comment-like-count']")
                    img = await el.query_selector("[data-e2e='comment-thumbnail']")
                    watched[cid] = {
                    "user": await user.get_attribute("href"),
                    "comment": await text.inner_text(),
                    "date": transf_date(await date.inner_text()),
                    "likes": await likes.inner_text() if likes else "",
                    "media": await img.get_attribute("src") if img else "",
                    "video_id":  video_id
                    }
                except Exception as e:
                    print(e)
                    continue
            await asyncio.sleep(5, 10)

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
            
            if scroll_count > 10:
                sc_com = False
            scroll_count += 1
        elem_com = await page.query_selector("button[data-e2e='arrow-right']")
        await elem_com.click()
        await asyncio.sleep(random.uniform(5, 10))
    comments = list(watched.values())
    return page

def transf_date(date: str):
    date_t = ""
    if "d" in date:
        date_t = datetime.now() - timedelta(days= int(re.search(r"\d+", date).group()))
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