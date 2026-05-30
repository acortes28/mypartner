from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

api_prefix = 'api/v1/'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path(api_prefix, include('apps.users.urls')),
    path(api_prefix, include('apps.groups.urls')),
    path(api_prefix, include('apps.finances.urls')),
    path(api_prefix, include('apps.documents.urls')),
    path(api_prefix, include('apps.announcements.urls')),
    path(api_prefix, include('apps.notifications.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
