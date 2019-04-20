from flask import Flask, redirect, url_for, request, flash, send_from_directory
from flask_login import UserMixin, login_required, login_user, logout_user, current_user, LoginManager
from werkzeug.utils import secure_filename
import os

app = Flask(__name__, static_url_path='')

with open("secretkey.txt") as secretfile:
	app.secret_key = secretfile.read()
login_manager = LoginManager()
login_manager.init_app(app)

users = {
	'llama': { 'password': 'adventure' }
}

class User(UserMixin):
    pass

@login_manager.user_loader
def user_loader(username):
    if username not in users:
        return
    user = User()
    user.id = username
    return user

@login_manager.request_loader
def request_loader(request):
    username = request.form.get('un')
    if username not in users:
        return

    user = User()
    user.id = username

    # DO NOT ever store passwords in plaintext and always compare password
    # hashes using constant-time comparison!
    user.is_authenticated = username in users and request.form['pw'] == users[username]['password']

    return user




@app.route("/")
def home():
	return """
<a href="/about-us.html">About Us</a><br/>
<a href="/charity.html">Charities</a><br/>
<a href="/login">Login</a><br/>
<a href="/logout">Logout</a><br/>
<a href="/upload">Upload</a><br/>
<a href="/backstage">Backstage</a><br/>
"""





@app.route("/about")
def about():
	app.send_static_file("about.html")

@app.route("/charity")
def charity():
	app.send_static_file("charity.html")



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return app.send_static_file("login.html")

    username = request.form['un']
    if username in users and request.form['pw'] == users[username]['password']:
        user = User()
        user.id = username
        login_user(user)
        return redirect(url_for('home'))

    return 'Bad login'





@app.route("/upload", methods=['GET', 'POST'])
@login_required
def upload():
	if request.method == "POST":
		if 'file' not in request.files:
			return "error"
		files = request.files.getlist('file')
		names = []
		for file in files:
			if not file or file.filename == '':
				continue
			filename = secure_filename(file.filename)
			names.append(filename)
			file.save(os.path.join("static", "uploads", filename))
		return redirect(url_for('gallery', img=names))
	return app.send_static_file("upload.html")



@app.route("/gallery")
def gallery():
	html = ""
	names = request.args.getlist('img')
	for name in names:
		html += "<img src='uploads/" + name + "'></img>"
	return html


@app.route("/backstage")
@login_required
def backstage():
	return "backstage wow"



@app.route('/logout')
def logout():
    logout_user()
    return 'Logged out'


@login_manager.unauthorized_handler
def unauthorized_handler():
    return redirect(url_for('login'))


