from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField,validators
from wtforms.validators import Required
class MainForm(FlaskForm):
    select = SelectField('toolsbuildlist',choices = [])
    hostbuild = TextField('HostBuild:', validators=[validators.required()])
    toolsbuild = TextField('ToolsBuild:', validators=[validators.required()])
    legacybuild = TextField('LegacyToolsBuild:', validators=[validators.required()])
    vcbuild = TextField('VCBuild:', validators=[validators.required()])
    alpsbuild = TextField('ALPSBuild:', validators=[validators.required()])
    alpsbuild = TextField('EmailAddress:', validators=[validators.required()])
    submit = SubmitField('submit the job')
