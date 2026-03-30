from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.apps import apps
from django.http import Http404
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from .serializers import TimeStampedModelSerializer


class TimeStampedModelViewSet(viewsets.ViewSet):
    """Read-only access to `created_at`/`updated_at` for any timestamped model.

    Usage: GET /time-stamped-models/{pk}/?app=<app_label>&model=<ModelName>
    Returns 400 if `app` or `model` query params are missing, 404 when model or
    instance not found, or 400 when the target model doesn't expose timestamp
    fields.
    """

    permission_classes = [IsAuthenticated]

    # Use 'id' as the lookup kwarg and constrain to integers for clearer schema
    lookup_field = "id"
    lookup_value_regex = "[0-9]+"

    @extend_schema(parameters=[OpenApiParameter(name="id", location=OpenApiParameter.PATH, required=True, type=OpenApiTypes.INT32)])
    def retrieve(self, request, pk=None):
        app_label = request.query_params.get("app")
        model_name = request.query_params.get("model")

        if not app_label or not model_name:
            return Response(
                {"detail": "Please provide `app` and `model` query parameters."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            model = apps.get_model(app_label, model_name)
        except (LookupError, ValueError):
            raise Http404("Model not found")

        try:
            obj = model.objects.get(pk=pk)
        except model.DoesNotExist:
            raise Http404("Object not found")

        # Ensure timestamp attributes exist
        if not (hasattr(obj, "created_at") and hasattr(obj, "updated_at")):
            return Response(
                {"detail": "Target model is not timestamped."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = TimeStampedModelSerializer(
            {"created_at": obj.created_at, "updated_at": obj.updated_at}
        )
        return Response(serializer.data)

    def list(self, request):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
    
    # Help schema generators that inspect view attributes
    serializer_class = TimeStampedModelSerializer