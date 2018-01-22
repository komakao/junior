# -*- coding: UTF-8 -*-
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.contrib.auth import authenticate, login
from django.db.models import *
from forms import LoginForm, UserRegistrationForm, PasswordForm, RealnameForm, LineForm, SchoolForm, EmailForm, StudentLoginForm
from django.contrib.auth.models import User
from account.models import Profile, PointHistory, Message, MessagePoll, Visitor, VisitorLog
from student.models import Enroll, Work, Assistant
from teacher.models import Classroom
#from certificate.models import Certificate
from django.core.exceptions import ObjectDoesNotExist
from account.templatetags import tag 
from django.views.generic import ListView, CreateView
from django.contrib.auth.models import Group
from django.http import JsonResponse
import sys, os
from django.http import HttpResponse
from mimetypes import MimeTypes
#from student.lesson import *
#from student.video import *
import StringIO
import xlsxwriter
import datetime
from django.utils import timezone
from django.utils.timezone import localtime
from datetime import datetime
from django.utils import timezone
from django.apps import apps
import json
import urllib
from django.db.models import Q
from itertools import groupby
from collections import OrderedDict
#from helper import VideoLogHelper

# 判斷是否為任教學生
def is_student(user_id, request):
    classrooms = Classroom.objects.filter(teacher_id=request.user.id)
    for classroom in classrooms:
        if Enroll.objects.filter(classroom_id=classroom.id, student_id=user_id).exists(): 
            return True
    return False
    
# 判斷是否為本班同學
def is_classmate(user_id, classroom_id):
    return Enroll.objects.filter(student_id=user_id, classroom_id=classroom_id).exists()

# 網站首頁
def homepage(request):
    models = apps.get_models()
    row_count = 0
    for model in models:
        row_count = row_count + model.objects.count()
    users = User.objects.all()
    try :
        admin_user = User.objects.get(id=1)
        admin_profile = Profile.objects.get(user=admin_user)
        admin_profile.home_count = admin_profile.home_count + 1
        admin_profile.save()
    except ObjectDoesNotExist:
        admin_profile = ""
    classroom_count = Classroom.objects.all().count()
    return render_to_response('homepage.html', {'classroom_count':classroom_count, 'row_count':row_count, 'user_count':len(users), 'admin_profile': admin_profile}, context_instance=RequestContext(request))

# 作者
def author(request):
    return render_to_response('account/author.html', context_instance=RequestContext(request))

	
	
# 使用者登入功能
def user_login(request):
        message = None
        test = ""
        if request.method == "POST":
                form = LoginForm(request.POST)
                if form.is_valid():
                        username = request.POST['username']
                        password = request.POST['password']
                        user = authenticate(username=username, password=password)
                        if user is not None:
                                if user.is_active:
                                        if user.is_superuser:
                                            mygroup1, created = Group.objects.get_or_create(name='teacher')
                                            user.groups.add(mygroup1) 
                                            mygroup2, created = Group.objects.get_or_create(name='active_teacher')
                                            user.groups.add(mygroup2)                                       
                                            if user.first_name == "": 
                                                user.first_name = "管理員"
                                                user.save()
                                                # create Message
                                                title = "請修改您的姓名"
                                                url = "/account/realname"
                                                message = Message.create(title=title, url=url, time=timezone.now())
                                                message.save()                        
                    
                                                # message for group member
                                                messagepoll = MessagePoll.create(message_id = message.id,reader_id=1)
                                                messagepoll.save()                                                             
                                        # 登入成功，導到大廳
                                        login(request, user)
                                        # 記錄訪客資訊
                                        admin_user = User.objects.get(id=1)
                                        try:
                                            profile = Profile.objects.get(user=admin_user)
                                        except ObjectDoesNotExist:
                                            profile = Profile(user=admin_user)
                                            profile.save()
                                        profile.visitor_count = profile.visitor_count + 1
                                        profile.save()
                                        
                                        year = localtime(timezone.now()).year
                                        month =  localtime(timezone.now()).month
                                        day =  localtime(timezone.now()).day
                                        date_number = year * 10000 + month*100 + day
                                        try:
                                            visitor = Visitor.objects.get(date=date_number)
                                        except ObjectDoesNotExist:
                                            visitor = Visitor(date=date_number)
                                        visitor.count = visitor.count + 1
                                        visitor.save()
                                        
                                        visitorlog = VisitorLog(visitor_id=visitor.id, user_id=user.id, IP=request.META.get('REMOTE_ADDR'))
                                        visitorlog.save()
                                        
                                        return redirect('/account/0')
                                else:
                                        message = "Your user is inactive"
                        else:                            
                            message = "無效的帳號或密碼!"
        else:
                form = LoginForm()
        return render_to_response('registration/login.html', {'test': test, 'message': message, 'form': form}, context_instance=RequestContext(request))

# 使用者登入功能
def student_login(request):
        message = None
        test = ""
        if request.method == "POST":
                form = StudentLoginForm(request.POST)
                if form.is_valid():
                        username = request.POST['teacher'] + "_" + request.POST['username']
                        password = request.POST['password']
                        user = authenticate(username=username, password=password)
                        if user is not None:
                                if user.is_active:                                                                                               
                                        # 登入成功，導到大廳
                                        login(request, user)
                                        try:
                                            profile = Profile.objects.get(user=user)
                                        except ObjectDoesNotExist:
                                            profile = Profile(user=user)
                                            profile.save()
                                            # create Message
                                            title = "請洽詢任課教師課程名稱及選課密碼"
                                            url = "/student/classroom/add"
                                            message = Message.create(title=title, url=url, time=timezone.now())
                                            message.save()                        
                    
                                            # message for group member
                                            messagepoll = MessagePoll(message_id = message.id,reader_id=user.id)
                                            messagepoll.save()               																						
                                        profile.visitor_count = profile.visitor_count + 1
                                        profile.save()
                                        
                                        year = localtime(timezone.now()).year
                                        month =  localtime(timezone.now()).month
                                        day =  localtime(timezone.now()).day
                                        date_number = year * 10000 + month*100 + day
                                        try:
                                            visitor = Visitor.objects.get(date=date_number)
                                        except ObjectDoesNotExist:
                                            visitor = Visitor(date=date_number)
                                        visitor.count = visitor.count + 1
                                        visitor.save()
                                        
                                        visitorlog = VisitorLog(visitor_id=visitor.id, user_id=user.id, IP=request.META.get('REMOTE_ADDR'))
                                        visitorlog.save()
                                        
                                        return redirect('/account/0')
                                else:
                                        message = "Your user is inactive"
                        else:                            
                            message = "無效的帳號或密碼!"
        else:
                form = StudentLoginForm()
        return render_to_response('account/student_login.html', {'test': test, 'message': message, 'form': form}, context_instance=RequestContext(request))

# 記錄登出
def suss_logout(request, user_id):
    return redirect('/account/login/')

# 訊息
class MessageListView(ListView):
    context_object_name = 'messages'
    paginate_by = 20
    template_name = 'account/dashboard.html'

    def get_queryset(self):             
        query = []
        #公告
        if self.kwargs['action'] == "1":
            messagepolls = MessagePoll.objects.filter(reader_id=self.request.user.id, message_type=1).order_by('-message_id')
        #私訊
        elif self.kwargs['action'] == "2":
            messagepolls = MessagePoll.objects.filter(reader_id=self.request.user.id, message_type=2).order_by('-message_id')
        #系統
        elif self.kwargs['action'] == "3":
            messagepolls = MessagePoll.objects.filter(reader_id=self.request.user.id, message_type=3).order_by('-message_id')						
        else :
            messagepolls = MessagePoll.objects.filter(reader_id=self.request.user.id).order_by('-message_id')
        for messagepoll in messagepolls:
            query.append([messagepoll, messagepoll.message])
        return query
        
    def get_context_data(self, **kwargs):
        context = super(MessageListView, self).get_context_data(**kwargs)
        context['action'] = self.kwargs['action']
        return context
        
# 註冊帳號                  
def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            # Create a new user object but avoid saving it yet
            new_user = form.save(commit=False)
            # Set the chosen password                 
            new_user.set_password(
                form.cleaned_data['password'])
            # Save the User object
            new_user.save()
            mygroup1, created = Group.objects.get_or_create(name='teacher')
            new_user.groups.add(mygroup1)             
            profile = Profile(user=new_user)
            profile.save()              
        
            # create Message
            title = "請洽詢任課教師課程名稱及選課密碼"
            url = "/student/classroom/add"
            message = Message.create(title=title, url=url, time=timezone.now())
            message.save()                        
                    
            # message for group member
            messagepoll = MessagePoll.create(message_id = message.id,reader_id=new_user.id)
            messagepoll.save()               
            return render(request,
                          'account/register_done.html',
                          {'new_user': new_user})
    else:
        form = UserRegistrationForm()
    return render(request,
                  'account/register.html',
                  {'form': form})
      
# 顯示個人檔案
def profile(request, user_id):
    user = User.objects.get(id=user_id)
    enrolls = Enroll.objects.filter(student_id=user_id)
    try: 
        profile = Profile.objects.get(user=user)
    except ObjectDoesNotExist:
        profile = Profile(user=user)
        profile.save()

    works = Work.objects.filter(user_id=user_id)
    for work in works:
        lesson_list[work.index-1].append(work.score)
        lesson_list[work.index-1].append(work.publication_date)
        if work.score > 0 :
            score_name = User.objects.get(id=work.scorer).first_name
            lesson_list[work.index-1].append(score_name)
        else :
            lesson_list[work.index-1].append("null")

    # 計算積分    
    credit = profile.work + profile.assistant + profile.debug + profile.creative     
        
    #檢查是否為教師或同班同學
    user_enrolls = Enroll.objects.filter(student_id=request.user.id)
    for enroll in user_enrolls:
        if is_classmate(user_id, enroll.classroom_id) or request.user.id == 1:
          return render_to_response('account/profile.html',{'works':works, 'enrolls':enrolls, 'profile': profile,'user_id':user_id, 'credit':credit}, context_instance=RequestContext(request))	
    if user_id == str(request.user.id):	
        return render_to_response('account/profile.html',{'works':works, 'enrolls':enrolls, 'profile': profile,'user_id':user_id, 'credit':credit}, context_instance=RequestContext(request))	
    return redirect("/")

# 修改密碼
def password(request, user_id):
    if not request.user.is_superuser:
        return redirect("/")
    if request.method == 'POST':
        form = PasswordForm(request.POST)
        if form.is_valid():
            user = User.objects.get(id=user_id)
            user.set_password(request.POST['password'])
            user.save()            
            return redirect('/')
    else:
        form = PasswordForm()
        user = User.objects.get(id=user_id)

    return render_to_response('form.html',{'form': form, 'user':user}, context_instance=RequestContext(request))

# 修改他人的真實姓名
def adminrealname(request, user_id):
    if not request.user.is_superuser:
        return redirect("/")	
    if request.method == 'POST':
        form = RealnameForm(request.POST)
        if form.is_valid():
            user = User.objects.get(id=user_id)
            user.first_name =form.cleaned_data['first_name']
            user.save()               
            return redirect('/account/userlist/')
    else:
        teacher = False
        enrolls = Enroll.objects.filter(student_id=user_id)
        for enroll in enrolls:
            classroom = Classroom.objects.get(id=enroll.classroom_id)
            if request.user.id == classroom.teacher_id:
                teacher = True
                break
        if teacher or request.user.is_superuser:
            user = User.objects.get(id=user_id)
            form = RealnameForm(instance=user)
        else:
            return redirect("/")

    return render_to_response('form.html',{'form': form}, context_instance=RequestContext(request))
	
# 修改自己的真實姓名
def realname(request):
    if request.method == 'POST':
        form = RealnameForm(request.POST)
        if form.is_valid():
            user = User.objects.get(id=request.user.id)
            user.first_name =form.cleaned_data['first_name']
            user.save()             
            return redirect('/account/profile/'+str(request.user.id))
    else:
        user = User.objects.get(id=request.user.id)
        form = RealnameForm(instance=user)

    return render_to_response('form.html',{'form': form}, context_instance=RequestContext(request))

# 修改學校名稱
def adminschool(request):
    if request.method == 'POST':
        form = SchoolForm(request.POST)
        if form.is_valid():
            user = User.objects.get(id=request.user.id)
            user.last_name =form.cleaned_data['last_name']
            user.save()             
            return redirect('/account/profile/'+str(request.user.id))
    else:
        user = User.objects.get(id=request.user.id)
        form = SchoolForm(instance=user)

    return render_to_response('form.html',{'form': form}, context_instance=RequestContext(request))
    
# 修改信箱
def adminemail(request):
    if request.method == 'POST':
        form = EmailForm(request.POST)
        if form.is_valid():
            user = User.objects.get(id=request.user.id)
            user.email =form.cleaned_data['email']
            user.save()              
            return redirect('/account/profile/'+str(request.user.id))
    else:
        user = User.objects.get(id=request.user.id)
        form = EmailForm(instance=user)

    return render_to_response('form.html',{'form': form}, context_instance=RequestContext(request))    

# 記錄積分項目
class LogListView(ListView):
    context_object_name = 'logs'
    paginate_by = 20
    template_name = 'account/log_list.html'
	
    def get_queryset(self):                                 
        if not self.kwargs['kind'] == "0" :
            queryset = PointHistory.objects.filter(user_id=self.kwargs['user_id'],kind=self.kwargs['kind']).order_by('-id')
        else :
            queryset = PointHistory.objects.filter(user_id=self.kwargs['user_id']).order_by('-id')		
        return queryset

    def get_context_data(self, **kwargs):
        context = super(LogListView, self).get_context_data(**kwargs)
        user_name = User.objects.get(id=self.kwargs['user_id']).first_name
        context.update({'user_name': user_name})
        return context		
        
# 超級管理員可以查看所有帳號
class UserListView(ListView):
    context_object_name = 'users'
    paginate_by = 20
    template_name = 'account/user_list.html'
    
    def get_queryset(self):      
        if self.request.GET.get('account') != None:
            keyword = self.request.GET.get('account')
            queryset = User.objects.filter(Q(username__icontains=keyword) | Q(first_name__icontains=keyword)).order_by('-id')
        else :
            queryset = User.objects.all().order_by('-id')				
        return queryset

    def get_context_data(self, **kwargs):
        context = super(UserListView, self).get_context_data(**kwargs)
        account = self.request.GET.get('account')
        context.update({'account': account})
        return context	
    
# Ajax 設為教師、取消教師
def make(request):
    user_id = request.POST.get('userid')
    action = request.POST.get('action')
    if user_id and action :
        user = User.objects.get(id=user_id)           
        try :
            group = Group.objects.get(name="active_teacher")	
        except ObjectDoesNotExist :
            group = Group(name="active_teacher")
            group.save()
        if action == 'set':            
            group.user_set.add(user)
            # create Message
            title = "<" + request.user.first_name + u">設您為教師"
            url = "/teacher/classroom"
            message = Message.create(title=title, url=url, time=timezone.now())
            message.save()                        
                    
            # message for group member
            messagepoll = MessagePoll.create(message_id = message.id,reader_id=user_id)
            messagepoll.save()    
        else :             
            group.user_set.remove(user)  
            # create Message
            title = "<"+ request.user.first_name + u">取消您為教師"
            url = "/"
            message = Message.create(title=title, url=url, time=timezone.now())
            message.save()                        
                    
            # message for group member
            messagepoll = MessagePoll.create(message_id = message.id,reader_id=user_id)
            messagepoll.save()               
        return JsonResponse({'status':'ok'}, safe=False)
    else:
        return JsonResponse({'status':user.first_name}, safe=False)        

def message(request, messagepoll_id):
    messagepoll = MessagePoll.objects.get(id=messagepoll_id)
    messagepoll.read = True
    messagepoll.save()
    message = Message.objects.get(id=messagepoll.message_id)
    return redirect(message.url)
    
# 列出所有私訊
class LineListView(ListView):
    model = Message
    context_object_name = 'messages'
    template_name = 'account/line_list.html'    
    paginate_by = 20
    
    def get_queryset(self):      
        queryset = Message.objects.filter(author_id=self.request.user.id, classroom_id=0-int(self.kwargs['classroom_id'])).order_by("-id")
        return queryset

    def get_context_data(self, **kwargs):
        context = super(LineListView, self).get_context_data(**kwargs)
        context['classroom_id'] = self.kwargs['classroom_id']
        return context	 
        
# 列出同學以私訊
class LineClassListView(ListView):
    model = Enroll
    context_object_name = 'enrolls'
    template_name = 'account/line_class.html'   
    
    def get_queryset(self):      
        queryset = Enroll.objects.filter(classroom_id=self.kwargs['classroom_id']).order_by("seat")
        return queryset
        
    # 限本班同學
    def render_to_response(self, context):
        if not is_classmate(self.request.user.id, self.kwargs['classroom_id']):
            return redirect('/')
        return super(LineClassListView, self).render_to_response(context)            
                
#新增一個私訊
class LineCreateView(CreateView):
    model = Message
    context_object_name = 'messages'    
    form_class = LineForm
    template_name = 'account/line_form.html'     

    def form_valid(self, form):
        self.object = form.save(commit=False)
        user_name = User.objects.get(id=self.request.user.id).first_name
        self.object.title = u"[私訊]" + user_name + ":" + self.object.title
        self.object.author_id = self.request.user.id
        self.object.save()
        self.object.url = "/account/line/detail/" + self.kwargs['classroom_id'] + "/" + str(self.object.id)
        self.object.classroom_id = 0 - int(self.kwargs['classroom_id'])
        self.object.save()
        # 訊息
        messagepoll = MessagePoll(message_id=self.object.id, reader_id=self.kwargs['user_id'], classroom_id=0-int(self.kwargs['classroom_id']))
        messagepoll.save()               
        return redirect("/account/line/"+self.kwargs['classroom_id'])       
        
    def get_context_data(self, **kwargs):
        context = super(LineCreateView, self).get_context_data(**kwargs)
        context['user_id'] = self.kwargs['user_id']
        context['classroom_id'] = self.kwargs['classroom_id']
        messagepolls = MessagePoll.objects.filter(reader_id=self.kwargs['user_id'],  classroom_id=0 - int(self.kwargs['classroom_id'])).order_by('-id')
        messages = []
        for messagepoll in messagepolls:
            message = Message.objects.get(id=messagepoll.message_id)
            if message.author_id == self.request.user.id :
                messages.append([message, messagepoll.read])
        context['messages'] = messages
        return context	 
        
# 查看私訊內容
def line_detail(request, classroom_id, message_id):
    message = Message.objects.get(id=message_id)
    messes = Message.objects.filter(author_id=message.author_id, classroom_id__lt=0).order_by("-id")
    try:
        messagepoll = MessagePoll.objects.get(message_id=message_id)
    except :
        pass
    return render_to_response('account/line_detail.html', {'lists':messes, 'classroom_id':classroom_id, 'message':message, 'messagepoll':messagepoll}, context_instance=RequestContext(request))


# 列出所有日期訪客
class VisitorListView(ListView):
    model = Visitor
    context_object_name = 'visitors'
    template_name = 'account/visitor_list.html'    
    paginate_by = 20
    
    def get_queryset(self):     
        visitors = Visitor.objects.all().order_by('-id')
        queryset = []
        for visitor in visitors:
            queryset.append([int(str(visitor.date)[0:4]), int(str(visitor.date)[4:6]),int(str(visitor.date)[6:8]),visitor])
        return queryset

    def get_context_data(self, **kwargs):
        context = super(VisitorListView, self).get_context_data(**kwargs)
        first_element = Visitor.objects.all().order_by("-id")[0]
        end_year = int(str(first_element.date)[0:4])
        last_element = Visitor.objects.all().order_by("id")[0]
        start_year = int(str(last_element.date)[0:4])
        context['height'] = 200+ (end_year-start_year)*200;
        #context['height'] = last_element.date
        visitors = Visitor.objects.all().order_by('id')
        queryset = []
        for visitor in visitors:
            queryset.append([int(str(visitor.date)[0:4]), int(str(visitor.date)[4:6]),int(str(visitor.date)[6:8]),visitor])
        context['total_visitors'] = queryset
        return context	   
			
# 列出單日日期訪客
class VisitorLogListView(ListView):
    model = VisitorLog
    context_object_name = 'visitorlogs'
    template_name = 'account/visitorlog_list.html'    
    paginate_by = 50
    
    def get_queryset(self):       
        queryset = VisitorLog.objects.filter(visitor_id=self.kwargs['visitor_id']).order_by('-id')
        return queryset
        
    def render_to_response(self, context):
        if not self.request.user.is_authenticated():
            return redirect('/')
        return super(VisitorLogListView, self).render_to_response(context)
        
# 下載檔案
def download(request, filename):
    #down_file = File.objects.get(name = filename)
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DOWNLOAD_URL = BASE_DIR+"/download/"
    file_path = DOWNLOAD_URL + filename
    file_name = filename
    fp = open(file_path, 'rb')
    response = HttpResponse(fp.read())
    fp.close()
    mime = MimeTypes()
    type, encoding = mime.guess_type(file_name)
    if type is None:
        type = 'application/octet-stream'
    response['Content-Type'] = type
    response['Content-Length'] = str(os.stat(file_path).st_size)
    if encoding is not None:
        response['Content-Encoding'] = encoding
    if u'WebKit' in request.META['HTTP_USER_AGENT']:
        filename_header = 'filename=%s' % file_name.encode('utf-8')
    elif u'MSIE' in request.META['HTTP_USER_AGENT']:
        filename_header = ''
    else:
        filename_header = 'filename*=UTF-8\'\'%s' % urllib.quote(file_name.encode('utf-8'))
    response['Content-Disposition'] = 'attachment; ' + filename_header  
    return response

def avatar(request):
    profile = Profile.objects.get(user = request.user)   
    return render_to_response('account/avatar.html', {'avatar':profile.avatar}, context_instance=RequestContext(request))
