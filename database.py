import sqlite3
conn = sqlite3.connect('project.db')
#conn = sqlite3.connect(':memory:')
c = conn.cursor()

c.execute("""CREATE TABLE clients (
            name text,
            surname text,
            email text,
            username text,
            password text
)""")


c.execute(""" CREATE TABLE credit_apps(
        name text,
        second_name text,
        surname text,
        PESEL text,
        Dateofbirth date,
        sex text,
        telephone text,
        email text,
        maritalstatus text,
        education text,
        income text,
        formofemployment  text,
        numberofpeopleinhousehold text,
        loanamount text,
        accept boolean,
        date_app date
)""")


c.execute(""" CREATE TABLE new_credit_app(
        name text,
        second_name text,
        surname text,
        PESEL text,
        Dateofbirth date,
        sex text,
        telephone text,
        email text,
        maritalstatus text,
        education text,
        income text,
        formofemployment  text,
        numberofpeopleinhousehold text,
        loanamount text
)""")


c.execute(""" CREATE TABLE employees(
        login text,
        password text,
        emp_id text)""")


conn.close()