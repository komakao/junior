# -*- coding: UTF-8 -*-
from django.shortcuts import render
from django.shortcuts import render_to_response, redirect
from teacher.models import Classroom, ImportUser
from student.models import Enroll
from account.models import Profile, Message, MessagePoll
from django.views.generic import ListView, DetailView, CreateView
from .forms import ClassroomForm, UploadFileForm
from django.template import RequestContext
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from wsgiref.util import FileWrapper
from django.forms.models import model_to_dict
import django_excel as excel
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

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
  
# 超級管理員可以查看所有帳號
class StudentListView(ListView):
    context_object_name = 'users'
    paginate_by = 40
    template_name = 'teacher/student_list.html'
    
    def get_queryset(self):      
        if self.request.GET.get('account') != None:
            keyword = self.request.GET.get('account')
            queryset = User.objects.filter(Q(username__icontains=self.request.user.username+"_"+keyword) | Q(first_name__icontains=keyword)).order_by('-id')
        else :
            queryset = User.objects.filter(username__icontains=self.request.user.username+"_").order_by('-id')				
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
            new_user = User(username=request.user.username+"_"+user.username, first_name=user.first_name, password=user.password, email=user.email)
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
