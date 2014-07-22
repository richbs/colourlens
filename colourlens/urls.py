from django.conf.urls import patterns, url
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^$', 'colourlens.views.index', name="colour_index"),
    url(r'^(?P<institution>[A-z& ]+)/?$', 'colourlens.views.index', name="colour_institution"),
)
