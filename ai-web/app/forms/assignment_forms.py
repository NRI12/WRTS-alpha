# app/forms/assignment_forms.py
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import SelectField, DateTimeField, TextAreaField, BooleanField, SubmitField, StringField
from wtforms.validators import DataRequired, Optional

class AssignmentCreateForm(FlaskForm):
    routine_id = SelectField('Bài võ (*)', coerce=int, validators=[DataRequired()])
    
    assignment_type = SelectField('Loại bài tập (*)', 
        choices=[('individual', 'Cá nhân'), ('class', 'Lớp học')],
        validators=[DataRequired()]
    )
    
    assigned_to_student = SelectField('Học viên', coerce=int, validators=[Optional()])
    assigned_to_class = SelectField('Lớp học', coerce=int, validators=[Optional()])
    
    deadline = DateTimeField('Hạn nộp', format='%Y-%m-%dT%H:%M', validators=[Optional()])
    
    instructions = TextAreaField('Hướng dẫn')
    
    priority = SelectField('Độ ưu tiên (*)',
        choices=[
            ('low', 'Thấp'),
            ('normal', 'Bình thường'),
            ('high', 'Cao'),
            ('urgent', 'Khẩn cấp')
        ],
        default='normal',
        validators=[DataRequired()]
    )
    
    is_mandatory = BooleanField('Bắt buộc', default=True)
    
    # Phương thức chấm điểm
    grading_method = SelectField('Phương thức chấm điểm (*)',
        choices=[
            ('manual', 'Chấm tay'),
            ('ai', 'AI tự động'),
            ('both', 'Cả hai (AI + Chấm tay)')
        ],
        default='manual',
        validators=[DataRequired()]
    )
    
    # BẮT BUỘC: Phải upload video hoặc nhập URL
    instructor_video_url = StringField('Link Video Demo')
    
    instructor_video_file = FileField('Upload Video Demo (*)', 
        validators=[
            FileAllowed(['mp4', 'mov', 'avi', 'mkv'], 'Chỉ chấp nhận video!')
        ]
    )
    
    submit = SubmitField('Gán bài tập')
    
    def validate(self, extra_validators=None):
        """Custom validation: Phải có video URL hoặc file"""
        if not super().validate(extra_validators):
            return False
        
        # Kiểm tra phải có ít nhất 1 trong 2: URL hoặc file
        if not self.instructor_video_url.data and not self.instructor_video_file.data:
            self.instructor_video_file.errors.append('Vui lòng upload video demo hoặc nhập link video')
            return False
        
        return True