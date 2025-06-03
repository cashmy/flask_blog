from flaskblog import create_app
from dotenv import load_dotenv

app = create_app()

# Added in order to use the Python script as a module as an option to "flask run"
if __name__ == '__main__':
	load_dotenv() 
	app.run(debug=True)
