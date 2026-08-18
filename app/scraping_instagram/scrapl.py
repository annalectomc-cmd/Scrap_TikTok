import asyncio, random, re, os
from playwright.async_api import Page
from scrapling.fetchers import AsyncStealthySession
from datetime import datetime, timedelta
from dotenv import load_dotenv

comments = []
videos_cant = 0
content_type = 1
scrolls = 1
search_content = ""

async def scrape_comments(perfil_url="", max_videos=100, type=1, scroll=10):
    global videos_cant
    global content_type
    global search_content
    global scrolls
    global comments

    search_content = perfil_url 
    content_type = type
    videos_cant = max_videos
    scrolls = scroll
    comments = []

    if type == 1:
        url = f"https://www.instagram.com/{perfil_url}/reels"
    else:
        url = f"https://www.instagram.com/explore/search/keyword/?q=%23{perfil_url}"
    load_dotenv()
    cookies = [
        {"name": "sessionid", "value": os.getenv("INSTAGRAM_SESSIONID"), "domain": ".instagram.com", "path": "/"},
        {"name": "csrftoken", "value": os.getenv("INSTAGRAM_CSRFTOKEN"), "domain": ".instagram.com", "path": "/"},
        {"name": "ds_user_id", "value": os.getenv("INSTAGRAM_USERID"), "domain": ".instagram.com", "path": "/"},
    ]

    async with AsyncStealthySession(headless=False) as session:   
        await session.context.add_cookies(cookies)  
        page = await session.fetch(
            url,                  # URL
            network_idle=True,
            page_action=flujo_completo,  # callback
        )
        return comments       



async def flujo_completo(page: Page):
    global comments
    global content_type
    global search_content
    global videos_cant
    global scrolls
    
    watched = {}
    # Interceptamos las respuestas de red para extraer comentarios directamente de los JSON de YouTube
    async def handle_response(response):
        if "comments/?" in response.url:
            try:
                data = await response.json()
                extracted = data.get("comments", {})
                
                for c in extracted:
                    cid = c.get("pk")
                    print(cid)
                    if cid and cid not in watched:
                        watched[cid] = {
                            "user": c.get("user", {}).get("username", ""),
                            "comment": c.get("text", ""),
                            "date": datetime.fromtimestamp(c.get("created_at", "")).strftime("%Y-%m-%d"),
                            "likes": c.get("comment_like_count", ""),
                            "media": "",
                            "video_id": page.url
                        }
                        print(watched[cid])
                                      
            except Exception as e:
                pass

    page.on("response", handle_response)
    await page.set_viewport_size({"width": 1280, "height": 720})
    await asyncio.sleep(random.uniform(2, 4))
    if content_type == 1:
        post_links = await page.query_selector_all("a[href*='/reel/']")
        if not post_links:
            try:
                await page.wait_for_selector("a[href*='/reel/']", timeout=5000)
                post_links = await page.query_selector_all("a[href*='/reel/']")
            except Exception:
                pass

        if not post_links:
            return page

        # Click on the first post link
        try:
            await post_links[1].click()
        except Exception:
            first_href = await post_links[1].get_attribute("href")
            if first_href:
                target_url = f"https://www.instagram.com/{first_href}" if first_href.startswith("/") else first_href
                await page.goto(target_url)
                
        await asyncio.sleep(random.uniform(2, 4))
    else:
        post_links = await page.query_selector_all("a[href*='/p/']")
        if not post_links:
            try:
                await page.wait_for_selector("a[href*='/p/']", timeout=5000)
                post_links = await page.query_selector_all("a[href*='/p/']")
            except Exception:
                pass

        if not post_links:
            return page

        # Click on the first post link
        try:
            await post_links[0].click()
        except Exception:
            first_href = await post_links[0].get_attribute("href")
            if first_href:
                target_url = f"https://www.instagram.com/{first_href}" if first_href.startswith("/") else first_href
                await page.goto(target_url)
                
        await asyncio.sleep(random.uniform(2, 4))

    for i in range(0, videos_cant):
        
        sc_com = True
        len_watched = len(watched)
        try_count = 0
        scroll_count = 0

        while sc_com:
            await asyncio.sleep(random.uniform(1.5, 2.5))
                        
            # Scroll en el contenedor
            scroll_el = await page.query_selector_all("li:has(div > button)")
            if scroll_el:
                try:
                    await asyncio.sleep(random.uniform(5, 10))
                    await scroll_el[-1].scroll_into_view_if_needed()
                    await asyncio.sleep(random.uniform(1, 2))
                    await scroll_el[-1].click()
                except Exception:
                    pass
            
            # if len_watched == len(watched):
            #     try_count += 1
            #     if try_count > 5:
            #         sc_com = False
            # else:
            #     try_count = 0
            #     len_watched = len(watched)
            
            scroll_count += 1

            if scroll_count >= scrolls-1:
                sc_com = False
            
        # Siguiente video
        next_button = await page.query_selector('button:has(svg[aria-label*="ext"])')
        await next_button.click()
        await asyncio.sleep(random.uniform(3, 5))

    comments = list(watched.values())
    print(comments)
    return page


def get_comments_from_json(obj):
    found = []
    def walk(node):
        if isinstance(node, dict):
            if "comments" in node:
                found.append(node)
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)
    walk(obj)
    return found

def transf_date(date: str):
    if not date:
        return datetime.now().strftime("%Y-%m-%d")
    date_str = str(date).strip()
    
    if "T" in date_str and "-" in date_str:
        return date_str.split("T")[0]
        
    now = datetime.now()
    
    match = re.search(r"(\d+)\s*([s|m|h|d|w|y])", date_str.lower())
    if match:
        val = int(match.group(1))
        unit = match.group(2)
        if unit == "d":
            date_t = now - timedelta(days=val)
        elif unit == "w":
            date_t = now - timedelta(weeks=val)
        elif unit == "h":
            date_t = now - timedelta(hours=val)
        elif unit == "m":
            date_t = now - timedelta(minutes=val)
        elif unit == "y":
            date_t = now - timedelta(days=365 * val)
        else:
            date_t = now
        return date_t.strftime("%Y-%m-%d")
        
    if "d" in date_str or "día" in date_str or "day" in date_str:
        num = re.search(r"\d+", date_str)
        if num:
            date_t = now - timedelta(days=int(num.group()))
            return date_t.strftime("%Y-%m-%d")
            
    if date_str.count("-") == 1:
        parts = date_str.split("-")
        day = parts[0].zfill(2)
        month = parts[1].zfill(2)
        return f"{now.year}-{month}-{day}"
    elif date_str.count("-") > 1:
        try:
            return datetime.strptime(date_str, "%Y-%d-%m").strftime("%Y-%m-%d")
        except Exception:
            try:
                return datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y-%m-%d")
            except Exception:
                pass
                
    return now.strftime("%Y-%m-%d")
