# -*- coding: UTF-8 -*-
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# 班級
class Classroom(models.Model):
    Lesson_CHOICES = [
        (1, '基礎程式設計：使用Scratch 2.X'),
        (2, '進階程式設計'),
    ]	
    # 班級名稱
    name = models.CharField(max_length=30)
    # 課程名稱
    lesson = models.IntegerField(default=1, choices=Lesson_CHOICES)			
    # 選課密碼
    password = models.CharField(max_length=30)
    # 授課教師
    teacher_id = models.IntegerField(default=0)
    # 是否開放分組
    group_open = models.BooleanField(default=True)
    # 組別人數
    group_size = models.IntegerField(default=4)
    # 是否開放創意秀分組
    group_show_open = models.BooleanField(default=False)
    # 組別人數
    group_show_size = models.IntegerField(default=2)    
	# 事件
    event_open = models.BooleanField(default=True)
	# 課程事件
    event_video_open = models.BooleanField(default=True)    
    
    @property
    def teacher(self):
        return User.objects.get(id=self.teacher_id)  
        
    def __unicode__(self):
        return self.name
        
    def lesson_choice(self):
        return dict(Classroom.Lesson_CHOICES)[self.lesson]	
  
        
#匯入
class ImportUser(models.Model):
	username = models.CharField(max_length=50, default="")
	first_name = models.CharField(max_length=50, default="")
	password = models.CharField(max_length=50, default="")
	email = models.CharField(max_length=100, default="")	
	