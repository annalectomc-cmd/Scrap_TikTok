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
    comments = []
    await page.set_viewport_size({"width": 1280, "height": 720})
    
    for x in range(50):    
        div_error = await page.query_selector_all("div[class*='DivErrorContainer']")
        await asyncio.sleep(random.uniform(0, 1))
        
        if div_error:    
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            boton = await page.query_selector("div[class*='DivErrorContainer'] button")
            await boton.hover()
            await boton.click()
    await page.wait_for_selector("div[data-e2e='user-post-item']")
    await asyncio.sleep(random.uniform(1, 3))
    first_video = await page.query_selector("div[data-e2e='user-post-item'] a")
    await asyncio.sleep(random.uniform(1, 3))

    if not first_video:
        return page
    await first_video.click()
    await asyncio.sleep(random.uniform(1, 3))
    watched = {}

    for i in range(9):
        video_id = page.url

        for i in range(19):
            elem_com_icon = await page.query_selector_all("button[aria-label*='comentario']")
            
            if elem_com_icon:
                elem_com_icon.click()
                await asyncio.sleep(random.uniform(1, 5))
            elements = await page.query_selector_all("div[data-comment-ui-enabled='true']")
            
            if not elements:
                elements = await page.query_selector_all("div[data-testid='cinema-side-panel-comment-row']")
            
            for el in elements:
                try:
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

                except Exception:
                    continue
            await asyncio.sleep(5, 10)

            if elements:

                try:
                    await elements[-1].scroll_into_view_if_needed()

                except:
                    continue
        elem_com = await page.query_selector("button[data-e2e='arrow-right']")
        await elem_com.click()
        await asyncio.sleep(random.uniform(5, 10))
    comments = list(watched.values())
    return page
