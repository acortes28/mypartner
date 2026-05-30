from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

api_prefix = 'api/v1/'

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    # API docs
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    # REST API
    path(api_prefix, include('apps.users.urls')),
    path(api_prefix, include('apps.groups.urls')),
    path(api_prefix, include('apps.finances.urls')),
    path(api_prefix, include('apps.documents.urls')),
    path(api_prefix, include('apps.announcements.urls')),
    path(api_prefix, include('apps.notifications.urls')),
    # Web frontend (Django templates)
    path('', include('apps.users.web_urls')),
    path('', include('apps.groups.web_urls')),
    path('', include('apps.finances.web_urls')),
    path('', include('apps.documents.web_urls')),
    path('', include('apps.announcements.web_urls')),
    path('', include('apps.notifications.web_urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
