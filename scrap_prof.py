import asyncio
import random
import os
from playwright.async_api import async_playwright
import json
from TikTokApi import TikTokApi
ms_token = os.getenv("MSTOKEN")

async def scrape_tiktok_videos(url):
    #async with async_playwright() as p:
    async with TikTokApi() as api:

        videos = []
        try:
            await api.create_sessions(
                ms_tokens=[ms_token],
                num_sessions=1,
                sleep_after=3,        # pausa tras crear sesión
                headless=False, 
            )
        
            user = api.user("tigo.colombia")
            #user_data = await user.info()
            await asyncio.sleep(random.uniform(5,20))
        
        
            async for video in user.videos(count=2):
                print(video.as_dict["id"])
                videos.append(video)
                await asyncio.sleep(random.uniform(5,20))    
        
        
        except Exception as e:
            print(e)
            return videos
        # context = await p.firefox.launch_persistent_context(
        # user_data_dir=os.getenv("URLFIREFOX"),
        # headless=False,
        # viewport={"width": 1280, "height": 800},
        # locale="es-CO",
        # timezone_id="America/Bogota",
        # )
       
        # page = await context.new_page()

        # # ocultar webdriver
        # await page.add_init_script("""
        #     Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        # """)

        # # Cargar cookies del archivo
        # with open("tiktok_cookies.json", "r") as f:
        #     cookies = json.load(f)
        
        # print(f"Abriendo {url}")
        # await page.goto(url, wait_until="networkidle")
        
        # await page.context.add_cookies(cookies)

        # await asyncio.sleep(random.uniform(2,10))

        # # aceptar cookies si aparece
        # try:
        #     await page.click("text=Accept all", timeout=5000)
        #     await asyncio.sleep(random.uniform(2,10))
        # except:
        #     pass

        # videos = []
        
        # async def handle_response(response):
        #     try:
        #         if "post/item_list" in response.url:
        #             data = await response.json()
        #             videos_data = data.get("itemList", [])
        #             for c in videos_data:
        #                 videos.append({
        #                     "id": c.get("id", "N/A")
        #                 })
        #             print(f"Capturados {len(videos_data)}")
        #     except:
        #         pass

        # page.on("response", handle_response)

        # await asyncio.sleep(random.uniform(2,10))
            
        # await context.close()
        return videos