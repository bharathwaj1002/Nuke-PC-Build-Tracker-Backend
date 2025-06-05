from django.contrib.auth.models import User
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model

class EmailBackend(BaseBackend):
    def authenticate(self, request, email=None, password=None):
        User = get_user_model()
        try:
            # Find user by email
            user = User.objects.get(email=email)
            # Check if the password is correct
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            return None
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None