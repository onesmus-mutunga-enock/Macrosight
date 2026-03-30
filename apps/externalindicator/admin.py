from django.contrib import admin
from django.utils import timezone

from .models import (
    ExternalSource,
    ExternalIndicator,
    ExternalIndicatorValue,
    ProviderMapping,
)
from . import tasks


@admin.register(ExternalSource)
class ExternalSourceAdmin(admin.ModelAdmin):
    list_display = ("name", "base_url", "created_at")
    readonly_fields = ("created_at",)
    actions = ["ingest_now"]

    def ingest_now(self, request, queryset):
        for src in queryset:
            # Basic heuristic: if this is World Bank, skip here; use indicator-level ingestion
            # We'll enqueue a central bank ingest task as a default
            tasks.task_ingest_central_bank.delay(src.name, src.base_url)
        self.message_user(request, "Ingestion tasks enqueued.")

    ingest_now.short_description = "Enqueue ingestion for selected sources"


@admin.register(ExternalIndicator)
class ExternalIndicatorAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "source")
    actions = ["ingest_indicator", "map_to_internal"]

    def ingest_indicator(self, request, queryset):
        for ind in queryset:
            src_name = ind.source.name
            # Heuristic: if source name contains 'World Bank'
            if "world bank" in src_name.lower():
                # indicator.code expected to be world bank code
                tasks.task_ingest_world_bank.delay(ind.code, "KEN")
            else:
                # default to central bank style ingest
                tasks.task_ingest_central_bank.delay(src_name, ind.code)
        self.message_user(request, "Ingest tasks enqueued for selected indicators.")

    ingest_indicator.short_description = "Enqueue ingestion for selected indicators"

    def map_to_internal(self, request, queryset):
        for ind in queryset:
            tasks.task_map_external_to_internal.delay(ind.source.name, ind.code)
        self.message_user(request, "Mapping tasks enqueued for selected indicators.")

    map_to_internal.short_description = "Map selected external indicators into internal indicators"


@admin.register(ExternalIndicatorValue)
class ExternalIndicatorValueAdmin(admin.ModelAdmin):
    list_display = ("indicator", "date", "value", "retrieved_at")
    readonly_fields = ("retrieved_at",)


@admin.register(ProviderMapping)
class ProviderMappingAdmin(admin.ModelAdmin):
    list_display = ("source", "external_code", "target_indicator", "is_active", "created_at")
    list_filter = ("source", "is_active")
    actions = ["map_now"]

    def map_now(self, request, queryset):
        for m in queryset:
            tasks.task_map_external_to_internal.delay(m.source.name, m.external_code)
        self.message_user(request, "Mapping tasks enqueued for selected mappings.")

    map_now.short_description = "Run mapping for selected provider mappings"

