import asyncio, random, re
from playwright.async_api import Page
from scrapling.fetchers import AsyncStealthySession
from datetime import datetime, timedelta

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

    clean_profile = perfil_url.strip().strip("/")
    if clean_profile.startswith("http://") or clean_profile.startswith("https://"):
        url = clean_profile
    elif type == 1:
        url = f"https://www.instagram.com/{clean_profile}/"
    else:
        url = f"https://www.instagram.com/explore/tags/{clean_profile}/"

    async with AsyncStealthySession(headless=False) as session:     
        page = await session.fetch(
            url,                  # URL
            network_idle=True,
            page_action=flujo_completo,  # callback
        )
        return comments       

async def dismiss_popups(page: Page):
    # Cookie banners
    cookie_buttons = [
        "button:has-text('Decline optional cookies')",
        "button:has-text('Allow all cookies')",
        "button:has-text('Allow essential and optional cookies')",
        "button:has-text('Rechazar cookies opcionales')",
        "button:has-text('Permitir todas las cookies')",
        "button:has-text('Aceptar todas')",
        "button:has-text('Aceptar')",
        "button:has-text('Only allow essential cookies')"
    ]
    for sel in cookie_buttons:
        try:
            btn = await page.query_selector(sel)
            if btn and await btn.is_visible():
                await btn.click()
                await asyncio.sleep(1)
        except Exception:
            pass

    # Login / signup modal close buttons
    close_selectors = [
        "svg[aria-label='Close']",
        "svg[aria-label='Cerrar']",
        "button:has-text('Not Now')",
        "button:has-text('Ahora no')",
        "div[role='dialog'] button:has-text('Not Now')",
        "div[role='dialog'] svg[aria-label='Close']"
    ]
    for sel in close_selectors:
        try:
            btn = await page.query_selector(sel)
            if btn and await btn.is_visible():
                await btn.click()
                await asyncio.sleep(1)
        except Exception:
            pass

async def flujo_completo(page: Page):
    global comments
    global content_type
    global search_content
    global videos_cant
    global scrolls
    
    comments = []
    await page.set_viewport_size({"width": 1280, "height": 720})
    await asyncio.sleep(random.uniform(2, 4))
    await dismiss_popups(page)

    # Scroll down slightly to ensure post grids load
    await page.evaluate("window.scrollTo(0, 400)")
    await asyncio.sleep(random.uniform(1.5, 3.0))
    await dismiss_popups(page)

    post_links = await page.query_selector_all("a[href*='/p/'], a[href*='/reel/'], a[href*='/reels/']")
    if not post_links:
        try:
            await page.wait_for_selector("a[href*='/p/'], a[href*='/reel/']", timeout=5000)
            post_links = await page.query_selector_all("a[href*='/p/'], a[href*='/reel/'], a[href*='/reels/']")
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
            target_url = f"https://www.instagram.com{first_href}" if first_href.startswith("/") else first_href
            await page.goto(target_url)
            
    await asyncio.sleep(random.uniform(2, 4))
    watched = {}

    for i in range(0, videos_cant):
        await dismiss_popups(page)
        video_id = page.url
        sc_com = True
        len_watched = len(watched)
        try_count = 0
        scroll_count = 0

        while sc_com:
            await dismiss_popups(page)
            
            comment_elements = await page.query_selector_all(
                "div[role='dialog'] ul li, ul._a9ym > div > li, ul > div > li, div._a9zs, div[role='main'] ul li"
            )
            
            if not comment_elements:
                comment_elements = await page.query_selector_all("ul li:has(span)")
            
            for el in comment_elements:
                try:
                    user_el = await el.query_selector("a[href*='/']")
                    text_el = await el.query_selector("span._ap3a, div._a9zs, span[dir='auto']")
                    if not text_el:
                        text_el = await el.query_selector("span")
                    
                    if not user_el or not text_el:
                        continue
                    
                    user_href = await user_el.get_attribute("href") or ""
                    comment_text = await text_el.inner_text() or ""
                    
                    if not comment_text.strip() or "Reply" in comment_text or "Responder" in comment_text:
                        # Skip UI action words if captured alone
                        if comment_text.strip() in ["Reply", "Responder", "Like", "Me gusta"]:
                            continue

                    cid = f"{user_href}_{comment_text[:25]}"
                    if cid in watched:
                        continue

                    date_el = await el.query_selector("time")
                    raw_date = ""
                    if date_el:
                        raw_date = await date_el.get_attribute("datetime") or await date_el.inner_text()
                    
                    likes_el = await el.query_selector("span:has-text('like'), button span")
                    likes_text = await likes_el.inner_text() if likes_el else ""
                    
                    img_el = await el.query_selector("img")
                    img_src = await img_el.get_attribute("src") if img_el else ""

                    full_user_url = f"https://www.instagram.com{user_href}" if user_href.startswith("/") else user_href

                    watched[cid] = {
                        "user": full_user_url,
                        "comment": comment_text,
                        "date": transf_date(raw_date),
                        "likes": likes_text,
                        "media": img_src,
                        "video_id": video_id
                    }
                except Exception as e:
                    print(f"Error parsing comment item: {e}")
                    continue

            if comment_elements:
                try:
                    await comment_elements[-1].scroll_into_view_if_needed()
                except Exception:
                    pass

            if len_watched == len(watched):
                try_count += 1
                if try_count > 3:
                    sc_com = False
            else:
                try_count = 0
                len_watched = len(watched)

            if scroll_count >= scrolls:
                sc_com = False
                
            scroll_count += 1
            await asyncio.sleep(random.uniform(1.5, 2.5))

        # Move to next post
        next_button = await page.query_selector("svg[aria-label='Next'], svg[aria-label='Siguiente'], a:has(svg[aria-label='Next']), button:has(svg[aria-label='Next'])")
        if next_button:
            try:
                await next_button.click()
            except Exception:
                await page.keyboard.press("ArrowRight")
        else:
            await page.keyboard.press("ArrowRight")
        
        await asyncio.sleep(random.uniform(2.5, 4.0))

    comments = list(watched.values())
    return page

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