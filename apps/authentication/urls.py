# -*- encoding: utf-8 -*-
"""
URLs for the authentication app
"""

from django.urls import path
from .views import login_view, register_user, forgot_password
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('login/', login_view, name="login"),
    path('register/', register_user, name="register"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path('forgot-password/', forgot_password, name='forgot_password'),
]
