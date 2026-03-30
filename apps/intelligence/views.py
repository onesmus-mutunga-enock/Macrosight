from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import extend_schema, OpenApiResponse

from . import services


class IntelligenceViewSet(viewsets.ViewSet):
    """Lightweight API surface for intelligence feature building.

    Exposes a POST action to build features for a given product / sector / date.
    This is intentionally minimal and safe — it calls the existing services
    implemented under `apps.intelligence.services` and returns JSON.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=None,
        responses={200: OpenApiResponse(description="Feature dictionary returned")},
    )
    @action(detail=False, methods=["post"])
    def build(self, request):
        """Build features for runtime prediction.

        Accepts JSON body with optional `product_id`, `sector_id`, and `date`.
        Returns a JSON object of feature name -> value.
        """
        product_id = request.data.get("product_id")
        sector_id = request.data.get("sector_id")
        date = request.data.get("date")

        try:
            features = services.build_features(product_id=product_id, as_of=date, sector_id=sector_id)
            return Response(features, status=status.HTTP_200_OK)
        except Exception as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
