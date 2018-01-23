# -*- coding: UTF-8 -*-
from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from . import views
from teacher.views import ClassroomListView, ClassroomCreateView, AnnounceListView, AnnounceCreateView

urlpatterns = [
    url(r'^classroom/$', login_required(ClassroomListView.as_view())),
    url(r'^classroom/add/$', login_required(ClassroomCreateView.as_view())),
    url(r'^classroom/edit/(?P<classroom_id>\d+)/$', views.classroom_edit),
    #列出所有學生帳號
    url(r'^student/list/$', views.StudentListView.as_view()),    
	  #大量匯入帳號
    url(r'^import/upload$', login_required(views.import_sheet), name='import_upload'),   	
    url(r'^import/student$', login_required(views.import_student), name='import_user'),     
    #退選
    url(r'^unenroll/(?P<enroll_id>\d+)/(?P<classroom_id>\d+)/$', views.unenroll),  	
    #修改資料
    url(r'^password/(?P<user_id>\d+)/$', views.password),
    url(r'^realname/(?P<user_id>\d+)/$', views.realname),    
    #公告
    url(r'^announce/(?P<classroom_id>\d+)/$', login_required(AnnounceListView.as_view()), name='announce-list'),
    url(r'^announce/add/(?P<classroom_id>\d+)/$', login_required(AnnounceCreateView.as_view()), name='announce-add'),  
    url(r'^announce/detail/(?P<message_id>\d+)/$', views.announce_detail),
    url(r'^announce/download/(?P<messagefile_id>\d+)/$', views.announce_download),		
    #作業
    url(r'^work/(?P<classroom_id>\d+)/$', views.work),    
    url(r'^assistant/(?P<classroom_id>\d+)/(?P<user_id>\d+)/(?P<lesson>\d+)/(?P<index>\d+)/$', views.assistant), 
    url(r'^assistant_cancle/(?P<classroom_id>\d+)/(?P<user_id>\d+)/(?P<lesson>\d+)/(?P<index>\d+)$', views.assistant_cancle),  
    url(r'^score_peer/(?P<lesson>\d+)/(?P<index>\d+)/(?P<classroom_id>\d+)/(?P<group>\d+)/$', views.score_peer),     
    url(r'^scoring/(?P<classroom_id>[^/]+)/(?P<user_id>\d+)/(?P<lesson>\d+)/(?P<index>\d+)/$', views.scoring),     
    url(r'^score/(?P<classroom_id>\d+)/(?P<lesson>\d+)/(?P<index>\d+)/$', views.score),   
    url(r'^score/group/(?P<lesson>\d+)/(?P<index>\d+)/(?P<classroom_id>\d+)/$', views.score_group),   
    url(r'^work/group/(?P<classroom_id>\d+)/$', views.work_group),	
   		
]