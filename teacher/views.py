# -*- coding: UTF-8 -*-
from django.shortcuts import render
from django.shortcuts import render_to_response, redirect
from teacher.models import Classroom, ImportUser
from student.models import Enroll, Work, EnrollGroup, Assistant, WorkFile
from account.models import Profile, Message, MessagePoll, MessageFile, PointHistory
from student.lesson import *
from django.views.generic import ListView, DetailView, CreateView
from .forms import ClassroomForm, UploadFileForm, AnnounceForm, ScoreForm
from account.forms import PasswordForm, RealnameForm
from django.template import RequestContext
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from wsgiref.util import FileWrapper
from django.forms.models import model_to_dict
import django_excel as excel
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.utils import timezone
from django.db.models import Q
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage
from uuid import uuid4
from django.contrib.auth.decorators import login_required
from collections import OrderedDict
from account.avatar import *

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

# 列出班級所有作業
def work(request, classroom_id):
    # 限本班任課教師
    if not is_teacher(request.user, classroom_id):
        return redirect("/")    
    classroom = Classroom.objects.get(id=classroom_id)         
    lesson_dict = OrderedDict()
    lesson = Classroom.objects.get(id=classroom_id).lesson
    for unit in lesson_list[lesson-1][1]:
        for assignment in unit[1]:
            lesson_dict[assignment[2]] = assignment[0]
    return render_to_response('teacher/work.html', {'lesson':lesson, 'lesson_dict':sorted(lesson_dict.iteritems()), 'classroom': classroom}, context_instance=RequestContext(request))
			
# 列出某作業所有同學名單
def score(request, classroom_id, lesson, index):
    # 限本班任課教師
    if not is_teacher(request.user, classroom_id):
        return redirect("/")    
    enrolls = Enroll.objects.filter(classroom_id=classroom_id)
    classroom_name = Classroom.objects.get(id=classroom_id).name
    classmate_work = []
    scorer_name = ""
    for enroll in enrolls:
        try:    
            work = Work.objects.get(user_id=enroll.student_id, index=index, lesson=lesson)
            if work.scorer > 0 :
                scorer = User.objects.get(id=work.scorer)
                scorer_name = scorer.first_name
            else :
                scorer_name = "1"
        except ObjectDoesNotExist:
            work = Work(index=index, user_id=0, lesson=lesson)
        except MultipleObjectsReturned:
            work =  Work.objects.filter(user_id=enroll.student_id, index=index, lesson=lesson).order_by("-id")[0]
        try:
            group_name = EnrollGroup.objects.get(id=enroll.group).name
        except ObjectDoesNotExist:
            group_name = "沒有組別"
        assistant = Assistant.objects.filter(classroom_id=classroom_id, student_id=enroll.student_id, lesson=index)
        if assistant.exists():
            classmate_work.append([enroll,work,1, scorer_name, group_name])
        else :
            classmate_work.append([enroll,work,0, scorer_name, group_name])            
    lesson_dict = {}
    for unit in lesson_list[int(lesson)-1][1]:
        for assignment in unit[1]:
            lesson_dict[assignment[2]] = assignment[0]    
    assignment = lesson_dict[int(index)]
		
    def getKey(custom):
        return custom[0].seat
	
    classmate_work = sorted(classmate_work, key=getKey)
         
    return render_to_response('teacher/score.html',{'lesson':lesson, 'classmate_work': classmate_work, 'classroom_id':classroom_id, 'assignment':assignment, 'index': index}, context_instance=RequestContext(request))


# 教師評分
def scoring(request, classroom_id, user_id, lesson, index):
    user = User.objects.get(id=user_id)
    enroll = Enroll.objects.get(classroom_id=classroom_id, student_id=user_id)
    classroom = Classroom.objects.get(id=classroom_id)
    lesson_dict = {}
    for unit in lesson_list[int(lesson)-1][1]:
        for assignment in unit[1]:
            lesson_dict[assignment[2]] = assignment[0]    
    assignment = lesson_dict[int(index)]		
    try:
        assistant = Assistant.objects.filter(classroom_id=classroom_id,lesson=index,student_id=request.user.id)
    except ObjectDoesNotExist:            
        if not is_teacher(request.user, classroom_id):
            return render_to_response('message.html', {'message':"您沒有權限"}, context_instance=RequestContext(request))
        
    try:
        work3 = Work.objects.get(user_id=user_id, index=index, lesson=lesson)
    except ObjectDoesNotExist:
        work3 = Work(index=index, user_id=user_id, lesson=lesson)
    except MultipleObjectsReturned:
        work3 =  Work.objects.filter(user_id=user_id, index=index, lesson=lesson).order_by("-id")[0]				
				
    workfiles = WorkFile.objects.filter(work_id=work3.id).order_by("-id")
		
    if request.method == 'POST':
        form = ScoreForm(request.user, request.POST)
        if form.is_valid():
            work = Work.objects.filter(index=index, user_id=user_id, lesson=lesson)
            if not work.exists():
                work = Work(lesson=lesson, index=index, user_id=user_id, score=form.cleaned_data['score'], publication_date=timezone.now())
                work.save()                  
            else:
                if work[0].score < 0 :   
                    # 小老師
                    if not is_teacher(request.user, classroom_id):
    	                # credit
                        update_avatar(request.user.id, 2, 1)
                        # History
                        history = PointHistory(user_id=request.user.id, kind=2, message='1分--小老師:<'+assignment+'><'+enroll.student.first_name.encode('utf-8')+'>', url=request.get_full_path())
                        history.save()				
    
				    # credit
                    update_avatar(enroll.student_id, 1, 1)
                    # History
                    history = PointHistory(user_id=user_id, kind=1, message='1分--作業受評<'+assignment+'><'+request.user.first_name.encode('utf-8')+'>', url=request.get_full_path())
                    history.save()		                        
                
                work.update(score=form.cleaned_data['score'])
                work.update(scorer=request.user.id)                 
						
            if is_teacher(request.user, classroom_id):         
                if form.cleaned_data['assistant']:
                    try :
					    assistant = Assistant.objects.get(student_id=user_id, classroom_id=classroom_id, lesson=index)
                    except ObjectDoesNotExist:
                        assistant = Assistant(student_id=user_id, classroom_id=classroom_id, lesson=index)
                        assistant.save()	
                        
                    # create Message
                    title = "<" + assistant.student.first_name.encode("utf-8") + u">擔任小老師<".encode("utf-8") + assignment + ">"
                    url = "/teacher/score_peer/" + lesson + "/" + str(index) + "/" + classroom_id + "/" + str(enroll.group) 
                    message = Message.create(title=title, url=url, time=timezone.now())
                    message.save()                        
                    
                    group = Enroll.objects.get(classroom_id=classroom_id, student_id=assistant.student_id).group
                    if group > 0 :
                        enrolls = Enroll.objects.filter(group = group)
                        for enroll in enrolls:
                            # message for group member
                            messagepoll = MessagePoll.create(message_id = message.id,reader_id=enroll.student_id)
                            messagepoll.save()
                    
                return redirect('/teacher/score/'+classroom_id+'/'+lesson+"/"+index)
            else: 
                return redirect('/teacher/score_peer/'+ lesson + "/" + index+'/'+classroom_id+'/'+str(enroll.group))

    else:
        work = Work.objects.filter(lesson=lesson, index=index, user_id=user_id)
        if not work.exists():
            form = ScoreForm(user=request.user)
        else:
            form = ScoreForm(instance=work[0], user=request.user)
    return render_to_response('teacher/scoring.html', {'form': form,'workfiles':workfiles, 'index': index, 'work':work3, 'student':user, 'classroom':classroom, 'lesson':lesson, 'assignment':assignment}, context_instance=RequestContext(request))

# 小老師評分名單
def score_peer(request, lesson, index, classroom_id, group):
    lesson_dict = {}
    for unit in lesson_list[int(lesson)-1][1]:
        for assignment in unit[1]:
            lesson_dict[assignment[2]] = assignment[0]    
    assignment = lesson_dict[int(index)]		
    try:
        assistant = Assistant.objects.get(lesson=index, classroom_id=classroom_id, student_id=request.user.id)
    except ObjectDoesNotExist:
        return redirect("/student/group/work/"+lesson+"/"+index+"/"+classroom_id)

    enrolls = Enroll.objects.filter(classroom_id=classroom_id, group=group)
    classmate_work = []
    workfiles = []
    for enroll in enrolls:
        if not enroll.student_id == request.user.id : 
            scorer_name = ""
            try:    
                work = Work.objects.get(lesson=lesson, user_id=enroll.student.id, index=index)
                if work.scorer > 0 :
                    scorer = User.objects.get(id=work.scorer)
                    scorer_name = scorer.first_name
            except ObjectDoesNotExist:
                work = Work(lesson=lesson, index=index, user_id=1)
            workfiles = WorkFile.objects.filter(work_id=work.id)
            classmate_work.append([enroll.student,work,1, scorer_name])
    return render_to_response('teacher/score_peer.html',{'assignment':assignment, 'enrolls':enrolls, 'workfiles': workfiles, 'classmate_work': classmate_work, 'classroom_id':classroom_id, 'lesson':lesson, 'index': index}, context_instance=RequestContext(request))

# 設定為小老師
def assistant(request, classroom_id, user_id, lesson, index):
    lesson_dict = {}
    for unit in lesson_list[int(lesson)-1][1]:
        for assignment in unit[1]:
            lesson_dict[assignment[2]] = assignment[0]    
    assignment = lesson_dict[int(index)]			
    # 限本班任課教師
    if not is_teacher(request.user, classroom_id):
        return redirect("/")    
    user = User.objects.get(id=user_id)
    assistant = Assistant(student_id=user_id, classroom_id=classroom_id, lesson=index)
    assistant.save()
    
    group = Enroll.objects.get(classroom_id=classroom_id, student_id=assistant.student_id).group
    # create Message
    title = "<" + assistant.student.first_name.encode("utf-8") + u">擔任小老師<".encode("utf-8") + assignment + ">"
    url = "/teacher/score_peer/" + str(lesson) + "/" + index + "/" + classroom_id + "/" + str(group) 
    message = Message.create(title=title, url=url, time=timezone.now())
    message.save()                        
        
    if group > 0 :
        enrolls = Enroll.objects.filter(group = group)
        for enroll in enrolls:
            # message for group member
            messagepoll = MessagePoll.create(message_id = message.id,reader_id=enroll.student_id)
            messagepoll.save()
    
    return redirect('/teacher/score/'+str(assistant.classroom_id)+"/"+lesson+"/"+index)    
    
# 取消小老師
def assistant_cancle(request, classroom_id, user_id, lesson, index):
    lesson_dict = {}
    for unit in lesson_list[int(lesson)-1][1]:
        for assignment in unit[1]:
            lesson_dict[assignment[2]] = assignment[0]    
    assignment = lesson_dict[int(index)]			
    # 限本班任課教師
    if not is_teacher(request.user, classroom_id):
        return redirect("homepage")    
    user = User.objects.get(id=user_id)   
    assistant = Assistant.objects.get(student_id=user_id, classroom_id=classroom_id, lesson=index)
    assistant.delete()
    
    # create Message
    title = "<" + assistant.student.first_name.encode("utf-8") + u">取消小老師<".encode("utf-8") + assignment + ">"
    url = "/student/group/work/" + str(lesson) + "/" + index + "/" + classroom_id 
    message = Message.create(title=title, url=url, time=timezone.now())
    message.save()                        
        
    group = Enroll.objects.get(classroom_id=classroom_id, student_id=assistant.student_id).group
    if group > 0 :
        enrolls = Enroll.objects.filter(group = group)
        for enroll in enrolls:
            # message for group member
            messagepoll = MessagePoll.create(message_id = message.id,reader_id=enroll.student_id)
            messagepoll.save()
   
    return redirect('/teacher/score/'+str(assistant.classroom_id)+"/"+lesson+"/"+index)    
    
# 心得
def memo(request, classroom_id):
        # 限本班任課教師
        if not is_teacher(request.user, classroom_id):
            return redirect("homepage")    
        enrolls = Enroll.objects.filter(classroom_id=classroom_id).order_by("seat")
        classroom_name = Classroom.objects.get(id=classroom_id).name
        # 記錄系統事件
        if is_event_open(request) :            
            log = Log(user_id=request.user.id, event=u'查閱心得<'+classroom_name+'>')
            log.save()  
        return render_to_response('teacher/memo.html', {'enrolls':enrolls, 'classroom_name':classroom_name}, context_instance=RequestContext(request))

# 評分某同學某進度心得
@login_required
def check(request, user_id, unit,classroom_id):
    # 限本班任課教師
    if not is_teacher(request.user, classroom_id):
        return redirect("homepage")

    user_name = User.objects.get(id=user_id).first_name
    del lesson_list[:]
    reset()
    works = Work.objects.filter(lesson=lesson, user_id=user_id)
    for work in works:
        lesson_list[work.index-1].append(work.score)
        lesson_list[work.index-1].append(work.publication_date)
        if work.score > 0 :
            score_name = User.objects.get(id=work.scorer).first_name
            lesson_list[work.index-1].append(score_name)
        else :
            lesson_list[work.index-1].append("尚未評分!")
        lesson_list[work.index-1].append(work.memo)
    c = 0
    for lesson in lesson_list:
        assistant = Assistant.objects.filter(student_id=user_id, lesson=c+1)
        if assistant.exists() :
            lesson.append("V")
        else :
            lesson.append("")
        c = c + 1
    user = User.objects.get(id=user_id)

    if unit == "1" :
        if request.method == 'POST':
            form = CheckForm1(request.POST)
            if form.is_valid():
                enroll = Enroll.objects.get(student_id=user_id, classroom_id=classroom_id)
                enroll.score_memo1=form.cleaned_data['score_memo1']
                enroll.save()
                
                # 記錄系統事件
                if is_event_open(request) :                    
                    log = Log(user_id=request.user.id, event=u'批改12堂課心得<'+user_name+'>')
                    log.save()                  
						
                if form.cleaned_data['certificate']:		
                    return redirect('/certificate/make_certification/'+unit+'/'+str(enroll.id)+'/certificate')
                else:
                    return redirect('/teacher/memo/'+classroom_id)
        else:
            enroll = Enroll.objects.get(student_id=user_id, classroom_id=classroom_id)
            form = CheckForm1(instance=enroll)
    elif unit == "2":
        if request.method == 'POST':
            form = CheckForm2(request.POST)
            if form.is_valid():
                enroll = Enroll.objects.get(student_id=user_id, classroom_id=classroom_id)
                enroll.score_memo2=form.cleaned_data['score_memo2']
                enroll.save()

                # 記錄系統事件
                if is_event_open(request) :                    
                    log = Log(user_id=request.user.id, event=u'批改實戰入門心得<'+user_name+'>')
                    log.save()      
						
                if form.cleaned_data['certificate']:		
                    return redirect('/certificate/make_certification/'+unit+'/'+str(enroll.id)+'/certificate')
                else:
                    return redirect('/teacher/memo/'+classroom_id)					
        else:
            enroll = Enroll.objects.get(student_id=user_id, classroom_id=classroom_id)
            form = CheckForm2(instance=enroll)
    elif unit == "3":
        if request.method == 'POST':
            form = CheckForm3(request.POST)
            if form.is_valid():
                enroll = Enroll.objects.get(student_id=user_id, classroom_id=classroom_id)
                enroll.score_memo3=form.cleaned_data['score_memo3']
                enroll.save()
                # 記錄系統事件
                if is_event_open(request) :                    
                    log = Log(user_id=request.user.id, event=u'批改實戰進擊心得<'+user_name+'>')
                    log.save() 
						
                if form.cleaned_data['certificate']:		
                    return redirect('/certificate/make_certification/'+unit+'/'+str(enroll.id)+'/certificate')
                else:
                    return redirect('/teacher/memo/'+classroom_id)							
        else:
            enroll = Enroll.objects.get(student_id=user_id, classroom_id=classroom_id)
            form = CheckForm3(instance=enroll)

    else:
        if request.method == 'POST':
            form = CheckForm4(request.POST)
            if form.is_valid():
                enroll = Enroll.objects.get(student_id=user_id, classroom_id=classroom_id)
                enroll.score_memo4=form.cleaned_data['score_memo4']
                enroll.save()
                # 記錄系統事件
                if is_event_open(request) :                    
                    log = Log(user_id=request.user.id, event=u'批改實戰高手心得<'+user_name+'>')
                    log.save() 						
                if form.cleaned_data['certificate']:		
                    return redirect('/certificate/make_certification/'+unit+'/'+str(enroll.id)+'/certificate')
                else:
                    return redirect('/teacher/memo/'+classroom_id)							
        else:
            enroll = Enroll.objects.get(student_id=user_id, classroom_id=classroom_id)
            form = CheckForm4(instance=enroll)	
    return render_to_response('teacher/check.html', {'form':form, 'works':works, 'lesson_list':lesson_list, 'student': user, 'unit':unit, 'classroom_id':classroom_id}, context_instance=RequestContext(request))

# 列出分組12堂課所有作業
def work_group(request, classroom_id):
        # 限本班任課教師
        if not is_teacher(request.user, classroom_id):
            return redirect("/")    
        classroom = Classroom.objects.get(id=classroom_id)
        lesson = Classroom.objects.get(id=classroom_id).lesson
        groups = [group for group in EnrollGroup.objects.filter(classroom_id=classroom_id)]				
        enroll_pool = [enroll for enroll in Enroll.objects.filter(classroom_id=classroom_id).order_by('seat')]
        student_ids = map(lambda a: a.student_id, enroll_pool)
        work_pool = Work.objects.filter(user_id__in=student_ids, lesson=classroom.lesson)
        user_pool = [user for user in User.objects.filter(id__in=work_pool.values('scorer'))]
        assistant_pool = [assistant for assistant in Assistant.objects.filter(classroom_id=classroom_id)]				
        lessons = []		
        lesson_dict = OrderedDict()
        for unit1 in lesson_list[int(lesson)-1][1]:
            for assignment in unit1[1]:
                student_groups = []													
                for group in groups:
                    members = filter(lambda u: u.group == group.id, enroll_pool)
                    group_assistants = []
                    works = []
                    scorer_name = ""
                    for member in members:
                        work = filter(lambda w: w.index == assignment[2] and w.user_id == member.student_id, work_pool)
                        if work:
                            work = work[0]
                            scorer = filter(lambda u: u.id == work.scorer, user_pool)
                            scorer_name = scorer[0].first_name if scorer else 'X'
                        else:
                            work = Work(index=assignment[2], user_id=1, score=-2)
                        works.append([member, work.score, scorer_name, work.memo])
                        assistant = filter(lambda a: a.student_id == member.student_id and a.lesson == assignment[2], assistant_pool)
                        if assistant:
                            group_assistants.append(member)
                    group_name = EnrollGroup.objects.get(id=group.id).name
                    student_groups.append([group, works, group_assistants, group_name])
                lesson_dict[assignment[2]] = [assignment, student_groups]
        return render_to_response('teacher/work_groups.html', {'lesson_dict':sorted(lesson_dict.iteritems()),'classroom':classroom}, context_instance=RequestContext(request))
 						
		