# -*- coding: UTF-8 -*-
from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from . import views
from teacher.views import ClassroomListView, ClassroomCreateView

urlpatterns = [
    url(r'^classroom/$', login_required(ClassroomListView.as_view())),
    url(r'^classroom/add/$', login_required(ClassroomCreateView.as_view())),
    url(r'^classroom/edit/(?P<classroom_id>\d+)/$', views.classroom_edit),
    # 退選
    
#url(r'^unenroll/(?P<enroll_id>\d+)/(?P<classroom_id>\d+)/$', views.unenroll),  	
]