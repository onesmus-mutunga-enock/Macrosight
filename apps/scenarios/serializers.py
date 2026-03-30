from rest_framework import serializers
from .models import ScenarioDefinition, ScenarioVersion, Scenario, Simulation, ScenarioComparison


class ScenarioDefinitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScenarioDefinition
        fields = [
            "id",
            "name",
            "description",
            "status",
            "sector",
            "type",
            "assumptions",
            "metadata",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]


class ScenarioVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScenarioVersion
        fields = [
            "id",
            "scenario_definition",
            "version_label",
            "description",
            "status",
            "implementation",
            "assumptions",
            "effective_date",
            "expiry_date",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]


class ScenarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scenario
        fields = "__all__"


class SimulationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Simulation
        fields = "__all__"


class ScenarioComparisonSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScenarioComparison
        fields = "__all__"