from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, DateField, TextAreaField, BooleanField
from wtforms.validators import DataRequired, Email, Length, Optional, Regexp

class CreateUserForm(FlaskForm):
    username = StringField('Tên đăng nhập', validators=[
        DataRequired(message='Vui lòng nhập tên đăng nhập'),
        Length(min=3, message='Tên đăng nhập tối thiểu 3 ký tự')
    ])
    password = PasswordField('Mật khẩu', validators=[
        DataRequired(message='Vui lòng nhập mật khẩu'),
        Length(min=6, message='Mật khẩu tối thiểu 6 ký tự')
    ])
    email = StringField('Email', validators=[
        DataRequired(message='Vui lòng nhập email'),
        Email(message='Email không hợp lệ')
    ])
    full_name = StringField('Họ và tên', validators=[
        DataRequired(message='Vui lòng nhập họ và tên')
    ])
    phone = StringField('Số điện thoại', validators=[
        Optional(),
        Regexp(r'^[0-9+\-() ]{10,20}$', message='Số điện thoại không hợp lệ')
    ])
    date_of_birth = DateField('Ngày sinh', validators=[Optional()], format='%Y-%m-%d')
    gender = SelectField('Giới tính', choices=[
        ('', '-- Chọn --'),
        ('male', 'Nam'),
        ('female', 'Nữ'),
        ('other', 'Khác')
    ], validators=[Optional()])
    address = TextAreaField('Địa chỉ', validators=[Optional()])
    role_id = SelectField('Vai trò', coerce=int, validators=[
        DataRequired(message='Vui lòng chọn vai trò')
    ])

class EditUserForm(FlaskForm):
    email = StringField('Email', validators=[
        DataRequired(message='Vui lòng nhập email'),
        Email(message='Email không hợp lệ')
    ])
    full_name = StringField('Họ và tên', validators=[
        DataRequired(message='Vui lòng nhập họ và tên')
    ])
    phone = StringField('Số điện thoại', validators=[
        Optional(),
        Regexp(r'^[0-9+\-() ]{10,20}$', message='Số điện thoại không hợp lệ')
    ])
    date_of_birth = DateField('Ngày sinh', validators=[Optional()], format='%Y-%m-%d')
    gender = SelectField('Giới tính', choices=[
        ('', '-- Chọn --'),
        ('male', 'Nam'),
        ('female', 'Nữ'),
        ('other', 'Khác')
    ], validators=[Optional()])
    address = TextAreaField('Địa chỉ', validators=[Optional()])
    role_id = SelectField('Vai trò', coerce=int, validators=[
        DataRequired(message='Vui lòng chọn vai trò')
    ])
    is_active = BooleanField('Kích hoạt tài khoản')
