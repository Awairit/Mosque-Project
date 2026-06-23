"""API views for account-related workflows."""

from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import MosqueAdmin
from apps.accounts.serializers import LoginSerializer


class LoginAPIView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "sensitive"

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        mobile_number = serializer.validated_data["mobile_number"]
        password = serializer.validated_data["password"]

        # Check if active MosqueAdmin profile exists for the given mobile number
        try:
            mosque_admin = MosqueAdmin.objects.select_related(
                "user", "mosque"
            ).get(mobile_number=mobile_number)
        except MosqueAdmin.DoesNotExist:
            return Response(
                {"non_field_errors": ["Invalid mobile number or password."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not mosque_admin.is_active or not mosque_admin.user.is_active:
            return Response(
                {"non_field_errors": ["This account has been disabled."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Authenticate the user. Username is the mobile number.
        user = authenticate(username=mobile_number, password=password)
        if not user:
            return Response(
                {"non_field_errors": ["Invalid mobile number or password."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        token, _ = Token.objects.get_or_create(user=user)

        return Response(
            {
                "token": token.key,
                "mobile_number": mosque_admin.mobile_number,
                "mosque_id": mosque_admin.mosque.id,
                "mosque_name": mosque_admin.mosque.mosque_name,
            },
            status=status.HTTP_200_OK,
        )
