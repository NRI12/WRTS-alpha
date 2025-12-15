from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SelectField, IntegerField, DecimalField
from wtforms.validators import DataRequired, Length, NumberRange, Optional, ValidationError


class RoutineCreateForm(FlaskForm):
    routine_code = StringField('Mã bài võ', validators=[
        DataRequired(message='Vui lòng nhập mã bài võ'),
        Length(max=30, message='Mã bài võ tối đa 30 ký tự'),
    ])
    routine_name = StringField('Tên bài võ', validators=[
        DataRequired(message='Vui lòng nhập tên bài võ'),
        Length(max=100, message='Tên bài võ tối đa 100 ký tự'),
    ])
    description = TextAreaField('Mô tả', validators=[Optional()])
    weapon_id = SelectField('Binh khí', coerce=int, validators=[
        DataRequired(message='Vui lòng chọn binh khí'),
    ])
    level = SelectField('Cấp độ', choices=[
        ('beginner', 'Sơ cấp'),
        ('intermediate', 'Trung cấp'),
        ('advanced', 'Nâng cao'),
    ], validators=[DataRequired(message='Vui lòng chọn cấp độ')])
    difficulty_score = DecimalField('Độ khó (1-10)', validators=[
        Optional(),
        NumberRange(min=1.0, max=10.0, message='Độ khó từ 1.0 đến 10.0'),
    ], default=1.0)
    duration_seconds = IntegerField('Thời lượng (giây)', validators=[
        DataRequired(message='Vui lòng nhập thời lượng'),
        NumberRange(min=1, max=3600, message='Thời lượng từ 1-3600 giây'),
    ])
    total_moves = IntegerField('Số động tác', validators=[
        Optional(),
        NumberRange(min=1, message='Số động tác tối thiểu 1'),
    ], default=1)
    pass_threshold = DecimalField('Ngưỡng đạt (%)', validators=[
        Optional(),
        NumberRange(min=0, max=100, message='Ngưỡng từ 0-100%'),
    ], default=70.00)
    # GIỮ LẠI cả 2 options
    reference_video_url = StringField('URL video mẫu (YouTube, Vimeo...)', validators=[
        Optional(),
        Length(max=500, message='URL tối đa 500 ký tự')
    ])
    
    reference_video_file = FileField('HOẶC upload video từ máy', validators=[
        Optional(),
        FileAllowed(['mp4', 'avi', 'mov', 'mkv'], 'Chỉ chấp nhận video!')
    ])
    
    # Validate: phải có ít nhất 1 trong 2 (chỉ khi tạo mới)
    def validate(self, extra_validators=None):
        if not super().validate(extra_validators):
            return False
        
        # Chỉ validate khi tạo mới, không validate khi edit
        # Khi edit, cả 2 field đều có thể để trống (giữ nguyên video cũ)
        return True


class RoutineEditForm(FlaskForm):
    """Form for editing existing routines - video fields are optional"""
    routine_code = StringField('Mã bài võ', validators=[
        DataRequired(message='Vui lòng nhập mã bài võ'),
        Length(max=30, message='Mã bài võ tối đa 30 ký tự'),
    ])
    routine_name = StringField('Tên bài võ', validators=[
        DataRequired(message='Vui lòng nhập tên bài võ'),
        Length(max=100, message='Tên bài võ tối đa 100 ký tự'),
    ])
    description = TextAreaField('Mô tả', validators=[Optional()])
    weapon_id = SelectField('Binh khí', coerce=int, validators=[
        DataRequired(message='Vui lòng chọn binh khí'),
    ])
    level = SelectField('Cấp độ', choices=[
        ('beginner', 'Sơ cấp'),
        ('intermediate', 'Trung cấp'),
        ('advanced', 'Nâng cao'),
    ], validators=[DataRequired(message='Vui lòng chọn cấp độ')])
    difficulty_score = DecimalField('Độ khó (1-10)', validators=[
        Optional(),
        NumberRange(min=1.0, max=10.0, message='Độ khó từ 1.0 đến 10.0'),
    ], default=1.0)
    duration_seconds = IntegerField('Thời lượng (giây)', validators=[
        DataRequired(message='Vui lòng nhập thời lượng'),
        NumberRange(min=1, max=3600, message='Thời lượng từ 1-3600 giây'),
    ])
    total_moves = IntegerField('Số động tác', validators=[
        Optional(),
        NumberRange(min=1, message='Số động tác tối thiểu 1'),
    ], default=1)
    pass_threshold = DecimalField('Ngưỡng đạt (%)', validators=[
        Optional(),
        NumberRange(min=0, max=100, message='Ngưỡng từ 0-100%'),
    ], default=70.00)
    
    # Video fields - both optional for editing
    reference_video_url = StringField('URL video mẫu (YouTube, Vimeo...)', validators=[
        Optional(),
        Length(max=500, message='URL tối đa 500 ký tự')
    ])
    
    reference_video_file = FileField('HOẶC upload video từ máy', validators=[
        Optional(),
        FileAllowed(['mp4', 'avi', 'mov', 'mkv'], 'Chỉ chấp nhận video!')
    ])


class CriteriaForm(FlaskForm):
    criteria_name = StringField('Tên tiêu chí', validators=[
        DataRequired(message='Vui lòng nhập tên tiêu chí'),
        Length(max=100, message='Tên tiêu chí tối đa 100 ký tự'),
    ])
    criteria_code = StringField('Mã tiêu chí', validators=[
        DataRequired(message='Vui lòng nhập mã tiêu chí'),
        Length(max=50, message='Mã tiêu chí tối đa 50 ký tự'),
    ])
    weight_percentage = DecimalField('Trọng số (%)', validators=[
        DataRequired(message='Vui lòng nhập trọng số'),
        NumberRange(min=0.01, max=100, message='Trọng số từ 0.01-100%'),
    ])
    description = TextAreaField('Mô tả', validators=[Optional()])
    evaluation_method = StringField('Phương pháp đánh giá', validators=[
        Optional(),
        Length(max=50, message='Phương pháp tối đa 50 ký tự'),
    ])


