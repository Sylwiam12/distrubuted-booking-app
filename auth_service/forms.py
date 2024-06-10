from wtforms import Form, BooleanField, StringField, PasswordField, validators
from wtforms.validators import DataRequired

class SigninForm(Form):
    email = StringField("Email", validators=[
        validators.Length(min=3, max =55),
        validators.Email(message="Please provide valid email address."),
        validators.DataRequired(message="Please fill in")
    ])

    password = PasswordField("Password", validators=[
        validators.DataRequired(message="Please fill in.")
    ])


class SignupForm(Form):
    name = StringField("Name", validators=[
        validators.Length(min=1, max=25),
        validators.DataRequired(message="Please fill in")
    ])

    surname = StringField("Surname", validators=[
        validators.Length(min=1, max=25),
        validators.DataRequired(message="Please fill in.")
    ])

    email = StringField("Email", validators=[
        validators.Email(message="Please provide valid email address"),
        validators.DataRequired(message="Please fill in.")
    ])

    password = PasswordField("Password", validators=[
        validators.DataRequired(message="Please fill in."),
        validators.EqualTo(fieldname="confirm", message="Your passwords do not match."),
    ])

    confirm = PasswordField("Password confirmation", validators=[
        validators.DataRequired(message="Please fill in.")
    ])

class SendEmail(Form):
    name = StringField("Name", validators=[
        validators.Length(min=1, max=100),
        validators.DataRequired(message="Please fill in")
    ])

    topic = StringField("Topic", validators=[
        validators.Length(min=1, max=100),
        validators.DataRequired(message="Please fill in.")
    ])

    email = StringField("Email", validators=[
        validators.Email(message="Please provide valid email address"),
        validators.DataRequired(message="Please fill in.")
    ])

    text = StringField("Text", validators=[
        validators.DataRequired(message="Please fill in."),
    ])