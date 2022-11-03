from urllib import response
import mysql.connector
from flask import Flask, make_response, render_template, request, redirect, url_for, session, send_file, abort, jsonify

mydb = mysql.connector.connect(
  host="127.0.0.1",
  user="root",
  password="",
  database="leiptca_web"
)

# inisiasi variabel aplikasi
app = Flask(__name__)
cursor = mydb.cursor(dictionary=True)
app.secret_key="abcd"

@app.route('/login', methods=['POST'])
# def login():
#      #Pengambilan data dari Form Login.html (email, Password)
#     if not 'loggedin' in session:
#         if request.method == 'POST' and 'email' in request.json and 'password' in request.json:
#             email = request.json['email']
#             password = request.json['password']

#             cursor.execute('SELECT * FROM user where email = %s AND password = %s', (email, password))
#             user = cursor.fetchone()
           
#             # jika user ditemukan
#             if user:
#                 session['loggedin'] = True
#                 session['username'] = user['username']
#                 session['role'] = user['role']

#                 return jsonify({"msg":"login sukses"})
#             else:
#               return jsonify({"msg":"pw salah"})
#         else:
#           return jsonify({"msg":"blm masukin pw"})
#     else:
#       return jsonify({"msg":"blm masukin email"})

def login():
    msg = ''
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        # Check if account exists using MySQL
        cursor.execute('SELECT * FROM user WHERE username = %s AND password = %s', (username, password,))
        # Fetch one record and return result
        account = cursor.fetchone()
        # If account exists in accounts table in out database
        if account:
            # Create session data, we can access this data in other routes
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            # Redirect to home page
            return 'Logged in successfully!'
        else:
            # Account doesnt exist or username/password incorrect
            msg = 'Incorrect username/password!'
    # Show the login form with message (if any)
    return jsonify(msg)

@app.route('/logout', methods=['POST'])
def logout():
    # menghapus semua data session
  session.clear()
  # redirect user ke halaman login
  return jsonify({"msg":"dah logout"})

@app.route('/signup', methods=['POST'])
def signup():
  email = request.json["email"]
  password = request.json["password"]

  cursor.execute('SELECT * FROM user where email = %s AND password = %s', (email, password))
  user = cursor.fetchone()
  user_exists = user.query.filter_by(email=email).first() is not None

  if user_exists:
    abort(409)
  
  new_user=user(email=email, password=password, role='client')
  mydb.session.add(new_user)
  mydb.session.commit()

  return jsonify({
    "id": new_user.id,
    "email": new_user.email
  })

@app.route('/article', methods=['GET'])
def article():
  cursor.execute('SELECT * FROM article')
  articles = cursor.fetchall()

  return jsonify(articles)

@app.route('/cek', methods=['GET'])
def cek():
  cursor.execute('SELECT * FROM user')
  user = cursor.fetchall()
  return {
    "username" : user[0]
  }


if __name__ == 'main':
    app.run(host='0.0.0.0',port=5000)
