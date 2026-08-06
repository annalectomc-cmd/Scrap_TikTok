import asyncio, random, re
from playwright.async_api import Page
from scrapling.fetchers import AsyncStealthySession
from datetime import datetime, timedelta

comments = []
videos_cant = 0
content_type = 1
scrolls = 1
search_content = ""

async def scrape_comments(search_text="", max_videos=1, type=1, scroll=10):
    global videos_cant
    global content_type
    global search_content
    global scrolls
    search_content = search_text 
    content_type = type
    videos_cant = max_videos
    scrolls = scroll
    url = "https://www.youtube.com/results?search_query="+search_text
   
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
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        first_video = await page.query_selector_all("a[href*='/shorts/']")
        await asyncio.sleep(random.uniform(1, 3))
        if not first_video:
            return page
        await first_video[1].click()
        await asyncio.sleep(random.uniform(1, 3))
        elem_com_icon = await page.query_selector("button[aria-label*='comments']")

        if elem_com_icon:
            await elem_com_icon.click()
    watched = {}

    for i in range(0, videos_cant):
        video_id = page.url
        sc_com = True
        len_watched = len(watched)
        try_count = 0
        scroll_count = 0
        await asyncio.sleep(random.uniform(1, 5))
        

        while sc_com:
            await asyncio.sleep(random.uniform(1, 2))
            scroll_el = await page.query_selector_all("ytd-comment-thread-renderer[class*='ytd-item-section-renderer']")
            try:
                async with page.expect_response(
                lambda r: "browse?prettyPrint=false" in r.url
                ) as response_info:
                    await scroll_el[-1].scroll_into_view_if_needed()
                response = await response_info.value
                data = await response.json()
                comments_el = get_comments(data)
                print(len(comments_el))
            except:
                comments_el = []

            for c in comments_el:
                cid = c["commentEntityPayload"]["properties"]["commentId"]

                if not cid or cid in watched:
                    continue
                watched[cid] = {
                "user": c["commentEntityPayload"]["properties"]["authorButtonA11y"],
                "comment": c["commentEntityPayload"]["properties"]["content"]["content"],
                "date": c["commentEntityPayload"]["properties"]["publishedTime"],
                "likes": c["commentEntityPayload"]["toolbar"]["likeCountLiked"],
                "media": "",
                "video_id":  video_id
                }

                print(watched[cid])
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
        elem_com = await page.query_selector("button[aria-label='Next video']")
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

async def handle_request(request):
            if "browse?prettyPrint=false" in request.url:
                print(request.method)
                print(request.url)
                print(request.post_data)

def get_comments(obj):
    comments = []

    def walk(node):
        if isinstance(node, dict):
            if "commentEntityPayload" in node:
                comments.append(node)

            for value in node.values():
                walk(value)

        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(obj)
    return comments