"""URL configuration for the Honor Board project."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

from board import views

# Arabic branding for the admin interface.
admin.site.site_header = "مركز الوهاب لتحفيظ القرآن الكريم"
admin.site.site_title = "لوحة الشرف"
admin.site.index_title = "إدارة لوحة الشرف"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.student_list, name="student_list"),
    path("health/", views.health, name="health"),
]

if settings.DEBUG:
    # Serve user-uploaded photos during local development only.
    # In production photos live on Cloudinary and are served from its CDN.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
