# -*- coding: UTF-8 -*-
from django.shortcuts import render_to_response, redirect
from django.contrib.auth.models import User
from django.template import RequestContext
from account.models import Profile, VisitorLog
from django.views.generic import ListView, CreateView
from django.shortcuts import render
from account.avatar import *
from student.lesson import *
from student.models import Enroll, EnrollGroup, Work, WorkFile
from account.models import Message, MessagePoll
from show.models import Round
from teacher.models import Classroom
from student.forms import EnrollForm, GroupForm, SubmitForm, SeatForm, GroupSizeForm
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.contrib.auth.decorators import login_required
from django.core.files.storage import FileSystemStorage
from uuid import uuid4
from django.utils import timezone
from django.utils.timezone import localtime
from collections import OrderedDict
# 判斷是否為授課教師
def is_teacher(user, classroom_id):
    return  user.groups.filter(name='active_teacher').exists() and Classroom.objects.filter(teacher_id=user.id, id=classroom_id).exists()

# 分類課程    
def lessons(request, lesson):       
        return render_to_response('student/lessons.html', {'lesson': lesson, 'lesson_list': lesson_list}, context_instance=RequestContext(request))

# 課程內容
def lesson(request, lesson, unit, index):
        scores = []
        workfiles = []
        work_index = lesson_list[int(lesson)-1][1][int(unit)-1][1][int(index)-1][2]	
        works = Work.objects.filter(index=work_index, user_id=request.user.id)
        try:
            filepath = request.FILES['file']
        except :
            filepath = False
        if request.method == 'POST':
            if filepath :
                myfile = request.FILES['file']
                fs = FileSystemStorage()
                filename = uuid4().hex
                fs.save("static/work/"+str(request.user.id)+"/"+filename, myfile)
						
            form = SubmitForm(request.POST, request.FILES)

            if not works.exists():
                if form.is_valid():
                    work = Work(index=work_index, user_id=request.user.id, memo=form.cleaned_data['memo'], publication_date=timezone.now())
                    work.save()
                    workfile = WorkFile(work_id=work.id, filename=filename)
                    workfile.save()
										# credit
                    update_avatar(request.user.id, 1, 2)
                    # History
                    history = PointHistory(user_id=request.user.id, kind=1, message='2分--繳交作業<'+lesson_list[int(index)-1][2]+'>', url=request.get_full_path())
                    history.save()
            else:
                if form.is_valid():
                    works.update(memo=form.cleaned_data['memo'],publication_date=timezone.localtime(timezone.now()))
                    workfile = WorkFile(work_id=works[0].id, filename=filename)
                    workfile.save()
                else :
                    works.update(memo=form.cleaned_data['memo'])           
            return redirect('/student/lesson/'+lesson+'/'+unit+"/"+index+"#tab3")
        else:
            if not works.exists():
                form = SubmitForm()
            else:
                workfiles = WorkFile.objects.filter(work_id=works[0].id).order_by("-id")							
                form = SubmitForm(instance=works[0])
                if len(workfiles)>0 and works[0].scorer>0: 
                    score_name = User.objects.get(id=works[0].scorer).first_name
                    scores = [works[0].score, score_name]
        lesson_name = lesson_list[int(lesson)-1][1][int(unit)-1][1][int(index)-1][0]	
        return render_to_response('student/lesson.html', {'index':index, 'form': form, 'unit':unit, 'lesson':lesson, 'lesson_name': lesson_name, 'scores':scores, 'workfiles': workfiles}, context_instance=RequestContext(request))
        
# 查看班級學生
def classmate(request, classroom_id):
        enrolls = Enroll.objects.filter(classroom_id=classroom_id).order_by("seat")
        enroll_group = []
        classroom_name=Classroom.objects.get(id=classroom_id).name
        for enroll in enrolls:
            login_times = len(VisitorLog.objects.filter(user_id=enroll.student_id))
            if enroll.group > 0 :
                enroll_group.append([enroll, EnrollGroup.objects.get(id=enroll.group).name, login_times])
            else :
                enroll_group.append([enroll, "沒有組別", login_times])                      
        return render_to_response('student/classmate.html', {'classroom_name':classroom_name, 'enroll_group':enroll_group}, context_instance=RequestContext(request))

# 顯示所有組別
def group(request, classroom_id):
        student_groups = []
        classroom = Classroom.objects.get(id=classroom_id)
        group_open = Classroom.objects.get(id=classroom_id).group_open        
        groups = EnrollGroup.objects.filter(classroom_id=classroom_id)
        try:
                student_group = Enroll.objects.get(student_id=request.user.id, classroom_id=classroom_id).group
        except ObjectDoesNotExist :
                student_group = []		
        for group in groups:
            enrolls = Enroll.objects.filter(classroom_id=classroom_id, group=group.id)
            student_groups.append([group, enrolls, classroom.group_size-len(enrolls)])
            
        #找出尚未分組的學生
        def getKey(custom):
            return custom.seat	
        enrolls = Enroll.objects.filter(classroom_id=classroom_id)
        nogroup = []
        for enroll in enrolls:
            if enroll.group == 0 :
		        nogroup.append(enroll)		
	    nogroup = sorted(nogroup, key=getKey)  
        return render_to_response('student/group.html', {'nogroup': nogroup, 'group_open': group_open, 'student_groups':student_groups, 'classroom':classroom, 'student_group':student_group, 'teacher': is_teacher(request.user, classroom_id)}, context_instance=RequestContext(request))

# 新增組別
def group_add(request, classroom_id):
        if request.method == 'POST':
            classroom_name = Classroom.objects.get(id=classroom_id).name            
            form = GroupForm(request.POST)
            if form.is_valid():
                group = EnrollGroup(name=form.cleaned_data['name'],classroom_id=int(classroom_id))
                group.save()     
        
                return redirect('/student/group/'+classroom_id)
        else:
            form = GroupForm()
        return render_to_response('form.html', {'form':form}, context_instance=RequestContext(request))
        
# 設定組別人數
def group_size(request, classroom_id):
        if request.method == 'POST':
            form = GroupSizeForm(request.POST)
            if form.is_valid():
                classroom = Classroom.objects.get(id=classroom_id)
                classroom.group_size = form.cleaned_data['group_size']
                classroom.save()       
        
                return redirect('/student/group/'+classroom_id)
        else:
            classroom = Classroom.objects.get(id=classroom_id)
            form = GroupSizeForm(instance=classroom)
        return render_to_response('form.html', {'form':form}, context_instance=RequestContext(request))        

# 加入組別
def group_enroll(request, classroom_id,  group_id):
        classroom = Classroom.objects.get(id=classroom_id)
        members = Enroll.objects.filter(group=group_id)
        if len(members) < classroom.group_size:
            group_name = EnrollGroup.objects.get(id=group_id).name
            enroll = Enroll.objects.filter(student_id=request.user.id, classroom_id=classroom_id)
            enroll.update(group=group_id)      
        return redirect('/student/group/'+classroom_id)

# 刪除組別
def group_delete(request, group_id, classroom_id):
    group = EnrollGroup.objects.get(id=group_id)
    group.delete()
    classroom_name = Classroom.objects.get(id=classroom_id).name      
    return redirect('/student/group/'+classroom_id)  
    
# 是否開放選組
def group_open(request, classroom_id, action):
    classroom = Classroom.objects.get(id=classroom_id)
    if action == "1":
        classroom.group_open=True
        classroom.save()           
    else :
        classroom.group_open=False
        classroom.save()             
    return redirect('/student/group/'+classroom_id)  	
	
# 列出選修的班級
def classroom(request):
        classrooms = []
        enrolls = Enroll.objects.filter(student_id=request.user.id).order_by("-id")
        for enroll in enrolls:
            shows = Round.objects.filter(classroom_id=enroll.classroom_id)
            classrooms.append([enroll, shows])       
        return render_to_response('student/classroom.html',{'classrooms': classrooms}, context_instance=RequestContext(request))    
    
# 查看可加入的班級
def classroom_add(request):
        if request.user.groups.filter(name='teacher').exists():
            classrooms = Classroom.objects.all().order_by('-id')
        else :
            user = User.objects.get(username=request.user.username[:request.user.username.find("_")])
            classrooms = Classroom.objects.filter(teacher_id=user.id).order_by("-id")
        classroom_teachers = []
        for classroom in classrooms:
            enroll = Enroll.objects.filter(student_id=request.user.id, classroom_id=classroom.id)
            if enroll.exists():
                classroom_teachers.append([classroom,classroom.teacher.first_name,1])
            else:
                classroom_teachers.append([classroom,classroom.teacher.first_name,0])   
        return render_to_response('student/classroom_add.html', {'classroom_teachers':classroom_teachers}, context_instance=RequestContext(request))
    
# 加入班級
def classroom_enroll(request, classroom_id):
        scores = []
        if request.method == 'POST':
                form = EnrollForm(request.POST)
                if form.is_valid():
                    try:
                        classroom = Classroom.objects.get(id=classroom_id)
                        if classroom.password == form.cleaned_data['password']:
                                enroll = Enroll(classroom_id=classroom_id, student_id=request.user.id, seat=form.cleaned_data['seat'])
                                enroll.save()                             
                        else:
                                return render_to_response('message.html', {'message':"選課密碼錯誤"}, context_instance=RequestContext(request))
                      
                    except Classroom.DoesNotExist:
                        pass
                    
                    
                    return redirect("/student/group/" + str(classroom.id))
        else:
            form = EnrollForm()
        return render_to_response('form.html', {'form':form}, context_instance=RequestContext(request))
        
# 修改座號
def seat_edit(request, enroll_id, classroom_id):
    enroll = Enroll.objects.get(id=enroll_id)
    if request.method == 'POST':
        form = SeatForm(request.POST)
        if form.is_valid():
            enroll.seat =form.cleaned_data['seat']
            enroll.save()
            classroom_name = Classroom.objects.get(id=classroom_id).name
            return redirect('/student/classroom')
    else:
        form = SeatForm(instance=enroll)

    return render_to_response('form.html',{'form': form}, context_instance=RequestContext(request))  

# 登入記錄
class LoginLogListView(ListView):
    context_object_name = 'visitorlogs'
    paginate_by = 20
    template_name = 'student/login_log.html'
    def get_queryset(self):
        visitorlogs = VisitorLog.objects.filter(user_id=self.kwargs['user_id']).order_by("-id")        
        return visitorlogs
        
    def get_context_data(self, **kwargs):
        context = super(LoginLogListView, self).get_context_data(**kwargs)
        if self.request.GET.get('page') :
            context['page'] = int(self.request.GET.get('page')) * 20 - 20
        else :
            context['page'] = 0
        return context        

# 列出所有公告
class AnnounceListView(ListView):
    model = Message
    context_object_name = 'messages'
    template_name = 'student/announce_list.html'    
    paginate_by = 20
    
    def get_queryset(self):
        classroom = Classroom.objects.get(id=self.kwargs['classroom_id'])  
        messages = Message.objects.filter(classroom_id=classroom.id, author_id=classroom.teacher_id).order_by("-id")
        queryset = []
        for message in messages:
            try: 
                messagepoll = MessagePoll.objects.get(message_id=message.id, reader_id=self.request.user.id, classroom_id=classroom.id)
                queryset.append([messagepoll, message])
            except ObjectDoesNotExist :
                pass
        return queryset
        
    def get_context_data(self, **kwargs):
        context = super(AnnounceListView, self).get_context_data(**kwargs)
        context['classroom'] = Classroom.objects.get(id=self.kwargs['classroom_id'])
        return context	    

def work_download(request, index, user_id, workfile_id):
    workfile = WorkFile.objects.get(id=workfile_id)
    username = User.objects.get(id=user_id).first_name
    filename = username + "_" + lesson_list[int(index)-1][2]  + ".sb2"
    download =  settings.BASE_DIR + "/static/work/" + str(user_id) + "/" + workfile.filename
    wrapper = FileWrapper(file( download, "r" ))
    response = HttpResponse(wrapper, content_type = 'application/force-download')
    #response = HttpResponse(content_type='application/force-download')
    response['Content-Disposition'] = 'attachment; filename={0}'.format(filename.encode('utf8'))
    # It's usually a good idea to set the 'Content-Length' header too.
    # You can also set any other required headers: Cache-Control, etc.
    return response
    #return render_to_response('student/download.html', {'download':download})
			
# 列出所有作業        
def work(request, classroom_id):
    lesson_dict = OrderedDict()
    works = Work.objects.filter(user_id=request.user.id).order_by("id")
    lesson = Classroom.objects.get(id=classroom_id).lesson
    for unit in lesson_list[lesson-1][1]:
        for assignment in unit[1]:
            sworks = filter(lambda w: w.index==assignment[2], works)
            if len(sworks)>0 :
                lesson_dict[assignment[2]] = [assignment[0], sworks[0]]
            else :
                lesson_dict[assignment[2]] = [assignment[0], None]
    return render_to_response('student/work.html', {'works':works, 'lesson_dict':sorted(lesson_dict.iteritems()), 'user_id': request.user.id, 'classroom_id':classroom_id}, context_instance=RequestContext(request))

# 查詢某作業分組小老師    
def work_group(request, lesson, classroom_id):
        student_groups = []
        groups = EnrollGroup.objects.filter(classroom_id=classroom_id)
        try:
                student_group = Enroll.objects.get(student_id=request.user.id, classroom_id=classroom_id).group
        except ObjectDoesNotExist :
                student_group = []		
        for group in groups:
            enrolls = Enroll.objects.filter(classroom_id=classroom_id, group=group.id)
            group_assistants = []
            works = []
            scorer_name = ""
            for enroll in enrolls: 
                try:    
                    work = Work.objects.get(user_id=enroll.student_id, index=lesson)
                    if work.scorer > 0 :
                        scorer = User.objects.get(id=work.scorer)
                        scorer_name = scorer.first_name
                    else :
                        scorer_name = "X"
                except ObjectDoesNotExist:
                    work = Work(index=lesson, user_id=1)
                works.append([enroll, work.score, scorer_name, work.file])
                try :
                    assistant = Assistant.objects.get(student_id=enroll.student.id, classroom_id=classroom_id, lesson=lesson)
                    group_assistants.append(enroll)
                except ObjectDoesNotExist:
				    pass
            student_groups.append([group, works, group_assistants])
        lesson_data = lesson_list[int(lesson)-1]		
        # 記錄系統事件
        if is_event_open(request) :          
            log = Log(user_id=request.user.id, event=u'查看作業小老師<'+lesson+'>')
            log.save()        
        return render_to_response('student/work_group.html', {'lesson':lesson, 'lesson_data':lesson_data, 'student_groups':student_groups, 'classroom_id':classroom_id, 'student_group':student_group}, context_instance=RequestContext(request))

# 查詢某作業所有同學心得
def memo(request, classroom_id, index):
 
    enrolls = Enroll.objects.filter(classroom_id=classroom_id)
    datas = []
    for enroll in enrolls:
        try:
            work = Work.objects.get(index=index, user_id=enroll.student_id)
            datas.append([enroll, work.memo])
        except ObjectDoesNotExist:
            datas.append([enroll, ""])
    def getKey(custom):
        return custom[0].seat
    datas = sorted(datas, key=getKey)	
    # 記錄系統事件
    if is_event_open(request) :      
        log = Log(user_id=request.user.id, event=u'查看某作業所有同學心得<'+index+'>')
        log.save()    
    return render_to_response('student/memo.html', {'datas': datas}, context_instance=RequestContext(request))


# 查詢某班級心得
def memo_all(request, classroom_id):
        enrolls = Enroll.objects.filter(classroom_id=classroom_id).order_by("seat")
        classroom_name = Classroom.objects.get(id=classroom_id).name
        # 記錄系統事件
        if is_event_open(request) :          
            log = Log(user_id=request.user.id, event=u'查看班級心得<'+classroom_name+'>')
            log.save()            
        return render_to_response('student/memo_all.html', {'enrolls':enrolls, 'classroom_name':classroom_name}, context_instance=RequestContext(request))

# 查詢某班級心得統計
def memo_count(request, classroom_id):
        enrolls = Enroll.objects.filter(classroom_id=classroom_id).order_by("seat")
        members = []
        for enroll in enrolls:
            members.append(enroll.student_id)
        classroom = Classroom.objects.get(id=classroom_id)
        works = Work.objects.filter(user_id__in=members)
        memo = ""
        for work in works:
            memo += work.memo
        memo = memo.rstrip('\r\n')
        seglist = jieba.cut(memo, cut_all=False)
        hash = {}
        for item in seglist: 
            if item in hash:
                hash[item] += 1
            else:
                hash[item] = 1
        words = []
        count = 0
        error=""
        for key, value in sorted(hash.items(), key=lambda x: x[1], reverse=True):
            if ord(key[0]) > 32 :
                count += 1	
                words.append([key, value])
                if count == 30:
                    break
        # 記錄系統事件
        if is_event_open(request) :          
            log = Log(user_id=request.user.id, event=u'查看班級心得統計<'+classroom.name+'>')
            log.save()            
        return render_to_response('student/memo_count.html', {'words':words, 'enrolls':enrolls, 'classroom':classroom}, context_instance=RequestContext(request))

# 評分某同學某進度心得
@login_required
def memo_user(request, user_id):
    user = User.objects.get(id=user_id)
    del lesson_list[:]
    reset()
    works = Work.objects.filter(user_id=user_id)
    for work in works:
        lesson_list[work.index-1].append(work.memo)

    # 記錄系統事件
    if is_event_open(request) :        
        log = Log(user_id=request.user.id, event=u'查閱個人心得<'+user.first_name+'>')
        log.save()  
    return render_to_response('student/memo_user.html', {'lesson_list':lesson_list, 'student': user}, context_instance=RequestContext(request))


# 查詢某班級某作業心得統計
def memo_work_count(request, classroom_id, work_id):
        enrolls = Enroll.objects.filter(classroom_id=classroom_id).order_by("seat")
        members = []
        for enroll in enrolls:
            members.append(enroll.student_id)
        classroom = Classroom.objects.get(id=classroom_id)
        works = Work.objects.filter(user_id__in=members, index=int(work_id))
        memo = ""
        for work in works:
            memo += work.memo
        memo = memo.rstrip('\r\n')
        seglist = jieba.cut(memo, cut_all=False)
        hash = {}
        for item in seglist: 
            if item in hash:
                hash[item] += 1
            else:
                hash[item] = 1
        words = []
        count = 0
        for key, value in sorted(hash.items(), key=lambda x: x[1], reverse=True):
            count += 1
            if ord(key[0]) > 32 :
                words.append([key, value])
                if count == 30:
                    break
        # 記錄系統事件
        if is_event_open(request) :          
            log = Log(user_id=request.user.id, event=u'查看班級作業心得統計<'+classroom.name+'><'+work_id+'>')
            log.save()                    
        return render_to_response('student/memo_work_count.html', {'words':words, 'enrolls':enrolls, 'classroom':classroom,  'work_id':work_id, 'lesson':lesson_list[int(work_id)-1][2]}, context_instance=RequestContext(request))

			
# 查詢某班某詞句心得
def memo_word(request, classroom_id, word):
        enrolls = Enroll.objects.filter(classroom_id=classroom_id).order_by("seat")
        members = []
        for enroll in enrolls:
            members.append(enroll.student_id)
        classroom = Classroom.objects.get(id=classroom_id)
        works = Work.objects.filter(user_id__in=members, memo__contains=word).order_by('index')
        for work in works:
            work.memo = work.memo.replace(word, '<font color=red>'+word+'</font>')
        # 記錄系統事件
        if is_event_open(request) :          
            log = Log(user_id=request.user.id, event=u'查看班級心得詞句<'+classroom.name+'><'+word+'>')
            log.save()            
        return render_to_response('student/memo_word.html', {'word':word, 'works':works, 'classroom':classroom}, context_instance=RequestContext(request))
		
# 查詢某班某作業某詞句心得
def memo_work_word(request, classroom_id, work_id, word):
        enrolls = Enroll.objects.filter(classroom_id=classroom_id).order_by("seat")
        members = []
        for enroll in enrolls:
            members.append(enroll.student_id)
        classroom = Classroom.objects.get(id=classroom_id)
        works = Work.objects.filter(user_id__in=members, index=work_id, memo__contains=word)
        for work in works:
            work.memo = work.memo.replace(word, '<font color=red>'+word+'</font>')
        # 記錄系統事件
        if is_event_open(request) :          
            log = Log(user_id=request.user.id, event=u'查看班級心得詞句<'+classroom.name+'><'+word+'>')
            log.save()            
        return render_to_response('student/memo_work_word.html', {'word':word, 'works':works, 'classroom':classroom, 'lesson':lesson_list[int(work_id)-1][2]}, context_instance=RequestContext(request))
		
		
# 查詢個人心得
def memo_show(request, user_id, unit,classroom_id, score):
    user_name = User.objects.get(id=user_id).first_name
    del lesson_list[:]
    reset()
    works = Work.objects.filter(user_id=user_id)
    for work in works:
        lesson_list[work.index-1].append(work.score)
        lesson_list[work.index-1].append(work.publication_date)
        if work.score > 0 :
            score_name = User.objects.get(id=work.scorer).first_name
            lesson_list[work.index-1].append(score_name)
        else :
            lesson_list[work.index-1].append("null")
        lesson_list[work.index-1].append(work.memo)
    c = 0
    for lesson in lesson_list:
        assistant = Assistant.objects.filter(student_id=user_id, lesson=c+1)
        if assistant.exists() :
            lesson.append("V")
        else :
            lesson.append("")
        c = c + 1
        #enroll_group = Enroll.objects.get(classroom_id=classroom_id, student_id=request.user.id).group
    user = User.objects.get(id=user_id)
    # 記錄系統事件
    if is_event_open(request) :      
        log = Log(user_id=request.user.id, event=u'查看同學心得<'+user_name+'><'+unit+'>')
        log.save()        
    return render_to_response('student/memo_show.html', {'classroom_id': classroom_id, 'works':works, 'lesson_list':lesson_list, 'user_name': user_name, 'unit':unit, 'score':score}, context_instance=RequestContext(request))

# 查詢作業進度
def progress(request, classroom_id, unit):
    bars = []
    bars1 = []
    bars2 = []
    bars3 = []
    bars4 = []
    a = 0
    classroom = Classroom.objects.get(id=classroom_id)
    enrolls = Enroll.objects.filter(classroom_id=classroom_id).order_by("seat")
    for enroll in enrolls:
        c = 0
        for lesson in lesson_list :
            works = Work.objects.filter(user_id=enroll.student_id)
            bars.append([enroll, [], ""])
            for work in works:
                if work.index == c+1:
                    bars[a*41+c][1] = work
                    if work.scorer > 0 :
                        score_name = User.objects.get(id=work.scorer).first_name
                        bars[a*41+c][2] = score_name
            c = c + 1
        for i in range(17) :
            bars1.append(bars[i+41*a])
        for i in range(8) :
            bars2.append(bars[i+17+41*a])
        for i in range(8) :
            bars3.append(bars[i+25+41*a])
        for i in range(8) :
            bars4.append(bars[i+33+41*a])
        a = a + 1
    # 記錄系統事件
    if is_event_open(request) :      
        log = Log(user_id=request.user.id, event=u'查看作業進度<'+unit+'><'+classroom.name+'>')
        log.save()           
    return render_to_response('student/progress.html', {'unit':unit, 'bars1':bars1, 'bars2':bars2, 'bars3':bars3, 'bars4':bars4,'classroom':classroom, 'lesson_list': lesson_list,}, context_instance=RequestContext(request))
    
