
# from firebase_admin import firestore

# db = firestore.client()

class ScrapingRepository:

    @staticmethod
    def save_comments(comments):
        
        print("save")

        # batch = db.batch()

        # project_ref = (
        #     db.collection("scraping_projects")
        # )

        # for comment in comments:

        #     comment_id = str(
        #         comment.get("comment_id")
        #     )

        #     comment_ref = (
        #         project_ref
        #         .collection("comments")
        #         .document(comment_id)
        #     )

        #     batch.set(
        #         comment_ref,
        #         comment
        #     )

        # batch.commit()