
import asyncio

from flask import jsonify

from .repository import ScrapingRepository
from app.scraping_tiktok.scrapl import scrape_comments as scrape_tiktok
from app.scraping_yt.scrapl import scrape_comments as scrape_yt
from app.scraping_instagram.scrapl import scrape_comments as scrape_instagram


class ScrapingService:

    @staticmethod
    def scrape(platform, profile, cant, content_type, scroll, captcha_callback=None):
        comments = []
        videos = []

        if platform == 1:
            comments, videos = asyncio.run(scrape_tiktok(
                profile,
                cant,
                content_type,
                scroll,
                captcha_callback=captcha_callback,
            ))

        elif platform == 2:

            comments, videos = asyncio.run(scrape_instagram(
                profile,
                cant,
                content_type,
                scroll
            ))

        elif platform == 3:

            comments, videos = asyncio.run(scrape_yt(
                profile,
                cant,
                content_type,
                scroll
            ))

        else:

            raise ValueError("Plataforma no válida")

        # if len(comments) == 0:
        #     return {"message": "no se encontraron comentarios"}

        ScrapingRepository.save_comments(
            comments
        )
        return comments, videos
