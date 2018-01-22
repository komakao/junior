# -*- coding: utf-8 -*-
from django import forms
from teacher.models import Classroom
from account.models import Message
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
            
#上傳檔案
class UploadFileForm(forms.Form):
    file = forms.FileField()
    
# 新增一個課程表單
class AnnounceForm(forms.ModelForm):
        class Meta:
           model = Message
           fields = ['title', 'content']
        
        def __init__(self, *args, **kwargs):
            super(AnnounceForm, self).__init__(*args, **kwargs)
            self.fields['title'].label = "公告主旨"
            self.fields['title'].widget.attrs['size'] = 50	
            self.fields['content'].label = "公告內容"
            self.fields['content'].widget.attrs['cols'] = 50
            self.fields['content'].widget.attrs['rows'] = 20        