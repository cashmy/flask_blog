from flaskblog import app

# Added in order to use the Python script as a module as an option to "flask run"
if __name__ == '__main__':
	app.run(debug=True)
