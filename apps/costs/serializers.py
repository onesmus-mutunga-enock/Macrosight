from rest_framework import serializers
from .models import InputCost, InputCostValue


class InputCostSerializer(serializers.ModelSerializer):
    class Meta:
        model = InputCost
        fields = [
            "id",
            "name",
            "sector",
            "unit",
        ]
        read_only_fields = ["id"]


class InputCostValueSerializer(serializers.ModelSerializer):
    cost = serializers.PrimaryKeyRelatedField(queryset=InputCost.objects.all())

    class Meta:
        model = InputCostValue
        fields = [
            "id",
            "cost",
            "date",
            "value",
        ]
        read_only_fields = ["id"]

    def validate_value(self, value):
        if value is None:
            return value
        try:
            numeric = float(value)
        except Exception:
            raise serializers.ValidationError("Value must be a number")
        if numeric < 0:
            raise serializers.ValidationError("Value must be non-negative")
        return numeric

    def validate(self, attrs):
        # Ensure no duplicate entries for the same cost+date
        cost = attrs.get("cost") if "cost" in attrs else getattr(self.instance, "cost", None)
        date = attrs.get("date") if "date" in attrs else getattr(self.instance, "date", None)

        if cost is None or date is None:
            return attrs

        qs = InputCostValue.objects.filter(cost=cost, date=date)
        if self.instance:
            qs = qs.exclude(id=self.instance.id)

        if qs.exists():
            raise serializers.ValidationError("An InputCostValue for this cost and date already exists")

        return attrs