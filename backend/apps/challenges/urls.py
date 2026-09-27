from django.urls import path

from apps.challenges import views

urlpatterns = [
    path("challenges/", views.challenge_list_view, name="challenge-list"),
    path("challenges/rooms/", views.challenge_rooms_view, name="challenge-rooms"),
    path("challenges/rooms/<str:code>/", views.challenge_room_detail_view, name="challenge-room-detail"),
    path("challenges/<uuid:pk>/", views.challenge_detail_view, name="challenge-detail"),
    path("challenges/<uuid:pk>/invitation/", views.challenge_invitation_respond_view, name="challenge-invitation-respond"),
    path("challenges/create/", views.challenge_create_view, name="challenge-create"),
]
