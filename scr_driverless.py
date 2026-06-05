import asyncio, random
from selenium_driverless import webdriver
from selenium_driverless.types.by import By
 
async def scrape_profile(user, max_videos=10):
    options = webdriver.ChromeOptions()
    
    async with webdriver.Chrome(options=options) as driver:
        await driver.get(f"https://www.tiktok.com/@{user}", wait_load=True)
        await asyncio.sleep(random.uniform(3, 6))
 
        # scroll para cargar más videos (carga perezosa)
        for _ in range(3):
            await driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(random.uniform(2, 4))
 
        # extraer los enlaces de videos
        items = await driver.find_elements(By.CSS_SELECTOR, "div[data-e2e='user-post-item'] a")
        videos = []
        for item in items[:max_videos]:
            href = await item.get_attribute("href")
            if href and "/video/" in href:
                video_id = href.split("/video/")[1].split("?")[0]
                videos.append({"id": video_id, "url": href})

        comments = []
        # for v in videos:
        #     comments += asyncio.run(scrape_com(driver, v["url"]))
                
        print(videos)

        return comments
    
async def scrape_com(driver, video_url, max_comentarios=50):
    await driver.get(video_url, wait_load=True)
    await asyncio.sleep(random.uniform(3, 5))
 
    # scroll dentro de la sección de comentarios para cargar más
    for _ in range(3):
        await driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(random.uniform(1.5, 3))
 
    items = await driver.find_elements(By.CSS_SELECTOR, "div[data-e2e='comment-level-1']")
    comentarios = []
 
    for item in items[:max_comentarios]:
        try:
            usuario_el = await item.find_element(By.CSS_SELECTOR, "[data-e2e='comment-username-1']")
            texto_el = await item.find_element(By.CSS_SELECTOR, "[data-e2e='comment-level-1'] p")
 
            comentarios.append({
                "user": await usuario_el.text,
                "comment": await texto_el.text,
                "video_id": video_url
            })
        except Exception:
            continue   # si falta algún campo, salta ese comentario
 
    return comentarios

asyncio.run(scrape_profile("clarocolombia")) 