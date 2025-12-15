from flask_wtf import FlaskForm
from datetime import datetime
from flask_wtf.file import FileField, FileAllowed  # THÊM import
from wtforms import StringField, TextAreaField, SelectField, DateTimeField, IntegerField, DecimalField, RadioField  # THÊM RadioField
from wtforms.validators import DataRequired, Length, NumberRange, Optional, ValidationError


class ExamCreateForm(FlaskForm):
    exam_code = StringField('Mã bài kiểm tra', validators=[
        DataRequired(message='Vui lòng nhập mã bài kiểm tra'),
        Length(max=30, message='Mã tối đa 30 ký tự'),
    ])
    exam_name = StringField('Tên bài kiểm tra', validators=[
        DataRequired(message='Vui lòng nhập tên bài kiểm tra'),
        Length(max=100, message='Tên tối đa 100 ký tự'),
    ])
    description = TextAreaField('Mô tả', validators=[Optional()])
    class_id = SelectField('Lớp học', coerce=int, validators=[Optional()])
    
    # THÊM MỚI: Chọn nguồn video
    video_source = RadioField(
        'Nguồn video',
        choices=[
            ('routine', 'Chọn từ Routine có sẵn'),
            ('upload', 'Upload video mới')
        ],
        default='routine',
        validators=[DataRequired()]
    )
    
    # SỬA: routine_id giờ optional
    routine_id = SelectField('Bài võ', coerce=int, validators=[Optional()])
    
    # THÊM MỚI: Upload video
    reference_video = FileField(
        'Video mẫu',
        validators=[
            Optional(),
            FileAllowed(['mp4', 'avi', 'mov', 'mkv'], 'Chỉ chấp nhận file video MP4, AVI, MOV, MKV!')
        ]
    )
    
    exam_type = SelectField('Loại kiểm tra', choices=[
        ('practice', 'Thi thử'),
        ('midterm', 'Giữa kỳ'),
        ('final', 'Cuối kỳ'),
        ('certification', 'Chứng chỉ'),
    ], validators=[DataRequired()])
    start_time = DateTimeField('Thời gian bắt đầu', format='%Y-%m-%dT%H:%M', validators=[
        DataRequired(message='Vui lòng chọn thời gian bắt đầu'),
    ])
    end_time = DateTimeField('Thời gian kết thúc', format='%Y-%m-%dT%H:%M', validators=[
        DataRequired(message='Vui lòng chọn thời gian kết thúc'),
    ])
    pass_score = DecimalField('Điểm đạt (%)', validators=[
        Optional(),
        NumberRange(min=0, max=100, message='Điểm từ 0-100%'),
    ], default=70.00)

    # THÊM MỚI: Custom validation
    def validate(self, extra_validators=None):
        if not super().validate(extra_validators=extra_validators):
            return False
        
        # Không cho phép tạo bài thi trong quá khứ
        if self.start_time.data and self.start_time.data < datetime.now():
            self.start_time.errors.append('Thời gian bắt đầu không được ở quá khứ')
            return False

        # Nếu chọn routine thì phải có routine_id
        if self.video_source.data == 'routine':
            if not self.routine_id.data or self.routine_id.data == 0:
                self.routine_id.errors.append('Vui lòng chọn bài võ')
                return False
        
        # Nếu chọn upload thì phải có file
        if self.video_source.data == 'upload':
            if not self.reference_video.data:
                self.reference_video.errors.append('Vui lòng upload video mẫu')
                return False
        
        return True

    def validate_end_time(self, field):
        if field.data and self.start_time.data and field.data <= self.start_time.data:
            raise ValidationError('Thời gian kết thúc phải sau thời gian bắt đầu')


