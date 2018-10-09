import secrets
import os
from PIL import Image
from flaskblog import app, bcrypt, db
from flask import render_template, url_for, flash, redirect, request
from flaskblog.forms import RegistrationForm, LoginForm, UpdateInfoForm
from .models import User
from flask_login import login_user, current_user, logout_user, login_required


posts = [
    {
        'author': 'Corey Schafer',
        'title': 'Blog Post 1',
        'content': 'First post content',
        'date_posted': 'April 20, 2018'
    },
    {
        'author': 'Jane Doe',
        'title': 'Blog Post 2',
        'content': 'Second post content',
        'date_posted': 'April 21, 2018'
    }
]


@app.route("/")
@app.route("/home")
def home():
    return render_template('home.html', posts=posts)


@app.route("/about")
def about():
    return render_template('about.html', title="about")


@app.route("/register", methods=['POST', 'GET'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash(f'account created for {form.username.data},you can log in now', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title="Register", form=form)


@app.route("/login", methods=['POST', 'GET'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
            # return redirect('home')
        else:
            flash('login unsuccessfully,please check email:( ', 'warning')

    return render_template('login.html', title="login", form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect('home')

# @app.route("/account")
# def account():
#     return render_template('account.html', title="account")


def save_picture(form_picture_data):
    hex_name = secrets.token_hex(8)
    _, file_ext = os.path.splitext(form_picture_data.filename)
    # file_name = hex_name + file_ext
    file_name = os.path.join(hex_name, file_ext)
    size = (125, 125)
    image = Image.open(form_picture_data)
    image.thumbnail(size)
    path = os.path.join(app.root_path, 'static/profile_image', file_name)
    image.save(path)
    return file_name


@app.route("/account", methods=['POST', 'GET'])
@login_required
def account():
    form = UpdateInfoForm()
    if request.method == "GET":
        form.username.data = current_user.username
        form.email.data = current_user.email
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        if form.image_file.data:
            image_name = save_picture(form.image_file.data)
            current_user.profile_image = image_name
        db.session.commit()

        return redirect(url_for('account'))

    picture_file = url_for('static', filename=f'profile_image/{current_user.profile_image}')
    return render_template('account.html', title="account", picture_file=picture_file, form=form)
