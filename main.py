from flask import Flask, render_template, request, jsonify, flash, redirect, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text, create_engine, text
conn_str = "mysql://root:cset155@localhost/exam_management_2"
engine = create_engine(conn_str, echo = True)
conn = engine.connect()

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
    test_scores = db.relationship('Student_Test_Scores', backref='test', cascade="all, delete-orphan", passive_deletes=True)


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

class Student_Test_Scores(db.Model):
    __tablename__ = 'student_test_scores'

    student_username = db.Column(
        db.Text,
        db.ForeignKey('student.student_username'),
        primary_key=True
    )
    
    test_id = db.Column(
        db.Integer, 
        db.ForeignKey('test.test_id', ondelete="CASCADE"),
        primary_key=True
    )

    score = db.Column(db.Integer, nullable=False)

    # relationships to access linked objects for querying data easier (as it limits errors)
    # student = db.relationship('Student', backref='test_scores')
    # back_populates = db.relationship('Test', backref='test_scores')

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/Account', methods = ['GET', 'POST'])
def account():
    account_type = request.args.get('type')
    accounts = []
    if account_type == ' teacher':
        teachers = conn.execute(text('select * from teacher')).all()
        student = conn.execute(text('select * from student')).all()

   

    return render_template('accounts.html', accounts=accounts, selected_type=account_type)

@app.route('/Login', methods = ['GET', 'POST'])
def login():
    app.secret_key = "your-secret-key"

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        fullname = request.form['fullname']
        account_type = request.form['account_type']

        if not username or not password or not fullname:
            error = "All fields (Full Name, Username, and Password) are required"
            return render_template('login.html', error=error)
        if account_type == 'student':
            student = Student.query.filter_by(student_username=username, student_fullname=fullname).first()
            if student and student.student_password == password:
                session['fullname'] = fullname
                session['username'] = username
                session['account_type'] = account_type
                return render_template('take_test.html')
            else:
                error = "Invalid username, full name, or password for student"
                return render_template('login.html', error=error)
        elif account_type == 'teacher':
            teacher = Teacher.query.filter_by(teacher_username=username, teacher_fullname=fullname).first()
            if teacher and teacher.teacher_password == password:
                session['username'] = username
                session['account_type'] = account_type
                return render_template('accounts.html')  
            else:
                error = "Invalid username, full name, or password for teacher"
                return render_template('login.html', error=error)
        else:
            error = "Invalid account type selected"
            return render_template('login.html', error=error)
        
    return render_template('login.html')

@app.route('/test_db')
def test_db_connection():
    try:
        result = db.session.execute('SELECT 1')
        return "Database connection successful!", 200
    except Exception as e:
        return f"Error connecting to the database: {e}", 500

@app.route('/Signup', methods = ['GET', 'POST'])
def signup():
    if request.method == 'POST':
        account_type = request.form['account_type']
        fullname = request.form['fullname']
        username = request.form['username']
        password = request.form['password']

        if not fullname or not username or not password:
            return render_template('signup.html', error="All fields are required")

        if account_type == 'teacher':
            if Teacher.query.filter_by(teacher_username=username).first():
                return render_template('signup.html', error="Teacher username already exists")
            new_user = Teacher(teacher_fullname=fullname, teacher_username=username, teacher_password=password)
        elif account_type == 'student':
            if Student.query.filter_by(student_username=username).first():
                return render_template('signup.html', error="Student username already exists")
            new_user = Student(student_fullname=fullname, student_username=username, student_password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect('/Login')

    return render_template('signup.html')

@app.route('/take_test')
def take_test_selector():
    return render_template('take_test.html', student_fullname=session.get("fullname"))

@app.route('/take_test/<int:test_id>')
def take_test(test_id):
    test = Test.query.get_or_404(test_id)
    return render_template('take_test.html', test=test, student_fullname=session.get("fullname"))


@app.route('/test_management')
def test_management():
    return render_template('test_management.html')

@app.route('/api/create_test', methods=['POST']) # this is a post method since it's used to send data to SQL database
def create_test():
    data = request.get_json() # receives the JSON string from JS (remember, it was stored in the payload object)
    test_name = data.get("test_name") # Grabs test name from the test_name var in JS file
    questions_data = data.get("questions", []) # grabs the questions from the created tests stored in the JS's questions var, then stores them in the empty array here

    # Temporary teacher for demo (adjust this later to the logged-in teacher using session['teacher_id'])
    teacher_fullname = data.get("teacher_fullname")
    teacher = Teacher.query.filter_by(teacher_fullname=teacher_fullname).first()

    if not teacher:
        teacher = Teacher(
            teacher_fullname=teacher_fullname,
            teacher_username=teacher_fullname.lower().replace(" ", "_"),
            teacher_password="defaultpass"  # You can change this logic
        )
        db.session.add(teacher)
        db.session.flush()  # Add it without committing yet
        
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

@app.route('/api/test/<int:test_id>', methods=['DELETE']) # method for deleting test in edit side of test management section
def delete_test(test_id): # method for deleting the test using the given test_id from the user 
    try: # try statements are used in cases of failure
        test = db.session.get(Test, test_id) # pull the test we are going to delete

        if not test: # if that test isn't found (which it should be because the delete button won't load without the test being found but I thought I would put this here regardless)
            return jsonify({"error": "Test not found"}), 404

        db.session.delete(test) # attempts to delete test
        db.session.commit() # then commits that change to the database

        return jsonify({"message": "Test deleted successfully"}), 200 # tell user the test was successfully deleted

    except Exception as e: # if an error occured:
        print(f"Error deleting test: {e}") # print to console what error stopped the system from deleting said test
        db.session.rollback() # I don't know
        return jsonify({"error": "Failed to delete test"}), 500 # return JSON object describing issue
    
@app.route("/api/check_submission")
def check_submission():
    student_fullname = request.args.get("student_fullname")
    test_id = request.args.get("test_id")

    result = db.session.execute(
        text("SELECT 1 FROM student_answers WHERE student_fullname = :name AND test_id = :tid LIMIT 1"),
        {"name": student_fullname, "tid": test_id}
    ).fetchone()

    return jsonify({"alreadySubmitted": result is not None})

@app.route('/api/submit_answers', methods=['POST'])
def submit_answers():
    try:
        data = request.get_json()
        student_fullname = data.get("student_fullname")

        test_id = data.get("test_id")
        answers = data.get("answers", [])
        submission_id = data.get("submission_id")

        for q in answers:
            question_text = q["question_text"]
            question_type = q["question_type"]

            question = Question.query.filter_by(test_id=test_id, question_text=question_text).first()
            if not question:
                print(f"Question not found for: {question_text}")
                continue

            if question_type == "short":
                short_answer = q.get("short_answer", "")
                db.session.execute(
                    text("INSERT INTO student_answers (submission_id, student_fullname, test_id, question_id, short_answer_text) VALUES (:id, :name, :test, :qid, :answer)"),
                    {
                        "id": submission_id,
                        "name": student_fullname,
                        "test": test_id,
                        "qid": question.question_id,
                        "answer": short_answer
                    }
                )

            elif question_type == "multiple":
                choices = q.get("choices", [])
                selected_choice = next((c for c in choices if c.get("selected")), None)

                if selected_choice:
                    db.session.execute(
                        text("INSERT INTO student_answers (submission_id, student_fullname, test_id, question_id, selected_choice_id) VALUES (:id, :name, :test, :qid, :cid)"),
                        {
                            "id": submission_id,
                            "name": student_fullname,
                            "test": test_id,
                            "qid": question.question_id,
                            "cid": selected_choice["choice_id"]
                        }
                    )
        db.session.commit()
        return jsonify({"message": "Answers submitted successfully!"}), 200

    except Exception as e:
        print("Error submitting answers:", e)
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
        app.run(debug=True)