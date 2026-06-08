from django.contrib import admin
from django.conf import settings
from django.http import JsonResponse
from django.urls import path, include, re_path
from django.views.static import serve
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

api_prefix = 'api/v1/'

_ASSETLINKS = [
    {
        'relation': ['delegate_permission/common.handle_all_urls'],
        'target': {
            'namespace': 'android_app',
            'package_name': 'com.finanzosos.mypartner_app',
            'sha256_cert_fingerprints': [
                '8E:BE:AB:19:F2:A2:4F:47:4B:A8:B7:17:75:31:EF:F9:88:C3:F1:23:6F:A7:03:AF:D0:46:C3:E1:3A:C4:16:E1',
            ],
        },
    }
]


def assetlinks_view(request):
    return JsonResponse(_ASSETLINKS, safe=False)


urlpatterns = [
    # Android App Links verification
    path('.well-known/assetlinks.json', assetlinks_view),
    # Admin
    path('admin/', admin.site.urls),
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
]

if settings.DEBUG:
    urlpatterns += [
        path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
        path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    ]

urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]
