from datetime import datetime, timezone
from django.db import connection
from django.core.cache import cache
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework import status
from apps.core.responses import api_response

class LivenessHealthCheckView(APIView):
    """
    Liveness probe to confirm that the HTTP application server is alive and accepting requests.
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        return api_response(
            data={
                "status": "UP",
                "service": "hallbook-api",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            message="HallBook API service is healthy and operational."
        )


class ReadinessHealthCheckView(APIView):
    """
    Readiness probe to confirm that all required external backing dependencies
    (PostgreSQL primary database, Redis cache/broker) are connected and responsive.
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        checks = {}
        all_healthy = True

        # Check PostgreSQL
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1;")
                cursor.fetchone()
            checks["database"] = {"status": "HEALTHY", "engine": "PostgreSQL"}
        except Exception as exc:
            all_healthy = False
            checks["database"] = {"status": "UNHEALTHY", "error": str(exc)}

        # Check Redis
        try:
            cache_key = "health_check_ping"
            cache.set(cache_key, "pong", timeout=10)
            val = cache.get(cache_key)
            if val == "pong":
                checks["redis"] = {"status": "HEALTHY", "role": "Cache / Celery Broker"}
            else:
                all_healthy = False
                checks["redis"] = {"status": "UNHEALTHY", "error": "Cache write/read mismatch"}
        except Exception as exc:
            all_healthy = False
            checks["redis"] = {"status": "UNHEALTHY", "error": str(exc)}

        status_code = status.HTTP_200_OK if all_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
        return api_response(
            data={
                "status": "READY" if all_healthy else "DEGRADED",
                "dependencies": checks,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            message="System dependencies ready." if all_healthy else "One or more backing dependencies are unhealthy.",
            status_code=status_code,
            success=all_healthy
        )
