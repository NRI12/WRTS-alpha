from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length

class FeedbackSubmitForm(FlaskForm):
    feedback_type = SelectField('Loại phản hồi (*)', choices=[
        ('bug_report', 'Báo lỗi'),
        ('feature_request', 'Đề xuất tính năng'),
        ('complaint', 'Khiếu nại'),
        ('suggestion', 'Gợi ý'),
        ('praise', 'Khen ngợi')
    ], validators=[DataRequired(message='Vui lòng chọn loại phản hồi')])
    
    subject = StringField('Tiêu đề (*)', validators=[
        DataRequired(message='Vui lòng nhập tiêu đề'),
        Length(max=200, message='Tiêu đề tối đa 200 ký tự')
    ])
    
    content = TextAreaField('Nội dung (*)', validators=[
        DataRequired(message='Vui lòng nhập nội dung')
    ])
    
    submit = SubmitField('Gửi phản hồi')

class FeedbackResponseForm(FlaskForm):
    priority = SelectField('Mức độ ưu tiên', choices=[
        ('low', 'Thấp'),
        ('normal', 'Bình thường'),
        ('high', 'Cao'),
        ('urgent', 'Khẩn cấp')
    ])
    
    feedback_status = SelectField('Trạng thái', choices=[
        ('pending', 'Chờ xử lý'),
        ('in_review', 'Đang xem xét'),
        ('resolved', 'Đã giải quyết'),
        ('rejected', 'Từ chối'),
        ('implemented', 'Đã triển khai')
    ])
    
    resolution_notes = TextAreaField('Ghi chú giải quyết')
    submit = SubmitField('Cập nhật')
