from rest_framework import serializers
from .models import GovernmentNotice, NoticeImpact, NoticeSectorImpact


class GovernmentNoticeSerializer(serializers.ModelSerializer):
    class Meta:
        model = GovernmentNotice
        fields = '__all__'


class NoticeImpactSerializer(serializers.ModelSerializer):
    class Meta:
        model = NoticeImpact
        fields = '__all__'


class NoticeSectorImpactSerializer(serializers.ModelSerializer):
    class Meta:
        model = NoticeSectorImpact
        fields = '__all__'