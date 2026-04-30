from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.authentication import JWTAuthentication


class JWTAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.jwt_authentication = JWTAuthentication()

    def __call__(self, request):
        header = self.jwt_authentication.get_header(request)
        if header:
            try:
                raw_token = self.jwt_authentication.get_raw_token(header)
                validated_token = self.jwt_authentication.get_validated_token(raw_token)
                request.user = self.jwt_authentication.get_user(validated_token)
                request.auth = validated_token
            except Exception:
                request.user = AnonymousUser()
                request.auth = None
        return self.get_response(request)
