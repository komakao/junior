# -*- coding: utf-8 -*-
from django import forms
from teacher.models import Classroom
#from student.models import Work, Enroll
#from account.models import Message
#from student.models import SWork, Enroll

# 新增一個課程表單
class ClassroomForm(forms.ModelForm):
        class Meta:
           model = Classroom
           fields = ['name','lesson', 'password']
        
        def __init__(self, *args, **kwargs):
            super(ClassroomForm, self).__init__(*args, **kwargs)
            self.fields['name'].label = "班級名稱"
            self.fields['lesson'].label = "課程名稱"			
            self.fields['password'].label = "選課密碼"
           