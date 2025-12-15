from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DateField, IntegerField, BooleanField, RadioField
from wtforms.validators import DataRequired, Length, Optional, NumberRange, ValidationError


class ClassCreateForm(FlaskForm):
    class_code = StringField('Mã lớp', validators=[
        DataRequired(message='Vui lòng nhập mã lớp'),
        Length(max=20, message='Mã lớp tối đa 20 ký tự')
    ])
    class_name = StringField('Tên lớp', validators=[
        DataRequired(message='Vui lòng nhập tên lớp'),
        Length(max=100, message='Tên lớp tối đa 100 ký tự')
    ])
    description = TextAreaField('Mô tả', validators=[Optional()])
    level = SelectField('Cấp độ', choices=[
        ('beginner', 'Sơ cấp'),
        ('intermediate', 'Trung cấp'),
        ('advanced', 'Nâng cao')
    ], validators=[DataRequired(message='Vui lòng chọn cấp độ')])
    max_students = IntegerField('Số học viên tối đa', validators=[
        DataRequired(message='Vui lòng nhập số học viên tối đa'),
        NumberRange(min=1, max=100, message='Số học viên từ 1-100')
    ], default=30)
    start_date = DateField('Ngày bắt đầu', validators=[
        DataRequired(message='Vui lòng chọn ngày bắt đầu')
    ], format='%Y-%m-%d')
    end_date = DateField('Ngày kết thúc', validators=[Optional()], format='%Y-%m-%d')
    # Schedule inputs removed; manage via class schedules pages

    def validate_end_date(self, field):
        if field.data and self.start_date.data and field.data < self.start_date.data:
            raise ValidationError('Ngày kết thúc phải sau ngày bắt đầu')


class ClassEditForm(FlaskForm):
    class_name = StringField('Tên lớp', validators=[
        DataRequired(message='Vui lòng nhập tên lớp'),
        Length(max=100, message='Tên lớp tối đa 100 ký tự')
    ])
    description = TextAreaField('Mô tả', validators=[Optional()])
    level = SelectField('Cấp độ', choices=[
        ('beginner', 'Sơ cấp'),
        ('intermediate', 'Trung cấp'),
        ('advanced', 'Nâng cao')
    ], validators=[DataRequired(message='Vui lòng chọn cấp độ')])
    max_students = IntegerField('Số học viên tối đa', validators=[
        DataRequired(message='Vui lòng nhập số học viên tối đa'),
        NumberRange(min=1, max=100, message='Số học viên từ 1-100')
    ])
    end_date = DateField('Ngày kết thúc', validators=[Optional()], format='%Y-%m-%d')
    # Schedule inputs removed; manage via class schedules pages
    is_active = BooleanField('Kích hoạt lớp')


class EnrollStudentForm(FlaskForm):
    student_id = SelectField('Chọn học viên', coerce=int, validators=[
        DataRequired(message='Vui lòng chọn học viên')
    ])
    notes = TextAreaField('Ghi chú', validators=[Optional()])


class ClassApprovalForm(FlaskForm):
    decision = RadioField('Quyết định', choices=[
        ('approve', 'Duyệt'),
        ('reject', 'Từ chối')
    ], validators=[DataRequired(message='Vui lòng chọn quyết định')])
    rejection_reason = TextAreaField('Lý do từ chối (nếu từ chối)', validators=[Optional()])

    def validate_rejection_reason(self, field):
        if self.decision.data == 'reject' and not field.data:
            raise ValidationError('Vui lòng nhập lý do từ chối')
