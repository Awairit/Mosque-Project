from rest_framework import serializers


class VisitTrackSerializer(serializers.Serializer):
    visitor_id = serializers.UUIDField(required=False, allow_null=True)
    path = serializers.CharField(max_length=255, default="/")
    city_id = serializers.IntegerField(required=False, allow_null=True)
    mosque_id = serializers.IntegerField(required=False, allow_null=True)
    event_type = serializers.CharField(max_length=50, default="page_view")
