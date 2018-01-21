# -*- coding: UTF-8 -*-
from django.shortcuts import render_to_response, redirect
from django.contrib.auth.models import User
from django.template import RequestContext
from account.models import Profile
from django.shortcuts import render
from student.lesson import *

# 分類課程    
def lessons(request, lesson):       
        return render_to_response('student/lessons.html', {'lesson': lesson, 'lesson_list': lesson_list}, context_instance=RequestContext(request))

# 課程內容
def lesson(request, lesson, unit,index):
       return render_to_response('student/lesson.html', {'index':index, 'unit':unit, 'lesson':lesson, 'lesson_list': lesson_list}, context_instance=RequestContext(request))
        
