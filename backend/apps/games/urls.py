from django.urls import path

from apps.games import views

urlpatterns = [
    path("home/", views.home_view, name="home"),
    # Phase 9 — Game Hub + play flow. Static paths sit ahead of {slug}
    # capture routes so catalog keywords can never shadow a page.
    path("hub/", views.hub_view, name="hub"),
    path("hub/categories/", views.hub_categories_view, name="hub-categories"),
    path("hub/categories/<str:ident>/", views.hub_category_view, name="hub-category"),
    path("hub/search/", views.hub_search_view, name="hub-search"),
    path("hub/games/", views.hub_games_view, name="hub-games"),
    path("hub/games/<str:slug>/", views.hub_game_view, name="hub-game"),
    path("hub/games/<str:slug>/sessions/", views.hub_session_create_view, name="hub-session-create"),
    path("hub/sessions/<str:pk>/complete/", views.hub_session_complete_view, name="hub-session-complete"),
]