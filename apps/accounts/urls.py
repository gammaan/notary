"""
Public auth routes (login, register, profile).

Disabled while the site is staff-only via Django Admin.
Re-enable by setting PUBLIC_AUTH_ENABLED = True in settings and
including accounts.urls in notary/urls.py.
"""

from django.urls import path

from accounts.views import (
    ProfileView,
    RegisterView,
    UserLoginView,
    UserLogoutView,
    UserPasswordChangeView,
)

app_name = "accounts"

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", UserLoginView.as_view(), name="login"),
    path("logout/", UserLogoutView.as_view(), name="logout"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("password/change/", UserPasswordChangeView.as_view(), name="password_change"),
]
