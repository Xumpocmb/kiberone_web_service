from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.static import serve
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi


schema_view = get_schema_view(
    openapi.Info(
        title="KIBERone API",
        default_version='v1',
        description="API документация для KIBERone веб-сервиса",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@kiberone.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("app_home.urls")),
    path("webapp/", include("app_kiberclub.urls")),
    path("api/", include("app_api.urls")),
    path("kibershop/", include("app_kibershop.urls")),
    path("users/", include("app_users.urls")),
    # Swagger URLs
    path("swagger<format>/", schema_view.without_ui(cache_timeout=0), name="schema-json"),
    path("swagger/", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    # Serve React build static files directly in DEBUG mode
    urlpatterns += static("/static/", document_root=settings.BASE_DIR / "templates/app_clients_resumes/build/static")
    # Serve React build files directly in DEBUG mode
    urlpatterns += [
        re_path(r'^(?P<path>.*)$', serve, {'document_root': settings.BASE_DIR / "templates/app_clients_resumes/build"}),
    ]
