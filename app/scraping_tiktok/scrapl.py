import asyncio, os, random, re
from functools import partial
from playwright.async_api import Page
from scrapling.fetchers import AsyncStealthySession
from datetime import datetime, timedelta
from contextlib import suppress

CAPTCHA_SELECTOR = "div[id*='captcha']"

# Selectores conocidos para el grid de videos de un perfil. TikTok no usa
# siempre exactamente el mismo data-e2e para todos los layouts (cuentas
# normales vs. verificadas/negocio a veces difieren un poco), así que
# probamos varios antes de rendirnos. Si en el futuro aparece un layout
# nuevo, basta con agregar el selector aquí.
PROFILE_VIDEO_CONTAINER_SELECTORS = [
    "div[data-e2e='user-post-item']",
    "[data-e2e='user-post-item-list'] > div",
]

PRIVATE_ACCOUNT_SELECTOR = "[data-e2e='user-private-title'], div[class*='PrivateTitle']"
LOGIN_WALL_SELECTOR = "div[id*='loginContainer']"
LOGIN_WALL_CLOSE_SELECTOR = "div[data-e2e='modal-close-inner-button']"

# TikTok a veces falla al traer los posts del perfil en su propio backend y
# muestra este estado de error genérico ("Something went wrong / Sorry about
# that! Please try again later.") con un botón de refresco, en vez del grid
# de videos. Esto no depende de nuestro selector: es TikTok fallando en su
# propia API interna. Lo detectamos por texto (las clases son hashes que
# cambian) y hacemos click en "Refresh" para reintentar.
PROFILE_LOAD_ERROR_SELECTOR = "text=Something went wrong"
PROFILE_LOAD_ERROR_REFRESH_BUTTON = "button:has-text('Refresh')"
MAX_PROFILE_LOAD_ERROR_RETRIES = 4

DEBUG_DIR = "debug"


def normalize_username(text: str) -> str:
    """
    Quita espacios, puntos, guiones y guiones bajos, y pasa a
    minúsculas. Sirve para comparar lo que el usuario escribió
    contra el href real del perfil, que puede tener puntuación
    distinta a la que se tipeó (p. ej. "tigo colombia" vs
    "/@tigo.colombia").
    """
    return re.sub(r"[\s_.\-]+", "", text or "").lower()


async def scrape_comments(search_text="", max_videos=100, type=1, scroll=10, captcha_callback=None):
    watched = {}
    videos_info = {}

    url = "https://www.tiktok.com/"

    try:
        async with AsyncStealthySession(headless=False) as session:
            await session.fetch(
                url,                  # URL
                network_idle=True,
                page_action=partial(
                    flujo_completo,
                    content_type=type,
                    search_content=search_text,
                    videos_cant=max_videos,
                    scrolls=scroll,
                    watched=watched,
                    videos_info=videos_info,
                    captcha_callback=captcha_callback,
                ),
            )
            return list(watched.values()), list(videos_info.values())
    except Exception as e:
        print(f"Error en sesión de TikTok: {e}")
        # Re-lanzamos para que el endpoint Flask reciba el motivo real
        # (perfil no encontrado, sin videos, etc.) en vez de solo un
        # 500 genérico. Si watched/videos_info ya tienen algo útil,
        # igual lo perdemos aquí a propósito: si hubo excepción, el
        # resultado parcial no es confiable.
        raise


async def wait_for_profile_videos(page: Page, search_content: str, captcha_detected,
                                   timeout_ms: int = 20000, captcha_callback=None) -> str:
    """
    Espera a que carguen los videos del perfil cubriendo las variantes que
    suelen darse en cuentas grandes/verificadas (Claro, Movistar, Tigo,
    etc.): selectores distintos según el layout, muro de login que
    reaparece, cuenta privada, o un primer render "colgado" que se arregla
    con un reload.

    Devuelve el selector de contenedor que efectivamente matcheó, para que
    el llamador pueda usarlo al buscar el primer video.
    Lanza ValueError con el motivo específico si no logra cargar nada.
    """
    os.makedirs(DEBUG_DIR, exist_ok=True)

    loop = asyncio.get_event_loop()
    deadline = loop.time() + (timeout_ms / 1000)
    attempt = 0
    reloaded = False
    error_retries = 0

    while loop.time() < deadline:
        attempt += 1

        # 1. ¿Apareció el captcha mientras esperábamos?
        if await page.query_selector(CAPTCHA_SELECTOR):
            captcha_detected.set()
            await handle_captcha(page, captcha_detected, captcha_callback=captcha_callback)

        # 2. ¿Cuenta privada? Esto no tiene arreglo por reintento.
        if await page.query_selector(PRIVATE_ACCOUNT_SELECTOR):
            raise ValueError(
                f"El perfil de \"{search_content}\" es privado, no se pueden ver sus videos."
            )

        # 3. ¿Reapareció el muro de login pidiendo iniciar sesión?
        if await page.query_selector(LOGIN_WALL_SELECTOR):
            close_btn = await page.query_selector(LOGIN_WALL_CLOSE_SELECTOR)
            if close_btn:
                with suppress(Exception):
                    await close_btn.click()
                    await asyncio.sleep(random.uniform(1, 2))

        # 4. ¿TikTok falló al traer los posts en su propia API y muestra su
        #    error genérico ("Something went wrong")? Si es así, hacemos
        #    click en su botón "Refresh" y le damos tiempo extra para
        #    reintentar, hasta un límite de intentos.
        if error_retries < MAX_PROFILE_LOAD_ERROR_RETRIES:
            error_el = await page.query_selector(PROFILE_LOAD_ERROR_SELECTOR)
            if error_el:
                error_retries += 1
                refresh_btn = await page.query_selector(PROFILE_LOAD_ERROR_REFRESH_BUTTON)
                with suppress(Exception):
                    if refresh_btn:
                        await refresh_btn.click()
                    else:
                        await page.reload(wait_until="domcontentloaded")
                # cada reintento le da un poco más de tiempo total, porque
                # el problema es del lado de TikTok, no nuestro
                deadline += 8
                await asyncio.sleep(random.uniform(3, 5))
                continue

        # 5. ¿Ya está el grid de videos con alguno de los selectores conocidos?
        for sel in PROFILE_VIDEO_CONTAINER_SELECTORS:
            el = await page.query_selector(sel)
            if el:
                return sel

        # 6. Si vamos por la mitad del tiempo y nada aparece, forzamos un
        #    reload una sola vez (a veces el SPA se queda colgado en el
        #    primer load de cuentas con mucho contenido/pines).
        if not reloaded and loop.time() > deadline - (timeout_ms / 2000):
            reloaded = True
            with suppress(Exception):
                await page.reload(wait_until="domcontentloaded")
                await asyncio.sleep(random.uniform(2, 3))

        await asyncio.sleep(0.5)

    # Nada funcionó: guardamos evidencia para diagnosticar y lanzamos el
    # error genérico (mantiene compatibilidad con el mensaje que ya
    # maneja el frontend), pero ahora con screenshot + HTML de respaldo.
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", search_content) or "perfil"
    screenshot_path = f"{DEBUG_DIR}/{safe_name}_{ts}.png"
    html_path = f"{DEBUG_DIR}/{safe_name}_{ts}.html"

    with suppress(Exception):
        await page.screenshot(path=screenshot_path, full_page=True)
    with suppress(Exception):
        html = await page.content()
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)

    still_erroring = await page.query_selector(PROFILE_LOAD_ERROR_SELECTOR)
    reason = (
        f"TikTok mostró su propio error \"Something went wrong\" al traer los posts "
        f"({error_retries} reintento(s) de refresh agotados)"
        if still_erroring else
        "no se detectó el estado de error de TikTok ni el grid de videos (posible cambio de selector)"
    )

    print(f"[DEBUG] No se encontró el grid de videos de \"{search_content}\" — {reason}. "
          f"Evidencia guardada en {screenshot_path} / {html_path}")

    raise ValueError(
        f"Entramos al perfil de \"{search_content}\" pero no se pudieron cargar sus videos."
    )


async def flujo_completo(page: Page, *, content_type, search_content, videos_cant, scrolls, watched, videos_info,
                         captcha_callback=None):

    captcha_detected = asyncio.Event()
    stop_watcher = asyncio.Event()

    watcher = asyncio.create_task(
        watch_captcha(page, captcha_detected, stop_watcher)
    )

    await page.set_viewport_size({"width": 1280, "height": 720})
    await asyncio.sleep(random.uniform(1, 2))
    await handle_captcha(page, captcha_detected, captcha_callback=captcha_callback)
    if content_type == 1:
        login_cont = await page.query_selector("div[id*='loginContainer']")
        search_button = await page.wait_for_selector("button[data-e2e='nav-search']")
        await asyncio.sleep(random.uniform(1, 2))
        login_cont = await page.query_selector("div[id*='loginContainer']")
        await search_button.click()
        login_cont = await page.query_selector("div[id*='loginContainer']")
        await asyncio.sleep(random.uniform(5, 10))
        login_cont = await page.query_selector("div[id*='loginContainer']")
        if login_cont:
            close_modal = await page.query_selector("div[data-e2e='modal-close-inner-button']")
            await close_modal.click()
            await asyncio.sleep(random.uniform(1, 3))
        await page.keyboard.type(search_content)
        await asyncio.sleep(random.uniform(0, 1))
        await page.keyboard.press("Enter")
        await asyncio.sleep(random.uniform(5, 10))

        for x in range(50):
            div_error = await page.query_selector_all("div[class*='DivContainer']:has(h2[data-e2e='search-error-title'])")
            await asyncio.sleep(random.uniform(0, 1))

            if div_error:
                button = await page.query_selector("div[class*='DivContainer']:has(h2[data-e2e='search-error-title']) button")
                await button.hover()
                await asyncio.sleep(random.uniform(1, 2))
                await button.click()
            else:
                break
        tab_bar = await page.query_selector("[class*='tabbar__item-container']")
        divs = await tab_bar.query_selector_all(":scope > div")
        await divs[1].hover()
        await divs[1].click()
        await asyncio.sleep(random.uniform(3, 4))

        list_us = await page.query_selector_all("[class*='DivPanelContainer'] a")

        if not list_us:
            stop_watcher.set()
            watcher.cancel()
            raise ValueError(
                f"No encontramos ningún perfil para \"{search_content}\" en TikTok."
            )

        # Buscamos coincidencia exacta normalizada (ignora espacios,
        # puntos, guiones y mayúsculas). Si nadie matchea exacto,
        # usamos el primer resultado: TikTok ya lo ordena por
        # relevancia, así que suele ser el correcto cuando el usuario
        # escribió el nombre de la marca en vez del @handle real.
        target_norm = normalize_username(search_content)
        matched_user = None

        for x in list_us:
            href = await x.get_attribute("href")
            if href and normalize_username(href.replace("/@", "")) == target_norm:
                matched_user = x
                break

        if not matched_user:
            matched_user = list_us[0]

        await matched_user.click()

        # Esperamos la navegación real al perfil (en vez de solo un sleep
        # fijo). Si el click no navegó por algún motivo, esto lo detecta
        # rápido en vez de quedarnos "esperando" en la página de búsqueda.
        with suppress(Exception):
            await page.wait_for_url("**/@*", timeout=10000)
        await asyncio.sleep(random.uniform(1, 2))

        matched_selector = await wait_for_profile_videos(
            page, search_content, captcha_detected, captcha_callback=captcha_callback
        )

        first_video = await page.query_selector(f"{matched_selector} a")
        if not first_video:
            first_video = await page.query_selector(matched_selector)
        await asyncio.sleep(random.uniform(1, 3))

        if not first_video:
            stop_watcher.set()
            watcher.cancel()
            raise ValueError(
                f"El perfil de \"{search_content}\" no tiene videos disponibles."
            )
        await first_video.click()
        await asyncio.sleep(random.uniform(1, 3))
    else:
        search_button = await page.wait_for_selector("button[data-e2e='nav-search']")
        await asyncio.sleep(random.uniform(1, 2))
        await search_button.click()
        await asyncio.sleep(random.uniform(1, 2))
        await page.keyboard.type(search_content)
        await asyncio.sleep(random.uniform(0, 1))
        await page.keyboard.press("Enter")
        await asyncio.sleep(random.uniform(2, 5))

        for x in range(50):
            div_error = await page.query_selector_all("div[class*='DivContainer']:has(h2[data-e2e='search-error-title'])")
            await asyncio.sleep(random.uniform(0, 1))

            if div_error:
                button = await page.query_selector("div[class*='DivContainer']:has(h2[data-e2e='search-error-title']) button")
                await button.hover()
                await asyncio.sleep(random.uniform(1, 2))
                await button.click()
            else:
                break
        first_video = await page.query_selector("div[data-e2e='search_top-item'] a")
        await asyncio.sleep(random.uniform(1, 3))

        if not first_video:
            stop_watcher.set()
            watcher.cancel()
            raise ValueError(
                f"No encontramos videos para el hashtag \"{search_content}\"."
            )
        await first_video.click()
        await asyncio.sleep(random.uniform(1, 3))
    for _ in range(videos_cant):
        await handle_captcha(page, captcha_detected, captcha_callback=captcha_callback)
        video_id = page.url
        sc_com = True
        len_watched = len(watched)
        try_count = 0
        scroll_count = 0
        await asyncio.sleep(random.uniform(5, 10))
        #vista modo cine, cambia el DOM
        cine_view = False
        cinema_elm = await page.query_selector_all("div[class*='CinemaMode']")

        if cinema_elm:
            cine_view = True
        if cine_view:
            user_video = await page.query_selector("div[class*='CreatorInfo'] a")
            likes_video = await page.query_selector("[data-e2e*='like-count']")
            q_comments = await page.query_selector("[data-e2e*='comment-count']")
            date_video = await page.query_selector("div[class*='CreatorInfo'] span")
            date = transf_date(await date_video.inner_text(), True) if date_video else ""
        else:
            user_video = await page.query_selector("a[data-e2e='browse-user-avatar']")
            likes_video = await page.query_selector("[data-e2e='browse-like-count']")
            q_comments = await page.query_selector("[data-e2e='browse-comment-count']")
            date_video = await page.query_selector_all("div[data-cinema-mode-player-root='true'] span")
            date = transf_date(await date_video[2].inner_text()) if len(date_video) > 2 else ""

        if video_id and video_id not in videos_info:
            videos_info[video_id] = {
                "url": video_id,
                "user": await user_video.get_attribute("href") if user_video else "",
                "likes": await likes_video.inner_text() if likes_video else "",
                "comments": await q_comments.inner_text() if q_comments else "",
                "date": date
            }
            #print(videos_info)
        while sc_com:
            await handle_captcha(page, captcha_detected, captcha_callback=captcha_callback)
            if cine_view:
                elements = await page.query_selector_all("div[class*='DivCommentObjectWrapper']")
            else:

                elements = await page.query_selector_all("div[data-comment-ui-enabled='true']")
            for el in elements:

                try:

                    if cine_view:
                        user_el = await el.query_selector("div[data-e2e='comment-username-1'] div a")
                        user_key = await user_el.get_attribute("href")if user_el else ""
                        cid = user_key
                    else:
                        cid = await el.get_attribute("id")

                    if not cid or cid in watched:
                        continue
                    if cine_view:
                        user = user_el
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
                    "user": await user.get_attribute("href")if user else "",
                    "comment": await text.inner_text() if text else "",
                    "date": transf_date(await date.inner_text()) if date else "",
                    "likes": await likes.inner_text() if likes else "",
                    "media": await img.get_attribute("src") if img else "",
                    "video_id":  video_id
                    }

                except Exception as e:
                    continue
            await asyncio.sleep(random.uniform(5, 8))
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

            if scroll_count > scrolls:
                sc_com = False
            scroll_count += 1
        #elem_com = await page.query_selector("button[data-e2e='arrow-right']")
        await page.keyboard.press("ArrowDown")
        await asyncio.sleep(random.uniform(5, 8))
    stop_watcher.set()
    watcher.cancel()

    with suppress(asyncio.CancelledError):
        await watcher

    return page

def transf_date(date: str, cine=False):
    date_t = ""
    if cine:
        date = date.split()[1]
    if "d" in date:
        date_t = datetime.now() - timedelta(days= int(re.search(r"\d+", date).group()))
        date_t = datetime.strptime(str(date_t).split(" ")[0], "%Y-%m-%d").strftime("%Y-%m-%d")
    elif "w" in date:
        date_t = datetime.now() - timedelta(weeks= int(re.search(r"\d+", date).group()))
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

async def watch_captcha(page:Page, captcha_detected, stop_watcher):
    while not stop_watcher.is_set():
        try:
            if await page.query_selector(CAPTCHA_SELECTOR):
                captcha_detected.set()

            await asyncio.sleep(10)
        except Exception:
            return


async def wait_until_captcha_disappears(page:Page):
    while await page.query_selector(CAPTCHA_SELECTOR):
        await asyncio.sleep(1)

async def handle_captcha(page: Page, captcha_detected, timeout_seconds=None, captcha_callback=None):
    if not captcha_detected.is_set():
        return
    if captcha_callback:
        captcha_callback(True)

    timeout_seconds = timeout_seconds or int(os.getenv("CAPTCHA_TIMEOUT_SECONDS", "900"))
    deadline = asyncio.get_running_loop().time() + timeout_seconds
    print("CAPTCHA detectado: esperando interacción del usuario en noVNC")

    while asyncio.get_running_loop().time() < deadline:
        await asyncio.sleep(2)
        captcha = await page.query_selector(CAPTCHA_SELECTOR)
        if not captcha:
            captcha_detected.clear()
            if captcha_callback:
                captcha_callback(False)
            return

    raise TimeoutError("El CAPTCHA no se resolvió antes del tiempo límite.")
