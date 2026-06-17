import asyncio
import random
from scrapling.fetchers import AsyncStealthySession

comments = []
async def scrape_comments(perfil_url):
    
    async with AsyncStealthySession(headless=False) as session:
        page = await session.fetch(
            perfil_url,                  #URL
            network_idle=True,
            page_action=flujo_completo,  # flujo 
        )

        return comments       

async def flujo_completo(page):
    global comments
    await page.set_viewport_size({"width": 1680, "height": 1050})
    await page.wait_for_selector("div[data-e2e='user-post-item']")
    await asyncio.sleep(random.uniform(1, 3))
    first_video = await page.query_selector("div[data-e2e='user-post-item'] a")
    await asyncio.sleep(random.uniform(1, 3))

    if not first_video:
        return page
    
    await first_video.click()
    await asyncio.sleep(random.uniform(1, 3))
    watched = {}

    for i in range(2):
        video_id = page.url
        for i in range(2):
            elements = await page.query_selector_all("div[data-comment-ui-enabled='true']")
            
            for el in elements:
                cid = await el.get_attribute("id")

                if not cid or cid in watched:
                    continue
                user = await el.query_selector("[data-e2e='comment-username-1']")
                text = await el.query_selector("[data-e2e='comment-level-1']")
                watched[cid] = {
                    "user": await user.inner_text(),
                    "comment": await text.inner_text(),
                    "video_id":  video_id
                }
                
            await asyncio.sleep(random.uniform(6, 10))
            if elements:
                await elements[-1].scroll_into_view_if_needed()
            
        elem_com = await page.query_selector("button[data-e2e='arrow-right']")
        await elem_com.click()
        await asyncio.sleep(random.uniform(5, 10))
        
    comments = list(watched.values())
    return page
