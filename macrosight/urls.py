from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/schema/swagger/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
path("api/v1/", include("apps.system.urls")),
    path("api/v1/", include("apps.policies.urls")),
    path("api/v1/", include("apps.indicators.urls")),
    path("api/v1/", include("apps.sectors.urls")),
    path("api/v1/", include("apps.forecasts.urls")),
    path("api/v1/", include("apps.sales.urls")),
    path("api/v1/", include("apps.costs.urls")),
    path("api/v1/", include("apps.core.urls")),
    path("api/v1/", include("apps.audit.urls")),
    path("api/v1/", include("apps.intelligence.urls")),
    path("api/v1/", include("apps.ml.urls")),
    path("api/v1/", include("apps.inputs.urls")),
    path("api/v1/", include("apps.notices.urls")),
    path("api/v1/", include("apps.dashboard.urls")),
    path("api/v1/", include("apps.scenarios.urls")),
    path("api/v1/", include("apps.agriculture_inputs.urls")),
    path("api/v1/users/", include("apps.users.urls")),
    path("api/v1/external-indicators/", include("apps.externalindicator.urls")),
]

