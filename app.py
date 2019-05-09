from flask import Flask, redirect, url_for, request, flash, send_from_directory, render_template
from flask_login import UserMixin, login_required, login_user, logout_user, current_user, LoginManager
from werkzeug.utils import secure_filename
import os

app = Flask(__name__, static_url_path='')

with open("secretkey.txt") as secretfile:
	app.secret_key = secretfile.read()
login_manager = LoginManager()
login_manager.init_app(app)

users = {
	'llama': { 'display_name': 'Test Account', 'password': 'adventure' }
}
countries = """finland
sweden
denmark
germany
czechia
austria
slovakia
hungaria
serbia
kosovo
bulgaria
turkey
georgia
azerbaijan
kazakhstan
russia
mongolia""".splitlines()

for country in countries:
	try:
		os.mkdir("static/uploads/" + country)
	except:
		pass

current_country = "kosovo"

class User(UserMixin):
    display_name = "(none)"

@login_manager.user_loader
def user_loader(username):
    if username not in users:
        return
    user = User()
    user.id = username
    user.display_name = users[username]["display_name"]
    return user

@login_manager.request_loader
def request_loader(request):
    username = request.form.get('un')
    if username not in users:
        return

    user = User()
    user.id = username
    user.display_name = users[username]["display_name"]

    # DO NOT ever store passwords in plaintext and always compare password
    # hashes using constant-time comparison!
    user.is_authenticated = username in users and request.form['pw'] == users[username]['password']

    return user




@app.route("/")
@app.route("/index.html")
def home():
	return """
<a href="/about-us.html">About Us</a><br/>
<a href="/charity.html">Charities</a><br/>
<a href="/login">Login</a><br/>
<a href="/logout">Logout</a><br/>
<a href="/upload">Upload</a><br/>
<a href="/backstage">Backstage</a><br/>
<a href="/gallery?country=">Gallery</a><br/>
"""






@app.route("/charity")
@app.route("/charity.html")
def charity():
	return app.send_static_file("charity.html")



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return app.send_static_file("login.html")

    username = request.form['un']
    if username in users and request.form['pw'] == users[username]['password']:
        user = User()
        user.id = username
        user.display_name = users[username]["display_name"]
        login_user(user)
        return redirect(url_for('home'))

    return 'Bad login'





import json, uuid
@app.route("/upload", methods=['GET', 'POST'])
@login_required
def upload():
	if request.method == "POST":
		country = request.form.get("country")
		if country not in countries:
			return "invalid country"
		if 'file' not in request.files:
			return "please upload a file"
		files = request.files.getlist('file')
		#names = []
		for file in files:
			if not file or file.filename == '':
				continue
			# filename = secure_filename(file.filename)
			# filename = hash_file(file)
			filename = uuid.uuid4().hex + ".jpg"
			#names.append(filename)
			file.save(os.path.join("static", "uploads", country, filename))
			with open(os.path.join("static", "uploads", country, filename + ".json"), "w") as fh:
				json.dump({
					"published": False,
					"deleted": False,
					"filename": filename,
					"author": current_user.display_name,
					"blurb": "",
					"original_filename": secure_filename(file.filename)
				}, fh)
		return redirect(url_for('backstage')) #, img=names
	return render_template("upload.html", countries=countries, current_country=current_country)


import glob
@app.route("/gallery")
def gallery():
	country = request.args.get('country')
	images = []
	for name in glob.glob("static/uploads/" + country + "/*.json"):
		with open(name, "r") as fh:
			data = json.load(fh)
		if data["published"] and not data["deleted"]:
			images.append(data)
	return render_template("index.html", country_name=country, images=images)


@app.route("/backstage")
@login_required
def backstage():
	# get list of unpublished pictures
	images = []
	for country in countries:
		for name in glob.glob("static/uploads/" + country + "/*.json"):
			with open(name, "r") as fh:
				data = json.load(fh)
			if not data["published"] and not data["deleted"]:
				images.append({
					"name": data["filename"],
					"country": country,
					"author": data["author"],
					"url": "/uploads/" + country + "/" + data["filename"]
				})
	return render_template("backstage.html", images=images)


@app.route('/deleteImg', methods=['POST'])
@login_required
def deleteImg():
	if request.form['country'] not in countries:
		return "bad country"
	with open("static/uploads/" + request.form['country'] + "/" + request.form['name'] + ".json", "r") as fh:
		data = json.load(fh)
	if not (data["published"] or data["deleted"]):
		data["deleted"] = True
		with open("static/uploads/" + request.form['country'] + "/" + request.form['name'] + ".json", "w") as fh:
			json.dump(data, fh)
	return "ok"

@app.route('/publishImg', methods=['POST'])
@login_required
def publishImg():
	if request.form['country'] not in countries:
		return "bad country"
	with open("static/uploads/" + request.form['country'] + "/" + request.form['name'] + ".json", "r") as fh:
		data = json.load(fh)
	if not (data["published"] or data["deleted"]):
		data["published"] = True
		data["blurb"] = request.form["blurb"]
		print(data)
		with open("static/uploads/" + request.form['country'] + "/" + request.form['name'] + ".json", "w") as fh:
			json.dump(data, fh)
	return "ok"

@app.route('/logout')
def logout():
    logout_user()
    return 'Logged out<br><br><a href="/">go back to home page</a>'


@login_manager.unauthorized_handler
def unauthorized_handler():
    return redirect(url_for('login'))


