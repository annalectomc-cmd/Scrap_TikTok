import asyncio
import random
from scrapling.fetchers import AsyncStealthySession

async def scrape_comentarios(video_url, num_scrolls=1):
    vistos = {}

    async with AsyncStealthySession(headless=False, solve_cloudflare=False) as session:
        page = await session.fetch(video_url, network_idle=True, wait=5000)

        for i in range(num_scrolls):
            # leer comentarios cargados AHORA (antes de que el scroll los quite)
            items = page.css("div[data-comment-ui-enabled='true']")

            for item in items:
                cid = item.attrib.get("id")
                if not cid or cid in vistos:
                    continue

                usuario = item.css("[data-e2e='comment-username-1']::text").get()
                texto = item.css("[data-e2e='comment-level-1']::text").get()
                likes = item.css("[data-e2e='comment-like-count']::text").get()

                vistos[cid] = {
                    "id": cid,
                    "usuario": (usuario or "").strip(),
                    "texto": (texto or "").replace("[ステッカー]", "").strip(),
                    "likes": (likes or "0").strip(),
                }

            print(f"scroll {i+1}: {len(vistos)} comentarios acumulados")

            # scroll al último comentario para cargar el siguiente lote
            await session.execute_script(
                "document.querySelectorAll('div[data-comment-ui-enabled=\"true\"]');"
                "let els = document.querySelectorAll('div[data-comment-ui-enabled=\"true\"]');"
                "if (els.length) els[els.length-1].scrollIntoView();"
            )
            await asyncio.sleep(random.uniform(1.5, 3))

            # re-obtener el DOM actualizado tras el scroll
            #page = await session.get_page()   # según la API de tu versión

    return list(vistos.values())

if __name__ == "__main__":
    url = "https://www.tiktok.com/@apple/video/7650168947207146766"   # pon un video real
    comentarios = asyncio.run(scrape_comentarios(url))
    print(f"\nTOTAL: {len(comentarios)} comentarios")