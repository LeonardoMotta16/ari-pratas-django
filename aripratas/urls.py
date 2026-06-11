from django.contrib import admin  # type: ignore[reportMissingModuleSource]
from django.urls import path, include  # type: ignore[reportMissingModuleSource]
from django.conf import settings  # type: ignore[reportMissingModuleSource]
from django.conf.urls.static import static  # type: ignore[reportMissingModuleSource]
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('loja.urls')),
    path('painel/', include('painel.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)