# -*- coding: UTF-8 -*-
from django.conf.urls import url
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    url(r'^lessons/(?P<lesson>[^/]+)/$', views.lessons),
    url(r'^lesson/(?P<lesson>[^/]+)/(?P<unit>[^/]+)/(?P<index>[^/]+)/$', views.lesson),      
]