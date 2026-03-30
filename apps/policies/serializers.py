from rest_framework import serializers
from .models import Policy, PolicyVersion, PolicySimulation, PolicyImpactAnalysis, PolicySimulationComparison


class PolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = Policy
        fields = [
            "id",
            "code",
            "name",
            "description",
            "status",
            "sector",
            "type",
            "effective_date",
            "expiry_date",
            "parameters",
            "metadata",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]


class PolicyVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PolicyVersion
        fields = [
            "id",
            "policy",
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


class PolicySimulationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PolicySimulation
        fields = "__all__"


class PolicyImpactAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = PolicyImpactAnalysis
        fields = "__all__"


class PolicySimulationComparisonSerializer(serializers.ModelSerializer):
    class Meta:
        model = PolicySimulationComparison
        fields = "__all__"