"""
URL configuration for DjangoOfficeProject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView

# 修复访问http://127.0.0.1:8000/media/img/aqb9AbgYoDxbGyzrpvduWz.jpg失败
urlpatterns = [
    path('admin/', admin.site.urls),
    path('officeAuth/', include('apps.officeAuth.urls')),
    path('Attendance/', include('apps.officeAttendance.urls')),
    path('staff/', include('apps.staff.urls')),
    path('file/', include('apps.file.urls')),
    path('inform/', include('apps.inform.urls')),
    path('home/', include('apps.home.urls')),
    path('download_api_docs/', SpectacularAPIView.as_view(), name='schema'),
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

