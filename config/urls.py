"""
URL configuration for config project.

Each feature app owns its own urls.py; this file only wires the top-level
path prefix for each feature (vertical slice) into the project.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),

    # Feature URLs (vertical slices)
    path('', include('apps.home.urls')),
    path('login/', include('apps.login.urls')),
    path('register/', include('apps.register.urls')),
    path('profile/', include('apps.profile.urls')),
    path('settings/', include('apps.user_settings.urls')),
    path('tickets/', include('apps.tickets.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
