from django.urls import path

from courses import views

urlpatterns = [
    path("", views.home, name="home"),
    path("data/add-period/", views.add_period, name="add_period"),
    path("data/edit-period/<int:pk>/", views.edit_period, name="edit_period"),
    path("data/delete-period/<int:pk>/", views.delete_period, name="delete_period"),
]
