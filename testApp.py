# app.py
from flask import Flask  , render_template         # import flask and render template
app = Flask(__name__)             # create an app instance

# @app.route("/<name>")              # at the end point /<name>
# def hello_name(name):              # call method hello_name
#     return "Hello "+ name          # which returns "hello + name   


# @app.route('/')
# def index():
#    return render_template('hello.html')



@app.route('/hello/<user>')
def hello_name(user):
   return render_template('hello.html', name = user)



if __name__ == "__main__":        # on running python app.py
    app.run(debug = True )                     # run the flask app




