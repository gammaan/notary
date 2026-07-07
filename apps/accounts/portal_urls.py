from django.urls import path

from accounts.portal_views import PortalDashboardView, PortalMatterDetailView

app_name = "portal"

urlpatterns = [
    path("", PortalDashboardView.as_view(), name="dashboard"),
    path("matters/<uuid:pk>/", PortalMatterDetailView.as_view(), name="matter_detail"),
]
