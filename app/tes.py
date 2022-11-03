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
def login():
  if not 'loggedin' in session:
    # if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
      email = request.json['email']
      password = request.json['password']

      cursor.execute('SELECT * FROM user where email = %s AND password = %s', (email, password))
      user = cursor.fetchone()
      
      # jika user ditemukan
      if user:
          session['loggedin'] = True
          session['username'] = user['username']
          session['role'] = user['role']

          return jsonify({"msg":"login sukses"})
      else:
        return jsonify({"msg":"pw salah"})
    # return jsonify({"msg":"pw salah"})
  return jsonify({"msg":"render template login"})

@app.route('/logout', methods=['POST'])
def logout():
    # menghapus semua data session
  session.clear()
  # redirect user ke halaman login
  return jsonify({"msg":"dah logout"})

@app.route('/signup', methods=['POST'])
def signup():
  name = request.json["name"]
  email = request.json["email"]
  password = request.json["password"]

  cursor.execute('SELECT * FROM user where email = %s AND password = %s', (email, password))
  user = cursor.fetchone()
  user_exists = user.query.filter_by(email=email).first() is not None

  if user_exists:
    abort(409)
  
  new_user=user(name = name, email=email, password=password, role='client')
  mydb.session.add(new_user)
  mydb.session.commit()

  return jsonify({
    "id": new_user.id,
    "email": new_user.email,
    "name":new_user.name
  })

@app.route('/article', methods=['GET'])
def article():
  cursor.execute('SELECT * FROM article')
  articles = cursor.fetchall()

  return jsonify(articles)

@app.route('/dictionary/<language>/<alphabet>', methods=['GET'])
def dictionary(language, alphabet):
  if language == "english":
    cursor.execute('SELECT * FROM dict_eng where word LIKE "{}%"'.format(alphabet))
  
  elif language == "indonesia":
    cursor.execute('SELECT * FROM dict_ind where word LIKE "{}%"'.format(alphabet))
  
  else :
    return jsonify({"msg":"gada bahasanya"})
  data = cursor.fetchall()
  return jsonify(data)


if __name__ == 'main':
    app.run(host='0.0.0.0',port=5000)
