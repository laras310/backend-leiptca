import mysql.connector
from flask import Flask, render_template, request, redirect, url_for, session, send_file

mydb = mysql.connector.connect(
  host="127.0.0.1",
  user="root",
  password="",
  database="leiptca"
)

# cursor.execute('SELECT name FROM user')
# user = cursor.fetchone()
# print(user)

# inisiasi variabel aplikasi
app = Flask(__name__)
cursor = mydb.cursor()

@app.route('/', methods=['GET', 'POST'])
def function():
    # if not 'loggedin' in session:
    #     return redirect(url_for('login'))
    # return redirect(url_for('home'))
    cursor.execute('SELECT name FROM user')
    user = cursor.fetchone()
    return user[0]

if __name__ == 'main':
    app.run(host='0.0.0.0',port=8080)
