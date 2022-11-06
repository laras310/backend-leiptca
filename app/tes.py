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
    if request.method == 'POST' and 'email' in request.json and 'password' in request.json:
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

@app.route('/signup', methods=['POST'])
def signup():
  if request.method == 'POST' and 'name' in request.json and 'email' in request.json and 'password' in request.json:
    name = request.json["name"]
    email = request.json["email"]
    password = request.json["password"]

    cursor.execute('SELECT name FROM user where email = %s',([email]))
    user = cursor.fetchone()
  
    if user:
      return jsonify({"msg":"usernya udah ada"})
    
    else:
      cursor.execute('INSERT INTO user (email, name, password, role) VALUES (%s,%s,%s,%s)', (email, name, password, "client"))
      mydb.commit()
      cursor.execute('SELECT * FROM user where email = %s',([email]))
      new_user=cursor.fetchone()
      return jsonify(new_user)
  return jsonify({"msg":"salah method/gada form nama/email/pq"})

@app.route('/logout', methods=['POST'])
def logout():
    # menghapus semua data session
  session.clear()
  # redirect user ke halaman login
  return jsonify({"msg":"dah logout"})

@app.route('/article/<by>/<val>', methods=['GET'])
def article(by, val):
  if by == "id":
    cursor.execute('SELECT * FROM article where article_id = %s',([val]))
    article = cursor.fetchone()
    return jsonify(article)
  elif by == "all":
    cursor.execute('SELECT * FROM article ORDER BY article_date DESC')
    articles = cursor.fetchall()
    return jsonify(articles)
  else:
    return jsonify({"msg":"tidak cocok"})

@app.route('/comment/<article_id>', methods=['GET'])
def comment(article_id):
  cursor.execute('SELECT * FROM comment WHERE article_id = "{}" ORDER BY comment_date DESC'.format(article_id))
  comments = cursor.fetchall()
  return jsonify(comments)

@app.route('/dictionary/<language>/<alphabet>', methods=['GET'])
def dictionary(language, alphabet):
  if language == "english":
    cursor.execute('SELECT * FROM dict_eng where word LIKE "{}%"'.format(alphabet))
  
  elif language == "indonesia":
    cursor.execute('SELECT * FROM dict_ind where word LIKE "{}%"'.format(alphabet))
  
  else :
    return jsonify({"msg":"gada bahasanya"})
  data = cursor.fetchall()
  data2= jsonify(data)
  data2.headers.add('Access-Control-Allow-Origin', '*')
  return data2

@app.route('/user/<id>', methods=['GET'])
def user(id):
  if not id=="all":
    cursor.execute('SELECT * FROM user where user_id = %s',([id]))
    user = cursor.fetchone()
    return jsonify(user)
  else:
    cursor.execute('SELECT * FROM user ORDER BY name ASC')
    users = cursor.fetchall()
    return jsonify(users)

@app.route('/del_user/<id>', methods=['POST'])
def del_user(id):
    cursor.execute('SELECT * FROM user where user_id = %s',([id]))
    user=cursor.fetchone()
    if user :
      cursor.execute('DELETE FROM user where user_id = %s',([id]))
      mydb.commit()
      return jsonify({"msg":"user terhapus"})
    else:
      return jsonify({"msg":"user tidak ditemukan"})

@app.route('/edit_user/<id>', methods=['POST'])
def edit_user(id):
  msg=""
  cursor.execute('SELECT * FROM user where user_id = %s',([id]))
  user=cursor.fetchone()
  if user :
    if 'name' in request.json:
      name = request.json["name"]
      cursor.execute('UPDATE user SET name = %s WHERE user_id = %s',(name,id))
      mydb.commit()

    if 'email' in request.json:
      email = request.json["email"]
      cursor.execute('UPDATE user SET email = %s WHERE user_id = %s',(email,id))
      mydb.commit()

    if 'password' in request.json:
      password = request.json["password"]
      cursor.execute('UPDATE user SET password = %s WHERE user_id = %s',(password,id))
      mydb.commit()

    if 'role' in request.json:
      role = request.json["role"]
      cursor.execute('UPDATE user SET role = %s WHERE user_id = %s',(role,id))
      mydb.commit()
    
    if 'phone_number' in request.json:
      cursor.execute('SELECT * FROM additional_info where user_id = %s',([id]))
      phone=cursor.fetchone()
      if phone:
        phone_number = request.json["phone_number"]
        cursor.execute('UPDATE additional_info SET phone_number = %s WHERE user_id = %s',(phone_number,id))
        mydb.commit()
        msg="nomor diupdate"
      else:
        msg="nomor tidak ada"
    
    return jsonify(msg)
      
  # else:
  return jsonify({"msg":"user tidak ditemukan"})

@app.route('/add_admin', methods=['POST'])
def add_admin():
  if request.method == 'POST' and 'name' in request.json and 'email' in request.json and 'password' in request.json and 'role' in request.json and 'phone_number' in request.json:
    name = request.json["name"]
    email = request.json["email"]
    password = request.json["password"]
    role = request.json["role"]
    phone_number = request.json["phone_number"]

    cursor.execute('SELECT name FROM user where email = %s',([email]))
    user = cursor.fetchone()
  
    if user:
      return jsonify({"msg":"usernya udah ada"})
    
    else:
      cursor.execute('INSERT INTO user (email, name, password, role) VALUES (%s,%s,%s,%s)', (email, name, password, role))
      mydb.commit()
      cursor.execute('SELECT user_id FROM user where email = %s',([email]))
      user_id = cursor.fetchone()
      print(user_id)
      cursor.execute('INSERT INTO additional_info (phone_number, user_id) VALUES (%s,%s)', (phone_number,user_id[0]))
      mydb.commit()
      cursor.execute('SELECT * FROM user where email = %s',([email]))
      new_user = cursor.fetchone()
      return jsonify(new_user)
  return jsonify({"msg":"salah method/gada form nama/email/pq"})

if __name__ == 'main':
    app.run(host='0.0.0.0',port=5000)
