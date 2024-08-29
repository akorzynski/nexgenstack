"""
URL configuration for nexgenstack project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
from django.urls import path
from svcs.views import VirtualMachineView

urlpatterns = [
    path("admin/", admin.site.urls),
    path('v1/core/virtual-machines/', VirtualMachineView.as_view(), name='virtual_machine'),
    path('v1/core/virtual-machines/<str:pk>/', VirtualMachineView.as_view(), name='virtual_machine_by_id'),
    path('v1/internal/vm-state/<str:pk>/', VirtualMachineView.as_view(), name='virtual_machine_update_state'),
]
