from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, UpdateView

from accounts.forms import (
    CustomPasswordChangeForm,
    EmailAuthenticationForm,
    UserProfileForm,
    UserRegistrationForm,
)
from accounts.models import User


class RegisterView(CreateView):
    model = User
    form_class = UserRegistrationForm
    template_name = "accounts/register.html"
    success_url = reverse_lazy("accounts:profile")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("accounts:profile")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        messages.success(
            self.request,
            _("Welcome, %(name)s! Your account has been created.") % {"name": self.object.first_name},
        )
        return response


class UserLoginView(LoginView):
    form_class = EmailAuthenticationForm
    template_name = "accounts/login.html"
    redirect_authenticated_user = True

    def form_valid(self, form):
        messages.success(
            self.request,
            _("Welcome back, %(name)s.") % {"name": form.get_user().first_name},
        )
        return super().form_valid(form)


class UserLogoutView(LogoutView):
    next_page = reverse_lazy("home")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, _("You have been signed out."))
        return super().dispatch(request, *args, **kwargs)


class ProfileView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserProfileForm
    template_name = "accounts/profile.html"
    success_url = reverse_lazy("accounts:profile")

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, _("Your profile has been updated."))
        return super().form_valid(form)


class UserPasswordChangeView(PasswordChangeView):
    form_class = CustomPasswordChangeForm
    template_name = "accounts/password_change.html"
    success_url = reverse_lazy("accounts:profile")

    def form_valid(self, form):
        messages.success(self.request, _("Your password has been changed."))
        return super().form_valid(form)
