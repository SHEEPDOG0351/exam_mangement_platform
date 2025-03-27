from flask import Flask, render_template, request
from sqlalchemy import create_engine, text
app = Flask(__name__)
conn_str = "mysql://root:cset155@localhost/boatdb"
engine = create_engine(conn_str, echo = True)
conn = engine.connect()

@app.route('/')
def MySandwichItWasInnocent():
    return render_template('index.html')



