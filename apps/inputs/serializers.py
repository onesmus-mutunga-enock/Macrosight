from rest_framework import serializers
from .models import Fertilizer, Seed, Pesticide, Fuel, InputSummary


class FertilizerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fertilizer
        fields = '__all__'


class SeedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Seed
        fields = '__all__'


class PesticideSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pesticide
        fields = '__all__'


class FuelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fuel
        fields = '__all__'


class InputSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = InputSummary
        fields = '__all__'