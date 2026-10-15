from django.urls import re_path

from colourlens import views

urlpatterns = [
    re_path(r'^$', views.index, name="colour_index"),
    re_path(r'^(?P<institution>[A-Za-z& ]+)/?$', views.index, name="colour_institution"),
]
