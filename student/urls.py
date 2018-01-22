# -*- coding: UTF-8 -*-
from django.conf.urls import url
from . import views
from django.contrib.auth import views as auth_views
from student.views import AnnounceListView
from django.contrib.auth.decorators import login_required

urlpatterns = [
    #課程
    url(r'^lessons/(?P<lesson>[^/]+)/$', views.lessons),
    url(r'^lesson/(?P<lesson>[^/]+)/(?P<unit>[^/]+)/(?P<index>[^/]+)/$', views.lesson),      
  
    # 選課
    url(r'^classroom/enroll/(?P<classroom_id>[^/]+)/$', views.classroom_enroll),      
    url(r'^classroom/add/$', views.classroom_add),  
    url(r'^classroom/$', views.classroom),
		url(r'^classroom/seat/(?P<enroll_id>\d+)/(?P<classroom_id>\d+)/$', views.seat_edit),
    # 作業上傳
    #url(r'^work/(?P<classroom_id>\d+)/$', views.work),  
    #url(r'^work/download/(?P<index>\d+)/(?P<user_id>\d+)/(?P<workfile_id>\d+)/$', views.work_download),  	
    #url(r'^work1/(?P<classroom_id>\d+)/$', views.work1),  	
    #url(r'^submit/(?P<lesson>[^/]+)/(?P<index>\d+)/$', views.submit),         
    # 同學
    url(r'^classmate/(?P<classroom_id>\d+)/$', views.classmate), 
    url(r'^loginlog/(?P<user_id>\d+)/$', views.LoginLogListView.as_view()),    
    #url(r'^calendar/(?P<classroom_id>\d+)/$', views.LoginCalendarClassView.as_view()),     	
    # 分組
    url(r'^group/enroll/(?P<classroom_id>[^/]+)/(?P<group_id>[^/]+)/$', views.group_enroll),    
    url(r'^group/add/(?P<classroom_id>[^/]+)/$', views.group_add),     
    url(r'^group/(?P<classroom_id>[^/]+)/$', views.group),   
    url(r'^group/size/(?P<classroom_id>[^/]+)/$', views.group_size),      
    url(r'^group/open/(?P<classroom_id>[^/]+)/(?P<action>[^/]+)/$', views.group_open),     
		url(r'^group/delete/(?P<group_id>[^/]+)/(?P<classroom_id>[^/]+)/$', views.group_delete), 
    #查詢該作業分組小老師
    url(r'^group/work/(?P<index>[^/]+)/(?P<classroom_id>[^/]+)$', views.work_group),  	
    #公告
    url(r'^announce/(?P<classroom_id>\d+)/$', login_required(AnnounceListView.as_view()), name='announce-list'),  
    # 作業上傳
    url(r'^work/(?P<classroom_id>\d+)/$', views.work),  
    url(r'^work/download/(?P<lesson>\d+)/(?P<index>\d+)/(?P<user_id>\d+)/(?P<workfile_id>\d+)/$', views.work_download),  	
    #查詢該作業所有同學心得
    url(r'^memo/(?P<classroom_id>[^/]+)/(?P<index>[^/]+)/$', views.memo),   
    url(r'^memo_user/(?P<user_id>\d+)/(?P<lesson>\d+)/$', views.memo_user),	
    #查詢某班級所有同學心得		
    url(r'^memo_all/(?P<classroom_id>[^/]+)$', views.memo_all),  	
    url(r'^memo_show/(?P<user_id>\d+)/(?P<unit>\d+)/(?P<classroom_id>[^/]+)/(?P<score>[^/]+)/$', views.memo_show),
    url(r'^memo_count/(?P<classroom_id>\d+)/$', views.memo_count),        
    url(r'^memo_word/(?P<classroom_id>\d+)/(?P<word>[^/]+)/$', views.memo_word),  	
    url(r'^memo_work_count/(?P<classroom_id>\d+)/(?P<index>\d+)/$', views.memo_work_count),        	
    url(r'^memo_work_word/(?P<classroom_id>\d+)/(?P<work_id>\d+)/(?P<word>[^/]+)/$', views.memo_work_word),  	
]