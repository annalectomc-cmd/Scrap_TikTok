import asyncio, random
from selenium_driverless import webdriver
from selenium_driverless.types.by import By
 
async def scrape_profile(user, max_videos=4):
    options = webdriver.ChromeOptions()
    
    async with webdriver.Chrome(options=options) as driver:

        await driver.get(f"https://www.tiktok.com/@{user}", wait_load=True)
        await asyncio.sleep(random.uniform(5, 10))
        # elem_search = await driver.find_element(By.CSS_SELECTOR, "div[data-e2e='nav-search']")
        # await elem_search.click()
        # await asyncio.sleep(random.uniform(2, 4))
        # texto = "user"
        # for letra in texto:
        #     await elem_search.send_keys(letra)
        #     await asyncio.sleep(random.uniform(0.05, 0.2))
        

        elem = await driver.find_element(By.CSS_SELECTOR, "div[data-e2e='user-post-item']")
        await elem.click()
        await asyncio.sleep(random.uniform(5, 10))
        comments = {}

        for i in range(max_videos):

            video_id = await driver.current_url

            for x in range(20):

            
                items = await driver.find_elements(By.CSS_SELECTOR, "div[data-comment-ui-enabled='true']")

                for item in items:           
                    try:
                        
                        cid = await item.get_attribute("id")

                        if not cid or cid in comments:
                            continue

                        user_el = await item.find_element(By.CSS_SELECTOR, "[data-e2e='comment-username-1']")
                        text_el = await item.find_element(By.CSS_SELECTOR, "[data-e2e='comment-level-1']")        
                        comments[cid] = {
                        "user": await user_el.text,
                        "comment": await text_el.text,
                        "video_id": video_id
                        }

                        await asyncio.sleep(random.uniform(1.5, 3))

                    except Exception:
                        continue   # si falta algún campo, salta ese comentario
                
                elem_scroll = await driver.find_elements(By.CSS_SELECTOR, "div[data-comment-ui-enabled='true']")
                for x in range(10):
                    await driver.execute_script("arguments[0].scrollIntoView();", elem_scroll[-1])
                    await asyncio.sleep(random.uniform(3, 6))

            elem_com = await driver.find_element(By.CSS_SELECTOR, "button[data-e2e='arrow-right']")
            await elem_com.click()
            await asyncio.sleep(random.uniform(5, 10))
        # async def on_response(params):
        #     try:
        #         resp = params.get("response", {})
        #         url = resp.get("url", "")
        #         if "/api/comment/list" in url:
        #             request_id = params.get("requestId")
        #             # pedir el cuerpo de la respuesta
        #             body = await driver.execute_cdp_cmd(
        #                 "Network.getResponseBody",
        #                 {"requestId": request_id}
        #             )
        #             data = json.loads(body["body"])
        #             comments.append(data)
        #     except Exception as e:
        #         print("error capturando:", e)

        # # activar red y suscribir el handler
        # await driver.execute_cdp_cmd("Network.enable", {})
        # driver.add_cdp_listener("Network.responseReceived", on_response)
        
        return list(comments.values())