from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, DateField, TextAreaField, BooleanField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional, Regexp

class LoginForm(FlaskForm):
    username = StringField('Tên đăng nhập', validators=[
        DataRequired(message='Vui lòng nhập tên đăng nhập')
    ])
    password = PasswordField('Mật khẩu', validators=[
        DataRequired(message='Vui lòng nhập mật khẩu')
    ])

class RegisterForm(FlaskForm):
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

class ForgotPasswordForm(FlaskForm):
    email = StringField('Email', validators=[
        DataRequired(message='Vui lòng nhập email'),
        Email(message='Email không hợp lệ')
    ])

class ResetPasswordForm(FlaskForm):
    new_password = PasswordField('Mật khẩu mới', validators=[
        DataRequired(message='Vui lòng nhập mật khẩu mới'),
        Length(min=6, message='Mật khẩu tối thiểu 6 ký tự')
    ])
    confirm_password = PasswordField('Xác nhận mật khẩu', validators=[
        DataRequired(message='Vui lòng xác nhận mật khẩu'),
        EqualTo('new_password', message='Mật khẩu xác nhận không khớp')
    ])

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Mật khẩu hiện tại', validators=[
        DataRequired(message='Vui lòng nhập mật khẩu hiện tại')
    ])
    new_password = PasswordField('Mật khẩu mới', validators=[
        DataRequired(message='Vui lòng nhập mật khẩu mới'),
        Length(min=6, message='Mật khẩu tối thiểu 6 ký tự')
    ])
    confirm_password = PasswordField('Xác nhận mật khẩu mới', validators=[
        DataRequired(message='Vui lòng xác nhận mật khẩu'),
        EqualTo('new_password', message='Mật khẩu xác nhận không khớp')
    ])

class EditProfileForm(FlaskForm):
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
