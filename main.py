from flask import Flask, render_template, request
from sqlalchemy import create_engine, text
app = Flask(__name__)
conn_str = "mysql://root:cset155@localhost/exam_management_2"
engine = create_engine(conn_str, echo = True)
conn = engine.connect()

@app.route('/')
def MySandwichItWasInnocent():
    return render_template('index.html')

@app.route('/Account')
def ThisIsWhyImDepressedAtNight():
    return render_template('accounts.html')


@app.route('/Login')
def YouCanCallMeTiffany():
    return render_template('login.html')

@app.route('/Signup')
def TomdaciLifeTwo():
    return render_template('signup.html')

@app.route('/take_test')
def HowHow():
    return render_template('take_test.html')

@app.route('/Test_mangment')
def SayDrake():
    return render_template('test_mangment.html')





