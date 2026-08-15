import uuid
from datetime import timedelta
from django.core.cache import cache
from django.utils import timezone
from django.db.models import Count
from django.db.models.functions import TruncDate
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsCityAdmin
from apps.analytics.models import AnonymousVisitor, VisitEvent
from apps.analytics.serializers import VisitTrackSerializer
from apps.platform_admin.permissions import IsSuperUser


class TrackVisitAPIView(APIView):
    """
    Public privacy-conscious endpoint for recording anonymous visits.
    Stores no PII (no IP, no fingerprinting, no phone, no email).
    """

    permission_classes = [AllowAny]
    throttle_scope = "burst"

    def post(self, request):
        serializer = VisitTrackSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        visitor_id_param = serializer.validated_data.get("visitor_id")
        path = serializer.validated_data.get("path", "/")
        city_id = serializer.validated_data.get("city_id")
        mosque_id = serializer.validated_data.get("mosque_id")
        event_type = serializer.validated_data.get("event_type", "page_view")

        visitor = None
        is_new = False

        if visitor_id_param:
            visitor = AnonymousVisitor.objects.filter(id=visitor_id_param).first()

        if visitor is None:
            visitor = AnonymousVisitor.objects.create(visit_count=1)
            is_new = True
        else:
            visitor.visit_count += 1
            visitor.save(update_fields=["last_seen", "visit_count", "updated_at"])

        # Deduplicate rapid bursts (e.g. duplicate tracking events within 3 seconds)
        dedup_key = f"vis_dedup_{visitor.id}_{path}_{event_type}"
        if not cache.get(dedup_key):
            cache.set(dedup_key, True, timeout=3)
            VisitEvent.objects.create(
                visitor=visitor,
                path=path[:255],
                city_id=city_id,
                mosque_id=mosque_id,
                event_type=event_type[:50],
            )

        return Response(
            {
                "visitor_id": str(visitor.id),
                "is_new_visitor": is_new,
            },
            status=status.HTTP_200_OK,
        )


class SuperAdminAnalyticsOverviewAPIView(APIView):
    """
    Platform-wide analytics dashboard metrics for Super Admin.
    """

    permission_classes = [IsAuthenticated, IsSuperUser]

    def get(self, request):
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = now - timedelta(days=7)
        month_start = now - timedelta(days=30)

        total_visits = VisitEvent.objects.count()
        unique_visitors = AnonymousVisitor.objects.count()
        new_visitors = AnonymousVisitor.objects.filter(visit_count=1).count()
        returning_visitors = AnonymousVisitor.objects.filter(visit_count__gt=1).count()

        today_visits = VisitEvent.objects.filter(timestamp__gte=today_start).count()
        this_week_visits = VisitEvent.objects.filter(timestamp__gte=week_start).count()
        this_month_visits = VisitEvent.objects.filter(timestamp__gte=month_start).count()

        # 14-day trend aggregation
        fourteen_days_ago = now - timedelta(days=14)
        daily_qs = (
            VisitEvent.objects.filter(timestamp__gte=fourteen_days_ago)
            .annotate(date=TruncDate("timestamp"))
            .values("date")
            .annotate(
                total_visits=Count("id"),
                unique_visitors=Count("visitor", distinct=True),
            )
            .order_by("date")
        )

        daily_trends = [
            {
                "date": row["date"].strftime("%Y-%m-%d") if row["date"] else "",
                "total_visits": row["total_visits"],
                "unique_visitors": row["unique_visitors"],
            }
            for row in daily_qs
        ]

        return Response(
            {
                "total_visits": total_visits,
                "unique_identified_visitors": unique_visitors,
                "new_visitors": new_visitors,
                "returning_visitors": returning_visitors,
                "period_metrics": {
                    "today": today_visits,
                    "this_week": this_week_visits,
                    "this_month": this_month_visits,
                },
                "daily_trends": daily_trends,
            },
            status=status.HTTP_200_OK,
        )


class CityAdminAnalyticsAPIView(APIView):
    """
    City-scoped visitor analytics metrics for City Admin.
    """

    permission_classes = [IsCityAdmin]

    def get(self, request):
        city_admin = request.user.city_admin
        city = city_admin.city
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = now - timedelta(days=7)
        month_start = now - timedelta(days=30)

        events_qs = VisitEvent.objects.filter(city=city)

        total_visits = events_qs.count()
        unique_visitors = events_qs.values("visitor").distinct().count()

        today_visits = events_qs.filter(timestamp__gte=today_start).count()
        this_week_visits = events_qs.filter(timestamp__gte=week_start).count()
        this_month_visits = events_qs.filter(timestamp__gte=month_start).count()

        # Popular mosques in city
        popular_mosques = (
            events_qs.filter(mosque__isnull=False)
            .values("mosque_id", "mosque__mosque_name")
            .annotate(views=Count("id"))
            .order_by("-views")[:5]
        )

        top_mosques = [
            {
                "mosque_id": row["mosque_id"],
                "mosque_name": row["mosque__mosque_name"],
                "views": row["views"],
            }
            for row in popular_mosques
        ]

        return Response(
            {
                "city_id": city.id,
                "city_name": city.name,
                "total_visits": total_visits,
                "unique_identified_visitors": unique_visitors,
                "period_metrics": {
                    "today": today_visits,
                    "this_week": this_week_visits,
                    "this_month": this_month_visits,
                },
                "top_mosques": top_mosques,
            },
            status=status.HTTP_200_OK,
        )
