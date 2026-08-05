from firebase_admin import auth

class AuthService:

    @staticmethod
    def verify_token(id_token):

        decoded = auth.verify_id_token(id_token)

        return {
            "uid": decoded["uid"],
            "email": decoded["email"]
        }