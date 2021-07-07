from django.urls import path

from courses import views

urlpatterns = [
    path("", views.home, name="home"),
    path("data/add-period/", views.add_period, name="add_period"),
    path("data/edit-period/<int:pk>/", views.edit_period, name="edit_period"),
    path("data/delete-period/<int:pk>/", views.delete_period, name="delete_period"),
    path("data/add-teacher/", views.add_teacher, name="add_teacher"),
    path("data/edit-teacher/<int:pk>/", views.edit_teacher, name="edit_teacher"),
    path("data/delete-teacher/<int:pk>/", views.delete_teacher, name="delete_teacher"),
    path("data/add-building/", views.add_building, name="add_building"),
    path("data/edit-building/<int:pk>/", views.edit_building, name="edit_building"),
    path(
        "data/delete-building/<int:pk>/", views.delete_building, name="delete_building"
    ),
    path("data/add-room/", views.add_room, name="add_room"),
    path("data/edit-room/<int:pk>/", views.edit_room, name="edit_room"),
    path("data/delete-room/<int:pk>/", views.delete_room, name="delete_room"),
    path("data/add-course/", views.add_course, name="add_course"),
    path("data/edit-course/<int:pk>/", views.edit_course, name="edit_course"),
    path("data/delete-course/<int:pk>/", views.delete_course, name="delete_course"),
]
