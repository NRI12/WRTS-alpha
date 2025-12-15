from flask_wtf import FlaskForm
from wtforms import SelectField, TimeField, StringField, TextAreaField, BooleanField
from wtforms.validators import DataRequired, Optional, ValidationError


class ScheduleForm(FlaskForm):
    day_of_week = SelectField(
        'Ngày trong tuần',
        choices=[
            ('', '-- Chọn ngày --'),
            ('monday', 'Thứ 2'),
            ('tuesday', 'Thứ 3'),
            ('wednesday', 'Thứ 4'),
            ('thursday', 'Thứ 5'),
            ('friday', 'Thứ 6'),
            ('saturday', 'Thứ 7'),
            ('sunday', 'Chủ nhật'),
        ],
        validators=[DataRequired(message='Vui lòng chọn ngày')],
    )

    time_start = TimeField('Giờ bắt đầu', validators=[DataRequired(message='Vui lòng chọn giờ bắt đầu')], format='%H:%M')
    time_end = TimeField('Giờ kết thúc', validators=[DataRequired(message='Vui lòng chọn giờ kết thúc')], format='%H:%M')

    location = StringField('Địa điểm', validators=[Optional()])
    notes = TextAreaField('Ghi chú', validators=[Optional()])
    is_active = BooleanField('Kích hoạt lịch học', default=True)

    def validate_time_end(self, field):
        if field.data and self.time_start.data and field.data <= self.time_start.data:
            raise ValidationError('Giờ kết thúc phải sau giờ bắt đầu')
