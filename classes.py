from wtforms import Form, StringField, TextAreaField, PasswordField, validators, DateField, IntegerField, SelectField
from flask import Flask, render_template, url_for, flash, request, redirect, url_for, session, logging
import sqlite3
from time import gmtime, strftime
import pandas as pd


class Client_check:

    def __init__(self, name, second_name, surname, PESEL, DateOfBirth, sex, telephone, email,
                 maritalstatus, education, income, formofemployment, numberofpeopleinhousehold,
                 loanamount):
        self.name = name
        self.second_name = second_name
        self.surname = surname
        self.PESEL = PESEL
        self.DateOfBirth = DateOfBirth
        self.sex = sex
        self.telephone = telephone
        self.email = email
        self.maritalstatus = maritalstatus
        self.education = education
        self.income = income
        self.formofemployment = formofemployment
        self.numberofpeopleinhousehold = numberofpeopleinhousehold
        self.loanamount = loanamount

    def new_client(self):
        conn = sqlite3.connect('project.db')
        c = conn.cursor()
        # Execute query
        c.execute("INSERT INTO new_credit_app VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
            self.name, self.second_name, self.surname, self.PESEL, self.DateOfBirth, self.sex, self.telephone, self.email, self.maritalstatus, self.education, self.income,
            self.formofemployment, self.numberofpeopleinhousehold, self.loanamount))
        # Commit to DB
        conn.commit()
        conn.close()

    def check_history(self):
        conn = sqlite3.connect('project.db')
        c = conn.cursor()
        df = pd.read_sql_query(
            'SELECT credit_apps.accept from new_credit_app LEFT JOIN credit_apps ON new_credit_app.pesel=credit_apps.pesel',
            conn)
        client = pd.read_sql_query('SELECT * from new_credit_app', conn)
        conn.close()
        df = list(df['accept'])
        suma = sum(filter(None, df))
        length = len(df)
        if len(df) < 1:
            counter_length = 1
        else:
            counter_length = (suma/len(df))



        return counter_length, client

    def education_score(self):
        risk_counter = 0
        if self.education == 1:
            risk_counter += 0
        elif self.education == 2:
            risk_counter += 5
        elif self.education == 3:
            risk_counter += 10
        return risk_counter

    def maritalstatus_score(self):
        maritalstatus_score = 0
        if self.maritalstatus == 1:
            maritalstatus_score += 0
        elif self.maritalstatus == 2:
            maritalstatus_score += 3
        elif self.maritalstatus == 3:
            maritalstatus_score += 6
        return maritalstatus_score

    def formofemployment_score(self):
        employment_score = 0
        if self.formofemployment == 1:
            employment_score += 10
        else:
            employment_score += 3
        return employment_score

    def income_score(self):
        incomeratio_score = 0
        if self.loanamount / (float(self.income) * 12) < 0.1:
            incomeratio_score = 20
        elif self.loanamount / (float(self.income) * 12) < 0.3:
            incomeratio_score = 10
        elif self.loanamount / (float(self.income) * 12) < 0.5:
            incomeratio_score = 5
        else:
            incomeratio_score = 0
        return incomeratio_score

    def overall_score(self):
        client = self.check_history()[1]
        date_app = strftime("%Y-%m-%d", gmtime())
        input_list = list(client)
        input_list.append('accept')
        input_list.append('date')
        client = client.values.tolist()[0]
        input_values = client
        if (self.maritalstatus_score() + self.formofemployment_score() + self.income_score() + self.education_score() > 20):
            flash('You get a credit!:)', 'success')
            input_values.append(1)
            input_values.append(date_app)
            conn = sqlite3.connect('project.db')
            c = conn.cursor()
            c.execute("INSERT INTO credit_apps VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", input_values)
            # Commit to DB
            conn.commit()
            conn.close()
        else:
            flash('You do not get a credit!', 'danger')
            input_values.append(0)
            input_values.append(date_app)
            conn = sqlite3.connect('project.db')
            c = conn.cursor()
            c.execute("INSERT INTO credit_apps VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", input_values)
            # Commit to DB
            conn.commit()
            conn.close()

        conn = sqlite3.connect('project.db')
        c = conn.cursor()
        c.execute('DELETE  FROM new_credit_app')
        conn.commit()
        conn.close()



class RegisterForm(Form):
    username = StringField('Username',[validators.Length(min=4,max=25)])
    pesel = StringField('PESEL', [validators.Length(min=11, max=11)])
    password = PasswordField('Password',[
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Password do no match')
        ])
    confirm = PasswordField('Confirm Password')


class CreditForm(Form):
    name = StringField('Name',[validators.Length(min=1,max=50)])
    second_name = StringField('Second Name')
    surname = StringField('Surname',[validators.Length(min=1,max=25)])
    pesel = StringField('PESEL',[validators.Length(min=11,max=11)])
    dateofbirth = DateField('Date of birth (yyyy-mm-dd)')
    sex = SelectField('Sex', choices=[('0', 'Male'), ('1','Female')])
    telephone = StringField('Telephone number')
    email = StringField('Email')
    # idnumber = StringField('ID number')
    maritalstatus = SelectField('Marital status', choices=[('1','Engaged'),('2','Single'),('3','Married')])
    education = SelectField('Education', choices=[('1', 'Primary'),('2', 'Secondary'), ('3','Higher')])
    # sourceofincome = StringField('Source of Income')
    income = IntegerField('Income (per month)', [validators.required()])
    formofemployment = SelectField('Form of employment', choices=[('1','Contract of employment'),('2','Contract of mandate'),('3','Contract of specific work'),('4','B2B')])
    numberofpeopleinhousehold = SelectField('Number of people in household', choices=[('1',1),('2',2),('3',3),('4',4),('5',5),('6','6+')])
    # purposeofcredit = StringField('Loan purpose')
    loanamount = IntegerField('Loan amount', [validators.required()])
