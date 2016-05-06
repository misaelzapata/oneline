from flask import flash, redirect, request, render_template, make_response, url_for
from flask.ext import admin, login
from flask.ext.admin import expose, helpers
from flask.ext.admin.contrib.mongoengine import ModelView
from wtforms import fields, form, validators
from web import app
from web.models import Contact, IncomingMessages, Message, OutgoingMessages, User


class MyAdminModelView(ModelView):

    def is_accessible(self):
        if login.current_user.is_authenticated:
            if login.current_user.has_role("admin"):
                return True
        return False


# Define login and registration forms (for flask-login)
class LoginForm(form.Form):
    login = fields.TextField(validators=[validators.required()])
    password = fields.PasswordField(validators=[validators.required()])

    def validate_login(self, field):
        user = self.get_user()

        if user is None:
            raise validators.ValidationError('Invalid user')

        if user.password != self.password.data:
            raise validators.ValidationError('Invalid password')

    def get_user(self):
        return User.objects(email=self.login.data).first()


class RegistrationForm(form.Form):
    login = fields.TextField(validators=[validators.required()])
    email = fields.TextField()
    password = fields.PasswordField(validators=[validators.required()])

    def validate_login(self, field):
        if db.session.query(User).filter_by(login=self.login.data).count() > 0:
            raise validators.ValidationError('Duplicate username')

# Customized admin views


class MyAdminIndexView(admin.AdminIndexView):

    def is_accessible(self):
        if login.current_user.is_authenticated:
            return login.current_user.has_role("admin")
        return True

    @expose('/')
    def index(self):
        if not login.current_user.is_authenticated:
            return redirect(url_for('.login_view'))
        return super(MyAdminIndexView, self).index()

    @expose('/login/', methods=('GET', 'POST'))
    def login_view(self):
        # handle user login

        form = LoginForm(request.form)
        if request.method == 'POST' and form.validate():
            user = form.get_user()
            if user is not None:
                if user and utils.verify_password(form.password.data, user.password):
                    login.login_user(user)
                    flash("Logged in successfully!", category='success')
                return redirect(url_for('admin.index'))
            flash("Wrong username or password!", category='error')

        if login.current_user.is_authenticated:
            return redirect(url_for('.index'))
        link = '<p>Don\'t have an account? Too bad... </p>'
        self._template_args['form'] = form
        self._template_args['link'] = link
        return super(MyAdminIndexView, self).index()

    @expose('/logout/')
    def logout_view(self):
        login.logout_user()
        return redirect(url_for('.index'))


class UserView(MyAdminModelView):

    # On the form for creating or editing a User, don't display a field corresponding to the model's password field.
    # There are two reasons for this. First, we want to encrypt the password before storing in the database. Second,
    # we want to use a password field (with the input masked) rather than a
    # regular text field.
    def scaffold_form(self):

        # Start with the standard form as provided by Flask-Admin. We've already told Flask-Admin to exclude the
        # password field from this form.
        form_class = super(UserView, self).scaffold_form()

        # Add a password field, naming it "password2" and labeling it "New
        # Password".
        form_class.password2 = fields.PasswordField('New Password')
        return form_class

    # This callback executes when the user saves changes to a newly-created or edited User -- before the changes are
    # committed to the database.
    def on_model_change(self, form, model, is_created):

        # If the password field isn't blank...
        if len(model.password2):

            # ... then encrypt the new password prior to storing it in the database. If the password field is blank,
            # the existing password in the database will be retained.
            model.password = model.password2

# Customized admin views


class RoleView(MyAdminModelView):

    column_filters = ['name']


class ContactView(MyAdminModelView):
    column_filters = ['name', 'phone']

    column_searchable_list = ('name', 'phone')


class MessageView(MyAdminModelView):
    column_filters = ['name']
    
admin = admin.Admin(
    app,
    'Admin',
    index_view=MyAdminIndexView())
admin.add_view(UserView(User))
admin.add_view(ContactView(Contact))
admin.add_view(MessageView(Message))
admin.add_view(MyAdminModelView(OutgoingMessages))
admin.add_view(MyAdminModelView(IncomingMessages))

