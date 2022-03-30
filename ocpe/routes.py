from functools import wraps
from pydoc import describe
from turtle import title
from flask import render_template, url_for, flash, redirect, request
from ocpe import app, db, bcrypt
from ocpe.forms import PostProblemForm, SignupForm, LoginForm
from ocpe.models import User, Contestant, Judge, Submission, Problem
from flask_login import login_user, current_user, logout_user, login_required
from ocpe.forms import SignupForm

#have to access problems from database
def contestant_required(func):
    '''If you decorate a view with this, it will ensure that the current user is a contestant'''
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if (not current_user.is_anonymous) and current_user.GetType() != "contestant":
            flash('Login as contestant to access this page.', 'danger')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        return func(*args, **kwargs)
    return decorated_view


def judge_required(func):
    '''If you decorate a view with this, it will ensure that the current user is a judge'''
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if (not current_user.is_anonymous) and current_user.GetType() != "judge":
            flash('Login as judge to access this page.', 'danger')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        return func(*args, **kwargs)
    return decorated_view


@app.route("/")
@app.route("/home")
def home():
    return render_template('index.html')

@app.route("/signup", methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = SignupForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        type = form.type.data
        if type=='judge':
            user = Judge(username=form.username.data, email=form.email.data, password=hashed_password, type=type)
        else:
            user = Contestant(username=form.username.data, email=form.email.data, password=hashed_password, type=type)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('signup.html', title='Signup', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route("/logout")
def logout():
    logout_user()
    flash('Logout Successful!', 'success')
    next_page = request.args.get('next')
    return redirect(next_page) if next_page else redirect(url_for('home'))


@app.route("/account")
@login_required
def account():
    return render_template('account.html', title='Account')

# extra routes
@app.route("/contests")
def contests():
   return render_template('contests.html', title='Contests')

@app.route("/contest")
def contest():
   return render_template('contest.html', title='Contest #')
# end extra routes

#this needs a post problem frontend html file
@app.route("/create_problem", methods=['GET', 'POST'])
@login_required
@judge_required
def create_problem():
    form = PostProblemForm()
    if form.validate_on_submit():
        problem = Problem(name=form.name.data, title=form.title.data, description=form.description.data, testInput=form.testInput.data, testOutput=form.testOutput.data, score=form.score.data)
        db.session.add(problem)
        db.session.commit()
        flash('The problem has been added to practice section!', 'success')
        return redirect(url_for('login'))
    return render_template('create_problem.html', title='Problems', form=form)

#this is where problems will appear as in codechef front page
@app.route("/practice")
@login_required
@contestant_required
def practice():
    problems = Problem.query.all()
    return render_template('practice.html',title="Practice", problems=problems)		

#dynamic-routing
@app.route('/problem/<problemId>', methods=['GET'])
def problem(problemId):
    problem = Problem.query.filter_by(id=problemId).first()
    if problem:
        return render_template('question.html', title= f"Problem {problemId}", problem=problem)
    else:
        return render_template('404.html', title="404")

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html', title="404")