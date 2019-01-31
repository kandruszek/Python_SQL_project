from flask import Flask, render_template, url_for, flash, request, redirect, url_for, session, logging, make_response
import sqlite3
import numpy as np
import pandas as pd
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
#from passlib.hash import sha256_crypt
from classes import RegisterForm, CreditForm,  Client_check
from functools import wraps
import logging
from werkzeug import MultiDict
import json
from random import randint


app = Flask(__name__)
# app.debug=True

# Home page
@app.route('/home')
@app.route('/')
@app.route('/#')
def home():
    return render_template('home.html')

# Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if ('logged_in' in session) & ('admin' in session):
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login_employee'))
    return wrap

def is_client_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if ('logged_in' in session) & ('user' in session):
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap

# Page for Employees
@app.route('/Employee')
@is_logged_in
def employee():
    return render_template('employee.html')

@app.route('/payments_info')
@is_logged_in
def payments_info():
    admin_name = session['username']

    # Create cursor
    conn = sqlite3.connect('project.db')
    c = conn.cursor()
    # Execute query
    c.execute("SELECT * FROM payment_info LEFT JOIN credit_apps USING(PESEL) WHERE PESEL IN (SELECT PESEL FROM clients WHERE emp_id==(SELECT emp_id FROM employees WHERE username == (?)))", [admin_name])
    listOfResults = c.fetchall()
    conn.close()
    return render_template('payments_info.html', data=json.dumps(listOfResults))

@app.route('/plots')
@is_logged_in
def plots():
    admin_name = session['username']
    # Create cursor
    conn = sqlite3.connect('project.db')
    c = conn.cursor()
    # Execute query
    c.execute("SELECT DISTINCT PESEL FROM payment_info WHERE PESEL IN (SELECT PESEL FROM clients WHERE emp_id==(SELECT emp_id FROM employees WHERE username == (?)))", [admin_name])
    listOfResults = c.fetchall()
    conn.close()

    listOfResults = [round(x[0]) for x in listOfResults]
    return render_template('plots.html', pesels=listOfResults)

@app.route('/plots/<string:pesel>')
@is_logged_in
def plot(pesel):

    # Create cursor
    conn = sqlite3.connect('project.db')
    c = conn.cursor()
    # Execute query
    c.execute("SELECT * FROM payment_info WHERE pesel=(?)", [pesel])
    listOfResults = c.fetchall()
    conn.close()

    myArray = np.asarray(listOfResults)
    line_labels=myArray[:,1].tolist()
    line_values=myArray[:,5].astype(np.float)
    line_values=line_values.tolist()

    df = pd.DataFrame(myArray[:,4])
    df.columns = ['Col1']
    df = pd.value_counts(df.Col1).to_frame().reset_index()
    if (df.shape[0] < 2):
        pie_values = [df.Col1.values[0], 0]
    else:
        pie_values = [df.Col1.values[0], df.Col1.values[1]]

    dates = pd.to_datetime(myArray[:, 1])
    df = pd.DataFrame(data=pd.to_numeric(myArray[:, 2]), index=dates)
    groupped = df.groupby(pd.Grouper(freq="M"))
    dataToPlot = groupped.sum()

    bar_labels = dataToPlot.index.values
    bar_labels = bar_labels.astype(dtype='M8[D]')
    bar_values = [val for sublist in dataToPlot.values for val in sublist]

    return render_template('plot.html', title='Info about client '+pesel, line_labels=json.dumps(line_labels), line_values=line_values, pie_data=pie_values, bar_labels=bar_labels, bar_values=bar_values)

@app.route('/account/')
@is_client_logged_in
def account():

    # Create cursor
    conn = sqlite3.connect('project.db')
    c = conn.cursor()

    # client pesel
    username = session['username']

    # Execute query
    c.execute("SELECT * FROM payment_info WHERE pesel in (SELECT DISTINCT PESEL FROM clients WHERE username in (?))", [username])
    listOfResults = c.fetchall()
    conn.close()

    myArray = np.asarray(listOfResults)
    if len(myArray)>0:
        line_labels=myArray[:,1].tolist()
        line_values=myArray[:,5].astype(np.float)
        line_values=line_values.tolist()
        title='Money still owed by you'
    else:
        line_labels = []
        line_values = []
        title='Your history is empty. Maybe get a loan?'
    return render_template('account.html', title=title, labels=json.dumps(line_labels), values=line_values)


# Register page
@app.route('/register', methods=['GET','POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        username = form.username.data
        pesel = form.pesel.data
        password = form.password.data
        emp_id = randint(1,2)
        # Create cursor
        conn = sqlite3.connect('project.db')
        c = conn.cursor()
        # Execute query
        c.execute("INSERT INTO clients(username, password, pesel, emp_id) VALUES(?,?,?,?)", (username, password, pesel,emp_id))
        # Commit to DB
        conn.commit()
        conn.close()

        flash('You are now registered and can log in', 'success')
        return redirect(url_for('home'))
    return render_template('register.html', form=form)


@app.route('/credit', methods=['GET','POST'])
@is_client_logged_in
def credit():
    form = CreditForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        second_name = form.second_name.data
        surname = form.surname.data
        pesel = form.pesel.data
        dateofbirth = form.dateofbirth.data
        sex = form.sex.data
        telephone = form.telephone.data
        email = form.email.data
        maritalstatus = form.maritalstatus.data
        education = form.education.data
        income = form.income.data
        formofemployment = form.formofemployment.data
        numberofpeopleinhousehold = form.numberofpeopleinhousehold.data
        loanamount = form.loanamount.data

        client = Client_check(name, second_name, surname, pesel, dateofbirth,sex,telephone,email,maritalstatus,education,income,formofemployment,numberofpeopleinhousehold,loanamount)
        client.new_client()
        client.overall_score()

        return redirect(url_for('home'))
    return render_template('credit.html', form=form)




# User logged_in
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        #get form fields
        username = request.form['username']
        password_candidate = request.form['password']
        # Create cursor
        conn = sqlite3.connect('project.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        # get user by Username
        result = c.execute("SELECT * FROM clients WHERE clients.username =:username", {'username': username})
        data = result.fetchone()
        if data is not None:
            password = data['password']
            #compare passwords
            if password_candidate == password:
                session['logged_in'] = True
                session['username'] = username
                session['user'] = True
                flash('You are now logged in', 'success')
                return redirect(url_for('home'))
            else:
                error = 'Invalid user'
                return render_template('login.html', error=error)

            conn.close()

        else:
            error ='Username not found'
            return render_template('login.html', error=error)


    return render_template('login.html')

@app.route('/login_employee', methods=['GET', 'POST'])
def login_employee():
    if request.method == 'POST':
        #get form fields
        username = request.form['username']
        password_candidate = request.form['password']
        # Create cursor
        conn = sqlite3.connect('project.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        # get user by Username
        result = c.execute("SELECT * FROM employees WHERE employees.username =:username", {'username': username})
        data = result.fetchone()
        if data is not None:
            # get stored hash
            password = data['password']
            #compare passwords
            if password_candidate == password:
                session['logged_in'] = True
                session['username'] = username
                session['admin'] = True
                flash('You are now logged in', 'success')
                return redirect(url_for('employee'))
            else:
                error = 'Invalid user'
                return render_template('login_employee.html', error=error)
            conn.close()
        else:
            error ='Username not found'
            return render_template('login_employee.html', error=error)
    return render_template('login_employee.html')



# Logout
@app.route('/logout')
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.secret_key='secret123'
    app.run(debug=True)