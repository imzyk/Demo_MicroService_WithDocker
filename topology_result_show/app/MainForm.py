from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField,validators
from wtforms.validators import Required
class MainForm(FlaskForm):
    select = SelectField('tools_build_list',choices = [])
    select = SelectField('esx_build_list',choices = [])
    select = SelectField('legacy_tools_build_list',choices = [])
    select = SelectField('legacy_esx_build_list',choices = [])
    select = SelectField('topology_type_list',choices = [])
    select = SelectField('topology_mode_list',choices = [])
    submit = SubmitField('Check the result')
