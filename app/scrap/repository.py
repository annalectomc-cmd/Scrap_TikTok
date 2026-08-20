import uuid
from app.extensions.firebase import get_firestore


class ScrapingRepository:

    @staticmethod
    def _get_db():
        return get_firestore()

    @classmethod
    def save_comments(cls, comments, project_id=None):
        if not comments:
            return 0

        db = cls._get_db()

        if project_id:
            comments_ref = (
                db.collection("scraping_projects")
                .document(str(project_id))
                .collection("comments")
            )
        else:
            comments_ref = db.collection("comments")

        # Firestore allows up to 500 operations per batch
        batch_size = 500
        total_saved = 0

        for i in range(0, len(comments), batch_size):
            chunk = comments[i:i + batch_size]
            batch = db.batch()

            for comment in chunk:
                comment_id = str(
                    comment.get("comment_id")
                    or comment.get("cid")
                    or comment.get("id")
                    or uuid.uuid4().hex
                )

                comment_ref = comments_ref.document(comment_id)
                batch.set(comment_ref, comment, merge=True)

            batch.commit()
            total_saved += len(chunk)

        print(f"Successfully saved {total_saved} comments to Firestore.")
        return total_saved

    @classmethod
    def get_comments(cls, project_id=None, limit=100):
        db = cls._get_db()

        if project_id:
            query = (
                db.collection("scraping_projects")
                .document(str(project_id))
                .collection("comments")
                .limit(limit)
            )
        else:
            query = db.collection("comments").limit(limit)

        docs = query.stream()
        return [doc.to_dict() for doc in docs]