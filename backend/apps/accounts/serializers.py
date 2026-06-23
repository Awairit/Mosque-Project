"""Serializers for accounts-related APIs."""

from rest_framework import serializers


class LoginSerializer(serializers.Serializer):
    mobile_number = serializers.CharField(write_only=True)
    password = serializers.CharField(
        write_only=True, style={"input_type": "password"}
    )

    def validate_mobile_number(self, value: str) -> str:
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Mobile number is required.")
        return value

    def validate_password(self, value: str) -> str:
        if not value:
            raise serializers.ValidationError("Password is required.")
        return value
