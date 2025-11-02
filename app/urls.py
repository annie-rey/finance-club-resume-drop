from django.urls import path
from . import views

urlpatterns = [
    # Public / landing
    path("", views.index, name="index"),

    # Auth
    path("signup/", views.signup, name="signup"),

    # Member pages
    path("me/", views.my_resume, name="my_resume"),
    path("upload/", views.upload_resume, name="upload_resume"),

    # Board pages
    path("board/", views.board_list, name="board_list"),
    path("board/book.zip", views.board_download_zip, name="board_download_zip"),
    path("board/manage/", views.board_group_manage, name="board_group_manage")
]