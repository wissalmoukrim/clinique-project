"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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

urlpatterns = [
    # 🔧 ADMIN
    path('admin/', admin.site.urls),

    # 🔐 AUTH
    path('api/auth/', include('accounts.urls')),
    path('api/core/', include('core.urls')),

    # 👤 MODULES MÉTIER
    path('api/patients/', include('patients.urls')),
    path('api/medecins/', include('medecins.urls')),
    path('api/rendezvous/', include('rendezvous.urls')),
    path('api/consultations/', include('consultations.urls')),
    path('api/hospitalisation/', include('hospitalisation.urls')),
    path('api/facturation/', include('facturation.urls')),
    path('api/personnel/', include('personnel.urls')),
    path('api/ambulance/', include('ambulance.urls')),
    path('api/visiteurs/', include('visiteurs.urls')),
]
