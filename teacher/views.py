# -*- coding: UTF-8 -*-
from django.shortcuts import render
from django.shortcuts import render_to_response, redirect
from teacher.models import Classroom, ImportUser
from student.models import Enroll
from account.models import Profile, Message, MessagePoll, MessageFile
from django.views.generic import ListView, DetailView, CreateView
from .forms import ClassroomForm, UploadFileForm, AnnounceForm
from account.forms import PasswordForm, RealnameForm
from django.template import RequestContext
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from wsgiref.util import FileWrapper
from django.forms.models import model_to_dict
import django_excel as excel
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from django.db.models import Q
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage
from uuid import uuid4

# 判斷是否為授課教師
def is_teacher(user, classroom_id):
    return user.groups.filter(name='active_teacher').exists() and Classroom.objects.filter(teacher_id=user.id, id=classroom_id).exists()

# 列出所有課程
class ClassroomListView(ListView):
    model = Classroom
    context_object_name = 'classrooms'
    #paginate_by = 1000
    def get_queryset(self):    
        queryset = Classroom.objects.filter(teacher_id=self.request.user.id).order_by("-id")
        return queryset
      
#新增一個課程
class ClassroomCreateView(CreateView):
    model = Classroom
    form_class = ClassroomForm
    template_name = 'form.html'
    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.teacher_id = self.request.user.id
        self.object.save()
        # 將教師設為0號學生
        enroll = Enroll(classroom_id=self.object.id, student_id=self.request.user.id, seat=0)
        enroll.save()           
        return redirect("/teacher/classroom")        
        
# 修改選課密碼
def classroom_edit(request, classroom_id):
    # 限本班任課教師
    if not is_teacher(request.user, classroom_id):
        return redirect("homepage")
    classroom = Classroom.objects.get(id=classroom_id)
    if request.method == 'POST':
        form = ClassroomForm(request.POST)
        if form.is_valid():
            classroom.name =form.cleaned_data['name']
            classroom.password = form.cleaned_data['password']
            classroom.save()               
            return redirect('/teacher/classroom')
    else:
        form = ClassroomForm(instance=classroom)

    return render_to_response('form.html',{'form': form}, context_instance=RequestContext(request))        

# 退選
def unenroll(request, enroll_id, classroom_id):
    # 限本班任課教師
    if not is_teacher(request.user, classroom_id):
        return redirect("/")    
    enroll = Enroll.objects.get(id=enroll_id)
    enroll.delete()
    classroom_name = Classroom.objects.get(id=classroom_id).name
    # 記錄系統事件
    if is_event_open(request) :        
        log = Log(user_id=request.user.id, event=u'退選<'+classroom_name+'>')
        log.save()       
    return redirect('/student/classmate/'+classroom_id)  
	
# 超級管理員可以查看所有帳號
class StudentListView(ListView):
    context_object_name = 'users'
    paginate_by = 40
    template_name = 'teacher/student_list.html'
    
    def get_queryset(self):      
        username = username__icontains=self.request.user.username+"_"
        if self.request.GET.get('account') != None:
            keyword = self.request.GET.get('account')
            queryset = User.objects.filter(Q(username__icontains=username+keyword) | (Q(first_name__icontains=keyword) & Q(username__icontains=username))).order_by('-id')
        else :
            queryset = User.objects.filter(username__icontains=username).order_by('-id')				
        return queryset

    def get_context_data(self, **kwargs):
        context = super(StudentListView, self).get_context_data(**kwargs)
        account = self.request.GET.get('account')
        context.update({'account': account})
        return context	
      
# Create your views here.
def import_sheet(request):
    if False:
        return redirect("/")
    if request.method == "POST":
        form = UploadFileForm(request.POST,
                              request.FILES)
        if form.is_valid():
            ImportUser.objects.all().delete()
            request.FILES['file'].save_to_database(
                name_columns_by_row=0,
                model=ImportUser,
                mapdict=['username', 'first_name', 'password', 'email'])
            users = ImportUser.objects.all()
            return render(request, 'teacher/import_student.html',{'users':users})
        else:
            return HttpResponseBadRequest()
    else:	
        form = UploadFileForm()
    return render(
        request,
        'teacher/upload_form.html',
        {
            'form': form,
            'title': 'Excel file upload and download example',
            'header': ('Please choose any excel file ' +
                       'from your cloned repository:')
        })
	
# Create your views here.
def import_student(request):
    if False:
        return redirect("/")
           
    users = ImportUser.objects.all()
    for user in users:
        try:
            account = User.objects.get(username=request.user.username+"_"+user.username)
        except ObjectDoesNotExist:
            username = request.user.username+"_"+user.username
            new_user = User(username=username, first_name=user.first_name, password=user.password, email=username+"@edu.tw")
            # Set the chosen password                 
            new_user.set_password(user.password)
            # Save the User object
            new_user.save()
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
    return redirect('/teacher/student/list')	

# 修改密碼
def password(request, user_id):
    user = User.objects.get(id=user_id)
    if not user.username.startswith(request.user.username):
        return redirect("/")
    if request.method == 'POST':
        form = PasswordForm(request.POST)
        if form.is_valid():
            user = User.objects.get(id=user_id)
            user.set_password(request.POST['password'])
            user.save()            
            return redirect('/teacher/student/list/')
    else:
        form = PasswordForm()
        user = User.objects.get(id=user_id)

    return render_to_response('form.html',{'form': form, 'user':user}, context_instance=RequestContext(request))

# 修改真實姓名
def realname(request, user_id):
    user = User.objects.get(id=user_id)
    if not user.username.startswith(request.user.username):
        return redirect("/")
    if request.method == 'POST':
        form = RealnameForm(request.POST)
        if form.is_valid():
            user = User.objects.get(id=user_id)
            user.first_name =form.cleaned_data['first_name']
            user.save()               
            return redirect('/teacher/student/list/')
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
						
# 列出所有公告
class AnnounceListView(ListView):
    model = Message
    context_object_name = 'messages'
    template_name = 'teacher/announce_list.html'    
    paginate_by = 20
		
    def get_queryset(self): 
        queryset = Message.objects.filter(classroom_id=self.kwargs['classroom_id'], author_id=self.request.user.id).order_by("-id")
        return queryset
        
    def get_context_data(self, **kwargs):
        context = super(AnnounceListView, self).get_context_data(**kwargs)
        context['classroom'] = Classroom.objects.get(id=self.kwargs['classroom_id'])
        return context	    

    # 限本班任課教師        
    def render_to_response(self, context):
        if not is_teacher(self.request.user, self.kwargs['classroom_id']):
            return redirect('/')
        return super(AnnounceListView, self).render_to_response(context)        
        
#新增一個公告
class AnnounceCreateView(CreateView):
    model = Message
    form_class = AnnounceForm
    template_name = 'teacher/announce_form.html'     
    def form_valid(self, form):
        classrooms = self.request.POST.getlist('classrooms')
        files = self.request.FILES.getlist('files')
        self.object = form.save(commit=False)
        filenames = []
        for file in files:
            fs = FileSystemStorage()
            filename = uuid4().hex
            fs.save("static/message/"+filename, file)
            filenames.append([filename, file.name])
        for classroom_id in classrooms:
            message = Message()
            message.title = u"[公告]" + self.object.title
            message.author_id = self.request.user.id	
            message.classroom_id = classroom_id
            message.content = self.object.content
            message.save()
            message.url = "/teacher/announce/detail/" + str(message.id)
            message.save()
            for filename in filenames:
                    messagefile = MessageFile(message_id=message.id, filename=filename[0], before_name=filename[1])
                    messagefile.save()
            # 班級學生訊息
            enrolls = Enroll.objects.filter(classroom_id=classroom_id)
            for enroll in enrolls:
                messagepoll = MessagePoll(message_id=message.id, reader_id=enroll.student_id, classroom_id=classroom_id)
                messagepoll.save()            
        return redirect("/teacher/announce/"+self.kwargs['classroom_id'])       
        
    def get_context_data(self, **kwargs):
        context = super(AnnounceCreateView, self).get_context_data(**kwargs)
        context['classroom'] = Classroom.objects.get(id=self.kwargs['classroom_id'])
        context['classrooms'] = Classroom.objects.filter(teacher_id=self.request.user.id).order_by("-id")
        return context	   
        
    # 限本班任課教師        
    def render_to_response(self, context):
        if not is_teacher(self.request.user, self.kwargs['classroom_id']):
            return redirect('/')
        return super(AnnounceCreateView, self).render_to_response(context)          
        
# 查看藝郎某項目
def announce_detail(request, message_id):
    message = Message.objects.get(id=message_id)
    classroom = Classroom.objects.get(id=message.classroom_id)
    
    announce_reads = []
    
    messagepolls = MessagePoll.objects.filter(message_id=message_id, classroom_id=classroom.id)
    for messagepoll in messagepolls:
        enroll = Enroll.objects.get(classroom_id=message.classroom_id, student_id=messagepoll.reader_id)
        announce_reads.append([enroll.seat, enroll.student.first_name, messagepoll])
    
    def getKey(custom):
        return custom[0]	
    announce_reads = sorted(announce_reads, key=getKey)

    files = MessageFile.objects.filter(message_id=message_id)
    return render_to_response('teacher/announce_detail.html', {'files':files, 'message':message, 'classroom':classroom, 'announce_reads':announce_reads}, context_instance=RequestContext(request))

def announce_download(request, messagefile_id):
    messagefile = MessageFile.objects.get(id=messagefile_id)
    download =  settings.BASE_DIR + "/static/message/" + messagefile.filename
    wrapper = FileWrapper(file( download, "r" ))
    filename = messagefile.before_name
    response = HttpResponse(wrapper, content_type = 'application/force-download')
    #response = HttpResponse(content_type='application/force-download')
    response['Content-Disposition'] = 'attachment; filename={0}'.format(filename.encode('utf8'))
    # It's usually a good idea to set the 'Content-Length' header too.
    # You can also set any other required headers: Cache-Control, etc.
    return response

    