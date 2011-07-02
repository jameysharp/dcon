from wtforms.fields import Field
from wtforms.widgets import TextInput
from wtforms.validators import EqualTo

from flaskext.uploads import configure_uploads, IMAGES, UploadSet
from flaskext.wtf import (Form, FileAllowed, FileRequired,
    Required, FileField, QuerySelectField, IntegerField,
    PasswordField, SubmitField, TextField, TextAreaField)

from newrem.main import app
from newrem.models import Character

images = UploadSet("images", IMAGES)
pngs = UploadSet("pngs", ("png",))

configure_uploads(app, (images, pngs))

class TagListField(Field):
    widget = TextInput()

    def _value(self):
        if self.data:
            return u", ".join(self.data)
        else:
            return u""

    def process_formdata(self, data):
        if data:
            self.data = [word.strip() for word in data[0].split(",")]
            self.data.sort()
        else:
            self.data = []

class CharacterCreateForm(Form):
    name = TextField(u"New name", validators=(Required(),))
    portrait = FileField("Select a portrait",
        validators=(FileAllowed(pngs, "PNGs only!"),))
    submit = SubmitField("Create!")

class CharacterModifyForm(Form):
    characters = QuerySelectField(u"Characters",
        query_factory=lambda: Character.query.order_by(Character.name),
        get_label="name")
    name = TextField(u"New name")
    portrait = FileField("Select a portrait",
        validators=(FileAllowed(pngs, "PNGs only!"),))
    submit = SubmitField("Modify!")

class CharacterDeleteForm(Form):
    characters = QuerySelectField(u"Characters",
        query_factory=lambda: Character.query.order_by(Character.name),
        get_label="name")
    submit = SubmitField("Delete!")

class LoginForm(Form):
    username = TextField("Username", validators=(Required(),))
    password = PasswordField("Password", validators=(Required(),))
    submit = SubmitField("Login!")

class RegisterForm(LoginForm):
    confirm = PasswordField("Confirm password",
        validators=(Required(), EqualTo("password")))
    submit = SubmitField("Register!")

class NewsForm(Form):
    title = TextField("Title", validators=(Required(),))
    content = TextAreaField("Content")
    submit = SubmitField("Post!")

class UploadForm(Form):
    file = FileField("Select a file to upload",
        validators=(FileRequired("Must upload a comic!"),
            FileAllowed(images, "Images only!")))
    title = TextField("Title", validators=(Required(),))
    index = IntegerField("Where to insert this comic?",
        validators=(Required(),))
    characters = TagListField("Characters")
    submit = SubmitField("Upload!")
