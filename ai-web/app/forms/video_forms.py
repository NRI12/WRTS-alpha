from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import TextAreaField, SelectField, HiddenField
from wtforms.validators import DataRequired, Optional, Length

class VideoUploadForm(FlaskForm):
    routine_id = SelectField('Chọn bài võ', coerce=int, validators=[DataRequired(message="Vui lòng chọn bài võ")])
    assignment_id = HiddenField('Assignment ID', validators=[Optional()])
    video_file = FileField('Chọn video bài tập', validators=[
        FileRequired(message="Vui lòng chọn file video"),
        FileAllowed(['mp4', 'avi', 'mov', 'mkv'], 'Chỉ chấp nhận file video (mp4, avi, mov, mkv)')
    ])
    notes = TextAreaField('Ghi chú (tùy chọn)', validators=[Optional(), Length(max=500)])

class VideoFilterForm(FlaskForm):
    routine_id = SelectField('Lọc theo bài võ', coerce=int, validators=[Optional()])
    status = SelectField('Trạng thái', validators=[Optional()])