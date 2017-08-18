# first we import a view helpful classes from flask-WTF
from flask_wtf import Form
from wtforms import StringField, SelectField, SelectMultipleField, SubmitField, RadioField, TextAreaField
from wtforms.validators import DataRequired, Email, Length

class QuestionForm(Form):
    # first_name = StringField("Firs Name") add validators to the field:
    # first_question = SelectField('Have you had experience of contributing to a systematic reviews?', choices=['Yes','No'], validators=[DataRequired()])
    first_question = SelectMultipleField('In what capacity have you contributed to a systematic review? Select all that apply:', choices=[('develop questions','develop questions'), ('planning methods or write & publish protocols', 'planning methods or write & publish protocols'), ('develop & run search', 'develop & run search'), ('select studies', 'select studies'), ('collect data', 'collect data'), ('assess risk of bias', 'assess risk of bias'), ('analyze data', 'analyze data'), ('interprete findings', 'interprete findings'), ('write & publish review', 'write & publish review')], validators=[DataRequired()])
    second_question = RadioField('How many systematic reviews have you completed?', choices=[('0','0'), ('1-5','1-5'), ('5-10','5-10'), ('More than 10','More than 10')], validators=[DataRequired()])
    third_question = RadioField('Have you experience of using the cochrane risk of bias tool', choices=[('Yes', 'Yes'), ('No', 'No')], validators=[DataRequired()])
    #email = StringField('Email', validators=[DataRequired("Please enter your correct email address"), Email("Please enter a valid email address!")])
    submit = SubmitField('Submit & Continue')

class QuestionForm2(Form):
    first_sus = RadioField('I think I would like to use this system frequently.', choices=[('1','1'), ('2','2'), ('3', '3'), ('4', '4'), ('5', '5')], validators=[DataRequired()])
    second_sus= RadioField('I found the system unnecessarily complex.', choices=[('1','1'), ('2','2'), ('3', '3'), ('4', '4'), ('5', '5')], validators=[DataRequired()])
    third_sus = RadioField('I thought the system was easy to use.', choices=[('1','1'), ('2','2'), ('3', '3'), ('4', '4'), ('5', '5')], validators=[DataRequired()])
    fourth_sus = RadioField('I think that I would need the support of a technical person to be able to use this system.', choices=[('1','1'), ('2','2'), ('3', '3'), ('4', '4'), ('5', '5')], validators=[DataRequired()])
    fifth_sus = RadioField('I found the various functions in this system were well integrated.', choices=[('1','1'), ('2','2'), ('3', '3'), ('4', '4'), ('5', '5')], validators=[DataRequired()])
    sixth_sus = RadioField('I thought there was too much inconsistency in this system.', choices=[('1','1'), ('2','2'), ('3', '3'), ('4', '4'), ('5', '5')], validators=[DataRequired()])
    seventh_sus = RadioField('I would imagine that most people would learn to use this system very quickly.', choices=[('1','1'), ('2','2'), ('3', '3'), ('4', '4'), ('5', '5')], validators=[DataRequired()])
    eighth_sus = RadioField('I found the system very cumbersome to use.', choices=[('1','1'), ('2','2'), ('3', '3'), ('4', '4'), ('5', '5')], validators=[DataRequired()])
    ninth_sus = RadioField('I felt very confident using the system.', choices=[('1','1'), ('2','2'), ('3', '3'), ('4', '4'), ('5', '5')], validators=[DataRequired()])
    tenth_sus = RadioField('I needed to learn a lot of things before I could get going with this system.', choices=[('1','1'), ('2','2'), ('3', '3'), ('4', '4'), ('5', '5')], validators=[DataRequired()])
    eleventh_sus = RadioField('I found the text suggested by the computer helpful in completing the task.', choices=[('1','1'), ('2','2'), ('3', '3'), ('4', '4'), ('5', '5')], validators=[DataRequired()])
    twelfth_sus = RadioField('I found it difficult to navigate to the sections of the article suggested as relevant by the model.', choices=[('1','1'), ('2','2'), ('3', '3'), ('4', '4'), ('5', '5')], validators=[DataRequired()])
    thirteenth_sus = RadioField('I feel that having the computer suggest text to reviewers would improve the quality of the final output (i.e., the information extracted for the systematic review).', choices=[('1','1'), ('2','2'), ('3', '3'), ('4', '4'), ('5', '5')], validators=[DataRequired()])
    fourteenth_sus = RadioField('I felt the text suggested by the computer was often irrelevant.', choices=[('1','1'), ('2','2'), ('3', '3'), ('4', '4'), ('5', '5')], validators=[DataRequired()])
    fifteenth_sus = RadioField('I was confused by the text that the computer suggested.', choices=[('1','1'), ('2','2'), ('3', '3'), ('4', '4'), ('5', '5')], validators=[DataRequired()])
    sixteenth_sus = RadioField('I would like to continue using this system to aid systematic review production.', choices=[('1','1'), ('2','2'), ('3', '3'), ('4', '4'), ('5', '5')], validators=[DataRequired()])
    seventeenth_sus = TextAreaField('Text', validators=[DataRequired()])
    submit = SubmitField('Submit & Continue')
