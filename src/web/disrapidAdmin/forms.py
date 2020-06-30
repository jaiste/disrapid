from flask_wtf import FlaskForm
from wtforms import BooleanField, TextField, SubmitField
from wtforms.validators import DataRequired, Length


class WelcomeForm(FlaskForm):
    enabled = BooleanField('Enabled', [
        DataRequired()])
    message = TextField('Message', [
        DataRequired(),
        Length(max=2000, message=('Only 2000 characters allowed'))])
    submit = SubmitField('Submit')
