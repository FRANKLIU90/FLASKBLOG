import secrets
import os
from PIL import Image
from flaskblog import app, bcrypt, db
from flask import render_template, url_for, flash, redirect, request, abort
from flaskblog.forms import RegistrationForm, LoginForm, UpdateInfoForm, PostForm
from .models import User, Post
from flask_login import login_user, current_user, logout_user, login_required


@app.route("/")
@app.route("/home")
def home():
    page = request.args.get('page', type=int)
    posts = Post.query.paginate(per_page=5, page=page)
    # posts = posts.items
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


@app.route("/post/new", methods=['POST', 'GET'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data, content=form.content.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        return redirect('home')
    return render_template('new_post.html', form=form)


@app.route("/post/<int:post_id>")
def post_detail(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post_detail.html', post=post)


@app.route("/post/<int:post_id>/update", methods=['POST', "GET"])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if current_user != post.author:
        return abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash('your updated your post', 'success')
        return redirect(url_for('post_detail', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
    return render_template('new_post.html', post=post, form=form)


@app.route("/post/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if current_user != post.author:
        return abort(403)
    db.session.delete(post)
    db.session.commit()
    return redirect(url_for('home'))


@app.route("/user/<string:username>")
def user_post(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = Post.query.filter_by(author=user).\
        order_by(Post.date_posted.desc()).\
        paginate(per_page=5, page=page)
    return render_template('user_posts.html', user=user, posts=posts)
