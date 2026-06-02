import asyncio
import random
import os
from TikTokApi import TikTokApi

ms_token = os.getenv("MSTOKEN")

async def scrap_comentarios(video: str, limite: int = 100):

    async with TikTokApi() as api:

        await api.create_sessions(
            ms_tokens=[ms_token],
            num_sessions=1,
            sleep_after=3,        # pausa tras crear sesión
            headless=False,       # menos detectable que headless
        )

        comments = []

        #for v in video:
        video = api.video(id=video)
        

        async for comentario in video.comments(count=limite):
            data = comentario.as_dict
            comments.append({
                "video_id": video.id,
                "comment": data.get("text"),
                "user": data["user"].get("unique_id"),
                #"likes": data.get("digg_count"),
                #"fecha": data.get("create_time"),
            })

        await asyncio.sleep(random.uniform(2,10))
        print(comments)
        return comments