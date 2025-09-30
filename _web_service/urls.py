from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", include("app_kiberclub.urls")),
    path("api/", include("app_api.urls")),
    path("api/tutor/", include("app_clients_resumes.urls")),
    path("kibershop/", include("app_kibershop.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
