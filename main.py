from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Setup MySQL connection for Flask-SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql://root:cset155@localhost/exam_management_2"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# SQLAlchemy Models
class Teacher(db.Model):
    teacher_username = db.Column(db.String(30), nullable=False)
    teacher_fullname = db.Column(db.String(30), primary_key=True)
    teacher_password = db.Column(db.String(30), nullable=False)
    tests = db.relationship('Test', backref='teacher', lazy=True)

class Test(db.Model):
    test_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    test_name = db.Column(db.String(255), nullable=False)
    teacher_fullname = db.Column(db.String(30), db.ForeignKey('teacher.teacher_fullname'))
    questions = db.relationship('Question', backref='test', cascade="all, delete-orphan")

class Question(db.Model):
    __tablename__ = 'question'
    question_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    test_id = db.Column(db.Integer, db.ForeignKey('test.test_id'), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.Enum('short', 'multiple'), nullable=False)
    choices = db.relationship('Choice', backref='question', cascade="all, delete-orphan")

class Choice(db.Model):
    __tablename__ = 'choice'
    choice_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    question_id = db.Column(db.Integer, db.ForeignKey('question.question_id'), nullable=False)
    choice_text = db.Column(db.Text, nullable=False)
    is_correct = db.Column(db.Boolean, default=False)




    
class Student(db.Model):
    __tablename__ = 'student'
    student_fullname = db.Column(db.Text, primary_key=True)
    student_username = db.Column(db.Text, nullable=False)
    student_password = db.Column(db.Text, nullable=False) 

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/Account', methods = ['GET', 'POST'])
def account():
    account_type = request.args.get('type')
    accounts = []
    if account_type == ' student':
        account = Student.query.all()
    elif account_type == ' teacher':
        account = Teacher.query.all()
    else:
        account = Student.query.all() + Teacher.query.all()

    return render_template('accounts.html', accounts=accounts, selected_type=account_type)

@app.route('/Login')
def login():
    return render_template('login.html')

@app.route('/Signup')
def signup():
    return render_template('signup.html')

@app.route('/take_test')
def take_test():
    return render_template('take_test.html')

@app.route('/test_management')
def test_management():
    return render_template('test_management.html')

@app.route('/api/create_test', methods=['POST']) # this is a post method since it's used to send data to SQL database
def create_test():
    data = request.get_json() # receives the JSON string from JS (remember, it was stored in the payload object)
    test_name = data.get("test_name") # Grabs test name from the test_name var in JS file
    questions_data = data.get("questions", []) # grabs the questions from the created tests stored in the JS's questions var, then stores them in the empty array here

    # Temporary teacher for demo (adjust this later to the logged-in teacher using session['teacher_id'])
    teacher = Teacher.query.first() # i think this will use the MR.C value as it's the only value in the teachers table thus far for a teacher's name

    new_test = Test(test_name=test_name, teacher=teacher) # creates a var to store the test data for the teacher and test name column's
    db.session.add(new_test) # then adds the values from the line above to the session var
    db.session.flush()  # Get new_test.test_id before commit

    for q in questions_data: # loops through the array of question data, iterating over each question one at a time
        question = Question( # using the Question object created far above, we assign the required Question's property's their expected values
            test_id=new_test.test_id, # assigns test_ID 
            question_text=q["question_text"], # assigns the question's question (it's text)
            question_type=q["question_type"] # and assigns type whether the question is short or MC
        )
        db.session.add(question) # then adds this data to the database
        db.session.flush()

        if q["question_type"] == "multiple": # if type for question is MC
            for c in q["choices"]: # for choice in the questions choices
                choice = Choice( # assigns the choices the user can select to the predefined Choice object created far above, then assigns it's values below
                    question_id=question.question_id, # assigns question ID the choice belongs to
                    choice_text=c["choice_text"], # assigns the choice's text
                    is_correct=c.get("is_correct", False) # if a choices value has a is_correct value, then the system uses that value for determining if the question is correct, if not, the value is set to False to avoid erroring
                )
                db.session.add(choice) # actually adds the choice to the choices table

    db.session.commit() # adds all changes and sends the data to the database
    return jsonify({"message": "Test created successfully", "test_id": new_test.test_id}), 201 # tells us the test was created, and gives us the test ID created for said test


@app.route('/api/test/<int:test_id>')
def get_test(test_id):
    test = Test.query.get_or_404(test_id)

    test_data = {
        "test_id": test.test_id,
        "test_name": test.test_name,
        "questions": []
    }

    for question in test.questions:
        question_data = {
            "question_id": question.question_id,
            "question_text": question.question_text,
            "question_type": question.question_type,
            "choices": []
        }

        if question.question_type == 'multiple':
            for choice in question.choices:
                question_data["choices"].append({
                    "choice_id": choice.choice_id,
                    "choice_text": choice.choice_text,
                    "is_correct": choice.is_correct
                })

        test_data["questions"].append(question_data)

    return jsonify(test_data)
if __name__ == '__main__':
        app.run(debug=True)