from django.urls import path

from apps.tournaments import views

urlpatterns = [
    path("tournaments/", views.tournament_list_view, name="tournament-list"),
    path("tournaments/<str:slug>/", views.tournament_detail_view, name="tournament-detail"),
    path("tournaments/<str:slug>/join/", views.tournament_join_view, name="tournament-join"),
    path("tournaments/<str:slug>/leave/", views.tournament_leave_view, name="tournament-leave"),
]
