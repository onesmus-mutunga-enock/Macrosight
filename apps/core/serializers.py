from rest_framework import serializers
from typing import Type


class TimeStampedModelSerializer(serializers.Serializer):
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    class Meta:
        read_only_fields = ["created_at", "updated_at"]


def get_timestamp_serializer_for_model(model: Type) -> Type[serializers.ModelSerializer]:
    """Return a ModelSerializer class for `model` exposing only timestamp fields.

    Usage:
        SerializerCls = get_timestamp_serializer_for_model(MyModel)
        serializer = SerializerCls(instance)

    Raises a ValueError when the model does not expose `created_at`/`updated_at`.
    """

    if not (hasattr(model, "_meta") and hasattr(model, "objects")):
        raise ValueError("Invalid model provided")

    meta = getattr(model, "_meta")

    # Collect field names from model _meta (supporting get_fields or .fields)
    field_names = set()
    if hasattr(meta, "get_fields"):
        try:
            field_names = {f.name for f in meta.get_fields()}
        except Exception:
            # Fall back to .fields if get_fields fails for some meta implementations
            field_names = {getattr(f, "name", None) for f in getattr(meta, "fields", [])}
    elif hasattr(meta, "fields"):
        field_names = {getattr(f, "name", None) for f in getattr(meta, "fields", [])}

    if "created_at" not in field_names or "updated_at" not in field_names:
        raise ValueError(f"Model {getattr(model, '__name__', str(model))} does not expose created_at/updated_at fields")

    class _Serializer(serializers.ModelSerializer):
        class Meta:
            model = model
            fields = ("created_at", "updated_at")
            read_only_fields = ("created_at", "updated_at")

    return _Serializer