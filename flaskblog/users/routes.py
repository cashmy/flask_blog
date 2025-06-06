import secrets
import os
import requests

from flask import render_template, url_for, flash, redirect, request, Blueprint
from flask_login import current_user, login_required, login_user, logout_user
from flaskblog import db, bcrypt
from flaskblog.models import User, Post
from flaskblog.users.forms import (RegistrationForm, LoginForm, UpdateAccountForm,
									RequestResetForm, ResetPasswordForm)
from flaskblog.users.utils import save_picture, send_reset_email



users = Blueprint('users', __name__)

@users.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('users.login'))
    return render_template('register.html', title='Register', form=form)


@users.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)


@users.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.home'))


def upload_to_vercel_blob(file_storage):
    """
    Uploads a file to Vercel Blob and returns the public URL.
    Returns None if the upload fails.
    """
    # 1. Get credentials and read file data
    blob_token = os.environ.get('BLOB_READ_WRITE_TOKEN')
    if not blob_token:
        flash('Blob storage credentials are not configured.', 'danger')
        return None

    # 2. Generate a secure, random filename
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(file_storage.filename)
    unique_filename = random_hex + f_ext
    
    # You can add a folder path for organization
    blob_path = f"profile_pics/{unique_filename}"

    # 3. Construct the API URL and headers
    upload_url = f"https://blob.vercel-storage.com/{blob_path}"
    headers = {
        'Authorization': f'Bearer {blob_token}',
        'Content-Type': file_storage.content_type
    }

    # 4. Upload the file
    try:
        response = requests.put(
            upload_url,
            data=file_storage.read(),
            headers=headers
        )
        response.raise_for_status()  # Raise an error for bad status codes
        
        # 5. Return the public URL from the response
        return response.json().get('url')

    except requests.exceptions.RequestException as e:
        flash(f'Error uploading file: {e}', 'danger')
        return None


@users.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        # If the user submitted a new picture, upload it
        if form.picture.data:
            public_url = upload_to_vercel_blob(form.picture.data)
            if public_url:
                # If upload was successful, save the new URL
                current_user.image_file = public_url

        # Update other user details
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        
        flash('Your account has been updated!', 'success')
        return redirect(url_for('users.account'))

    elif request.method == 'GET':
        # Pre-populate the form with current user data
        form.username.data = current_user.username
        form.email.data = current_user.email

    # THE FIX: Pass the full URL directly to the template.
    # If the user has no picture, this will be None or an empty string.
    image_file = current_user.image_file 

    return render_template(
        'account.html', title='Account', image_file=image_file, form=form
    )


@users.route("/user/<string:username>")
def user_posts(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(author=user)\
        .order_by(Post.date_posted.desc())\
        .paginate(page=page, per_page=5)
    return render_template('user_posts.html', posts=posts, user=user)



@users.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RequestResetForm()   
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_reset_email(user)
            flash('An email has been sent with instructions to reset your password.', 'info')
            return redirect(url_for('users.login'))
        else:
            flash('No account found with that email.', 'danger')
    return render_template('reset_request.html', title='Reset Password', form=form)


@users.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('users.reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash('Your password has been updated! You are now able to log in', 'success')
        return redirect(url_for('users.login'))
    return render_template('reset_token.html', title='Reset Password', form=form)