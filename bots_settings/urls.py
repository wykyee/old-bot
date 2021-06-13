from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls import include
from django.contrib import admin
from django.urls import path

handler404 = "bots_management.views.notfound"

urlpatterns = [
    path('bot_admin/', admin.site.urls),
    path('', include('bots_management.urls', namespace="bots-management")),
    path('', include('moderators.urls', namespace="moderators"))
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
