from urllib import response
import mysql.connector
from flask import Flask, make_response, render_template, request, redirect, url_for, session, send_file, abort, jsonify
# from flask_cors import CORS
import datetime

mydb = mysql.connector.connect(
  host="127.0.0.1",
  user="root",
  password="",
  database="leiptca_web"
)

# inisiasi variabel aplikasi
app = Flask(__name__)
# CORS(app)
cursor = mydb.cursor(dictionary=True,buffered=True)
app.secret_key="abcd"

@app.route('/current_user', methods=['GET'])
@app.route('/current_user/', methods=['GET'])
def current_user():
    if 'name' in session:
      return jsonify({
          "name":session['name'],
          "role":session['role'],
          "email":session['email'],
          "user_id":session['user_id']
        })
    else:
        return jsonify({'error': 'Not logged in'})

@app.route('/admin_list', methods=['GET'])
@app.route('/admin_list/', methods=['GET'])
def admin_list():
  if 'name' in session:
    if not session['role'] == "client":
      cursor.execute('SELECT * FROM user where role != "client"')
      admin = cursor.fetchall()
      return jsonify(admin)
    return jsonify({"msg":"Has no access"})
  return jsonify({"msg":"Has not login"})

@app.route('/login', methods=['POST'])
@app.route('/login/', methods=['POST'])
def login():
  if not 'loggedin' in session:
    if 'email' in request.json and 'password' in request.json:
      email = request.json['email']
      password = request.json['password']

      cursor.execute('SELECT * FROM user where email = %s AND password = %s', (email, password))
      user = cursor.fetchone()
      
      # jika user ditemukan
      if user:
          session['name'] = user['name']
          session['user_id'] = user['user_id']
          session['role'] = user['role']
          session['email'] = user['email']

          return redirect(url_for('current_user'))
      
      # jika user tidak ditemukan
      return jsonify({'error': 'Invalid email or password'})
    
    # jika parameter tidak lengkap
    return jsonify({'error': 'Invalid parameter'})
  
  # jika sudah login
  return redirect(url_for('current_user'))

@app.route('/signup', methods=['POST'])
@app.route('/signup/', methods=['POST'])
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
@app.route('/logout/', methods=['POST'])
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

@app.route('/del_article/<id>', methods=['POST'])
def del_article(id):
  if 'name' in session:
    if session['role'] == "superadmin" or session['role'] == "codev":
      cursor.execute('DELETE FROM comment WHERE article_id = %s',([id]))
      mydb.commit()
      cursor.execute('DELETE FROM article WHERE article_id = %s',([id]))
      mydb.commit()
      return jsonify({"msg":"article deleted"})
    else:
      return jsonify({"msg":"Has no access"})
  else:
    return jsonify({"msg":"Has not login"})

@app.route('/add_article', methods=['POST'])
def add_article():
  if 'name' in session:
    if session['role'] == "superadmin" or session['role'] == "codev":
      title = request.json["title"]
      author_name = request.json["author_name"]
      coauthor_name = request.json["coauthor_name"]
      article_text = request.json["article_text"]
      date= datetime.datetime.now().date()
      article_pic = request.json["article_pic"]
      
      cursor.execute('SELECT article_id FROM article ORDER BY article_id DESC')
      article = cursor.fetchone()
      if article:
        article_id = "ar"+str(int(article['article_id'][2:])+1)
      else:
        article_id = "ar1"
      
      cursor.execute('INSERT INTO article (article_id, author_name, coauthor_name, article_title, article_text, article_date, article_pic) VALUES (%s,%s,%s,%s,%s,%s,%s)', 
      (article_id, author_name, coauthor_name, title, article_text, date, article_pic))
      mydb.commit()

      return jsonify(article_id)
    else:
      return jsonify({"msg":"Has no access"})
  else:
    return jsonify({"msg":"Has not login"})

@app.route('/edit_article/<id>', methods=['POST'])
def edit_article(id):
  if 'name' in session:
    if session['role'] == "superadmin" or session['role'] == "codev":
      if 'title' in request.json:
        title = request.json["title"]
        cursor.execute('UPDATE article SET article_title = %s WHERE article_id = %s',(title,id))
        mydb.commit()

      if 'author_name' in request.json:
        author_name = request.json["author_name"]
        cursor.execute('UPDATE article SET author_name = %s WHERE article_id = %s',(author_name,id))
        mydb.commit()

      if 'coauthor_name' in request.json:
        coauthor_name = request.json["coauthor_name"]
        cursor.execute('UPDATE article SET coauthor_name = %s WHERE article_id = %s',(coauthor_name,id))
        mydb.commit()

      if 'article_text' in request.json:
        article_text = request.json["article_text"]
        cursor.execute('UPDATE article SET article_text = %s WHERE article_id = %s',(article_text,id))
        mydb.commit()
    else:
      return jsonify({"msg":"Has no access"})
  else:
    return jsonify({"msg":"Has not login"})

@app.route('/comment/<article_id>', methods=['GET','POST'])
def comment(article_id):
  if request.method =='GET':
    cursor.execute('SELECT * FROM comment WHERE article_id = "{}" ORDER BY comment_date DESC'.format(article_id))
    comments = cursor.fetchall()
    return jsonify(comments)
  
  elif request.method == 'POST':
    if 'name' in session :
      if session['role'] == "client":
        user_id = session['user_id']
        comment_text = request.json["comment_text"]
        date = datetime.datetime.now().date()
        cursor.execute('SELECT comment_id FROM comment ORDER BY comment_id DESC')
        comment = cursor.fetchone()
        if comment:
          comment_id = "com"+str(int(comment['comment_id'][3:])+1)
        else:
          comment_id = "com1"
        cursor.execute('INSERT INTO comment (comment_id, user_id, article_id, comment_text, comment_date) VALUES (%s,%s,%s,%s,%s)', (comment_id, user_id, article_id, comment_text, date))
        mydb.commit()
        return jsonify(comment_id)
      return jsonify({"msg":"Has no access"})
    return jsonify({"msg":"blm login"})
  return ('',204)

@app.route('/delete_comment/<comment_id>', methods=['POST'])
def delete_comment(comment_id):
  cursor.execute('SELECT user_id FROM comment WHERE comment_id = %s',([comment_id]))
  user=cursor.fetchone()

  if session['user_id'] == user['user_id'] or session['role'] != "client":
    cursor.execute('DELETE FROM comment WHERE comment_id = %s',([comment_id]))
    mydb.commit()
    return jsonify({"msg":"comment deleted"})
  else:
    return jsonify({"msg":"login first"})

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

@app.route('/add_dictionary', methods=['POST'])
@app.route('/add_dictionary/', methods=['POST'])
def add_dictionary():
  if 'name' in session:
    if session['role'] == "superadmin" or session['role'] == "codev":
      language = request.json["language"]
      word = request.json["word"]
      meaning = request.json["meaning"]

      # language = "english"
      if language == "english":
        cursor.execute('INSERT INTO dict_eng (word, meaning) VALUES (%s,%s)', (word, meaning))
        mydb.commit()
        return jsonify({"msg":"word added to english dictionary"})

      # language = "indonesia"
      elif language == "indonesia":
        cursor.execute('INSERT INTO dict_ind (word, meaning) VALUES (%s,%s)', (word, meaning))
        mydb.commit()
        return jsonify({"msg":"word added to indonesia dictionary"})

      # languange is not recognized
      return jsonify({"msg":"languange not found"})

    # unauthorized
    return jsonify({"msg":"Has no access"})
    
  # not login
  return jsonify({"msg":"Has not login"})

@app.route('/del_dictionary/<language>/<dict_id>', methods=['POST'])
def del_dictionary(language, dict_id):
  if 'name' in session:
    if session['role'] == "superadmin" or session['role'] == "codev":
      if language == "english":
        cursor.execute('DELETE FROM dict_eng WHERE dict_id = %s',([dict_id]))
        mydb.commit()
        return jsonify({"msg":"word deleted from english dictionary"})

      elif language == "indonesia":
        cursor.execute('DELETE FROM dict_ind WHERE dict_id = %s',([dict_id]))
        mydb.commit()
        return jsonify({"msg":"word deleted from indonesia dictionary"})

      return jsonify({"msg":"languange not found"})

    return jsonify({"msg":"Has no access"})
    
  return jsonify({"msg":"Has not login"})

@app.route('/edit_dictionary/<language>/<dict_id>', methods=['POST'])
def edit_dictionary(language, dict_id):
  if 'name' in session:
    if session['role'] == "superadmin" or session['role'] == "codev":
      if language == "english":
        word = request.json["word"]
        meaning = request.json["meaning"]
        cursor.execute('UPDATE dict_eng SET word = %s, meaning = %s WHERE dict_id = %s',(word,meaning,dict_id))
        mydb.commit()
        return jsonify({"msg":"word edited from english dictionary"})

      elif language == "indonesia":
        word = request.json["word"]
        meaning = request.json["meaning"]
        cursor.execute('UPDATE dict_ind SET word = %s, meaning = %s WHERE dict_id = %s',(word,meaning,dict_id))
        mydb.commit()
        return jsonify({"msg":"word edited from indonesia dictionary"})

      return jsonify({"msg":"languange not found"})

    return jsonify({"msg":"Has no access"})
    
  return jsonify({"msg":"Has not login"})

@app.route('/user/<id>', methods=['GET'])
def user(id):
  if 'role' in session:
    if session['role'] == "superadmin":
      if not id=="all":
        cursor.execute('SELECT * FROM user where user_id = %s',([id]))
        user = cursor.fetchall()
        return jsonify(user)
      else:
        cursor.execute('SELECT * FROM user ORDER BY name ASC')
        users = cursor.fetchall()
        return jsonify(users)
    return jsonify({"msg":"has no access"})
  return jsonify({"msg":"has not logged in"})

@app.route('/del_user/<id>', methods=['POST'])
def del_user(id):
  if 'role' in session:
    if session['role'] == "superadmin":
      cursor.execute('SELECT * FROM user where user_id = %s',([id]))
      user=cursor.fetchone()
      if user :
        cursor.execute('DELETE FROM user where user_id = %s',([id]))
        mydb.commit()
        return jsonify({"msg":"user terhapus"})
      else:
        return jsonify({"msg":"user tidak ditemukan"})
    return jsonify({"msg":"has no access"})
  return jsonify({"msg":"has not logged in"})

@app.route('/edit_user/<id>', methods=['POST'])
def edit_user(id):
  if 'role' in session:
    if session['role'] == "superadmin":
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
      return jsonify({"msg":"user tidak ditemukan"})
    return jsonify({"msg":"has no access"})
  return jsonify({"msg":"has not logged in"})

@app.route('/add_admin', methods=['POST'])
def add_admin():
  if 'role' in session:
    if session['role'] == "superadmin":
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
    return jsonify({"msg":"has no access"})
  return jsonify({"msg":"has not logged in"})

@app.route('/roles', methods=['GET'])
@app.route('/roles/', methods=['GET'])
def roles():
  cursor.execute('SELECT * FROM roles')
  roles = cursor.fetchall()
  return jsonify(roles)

@app.route('/orders/<id>', methods=['GET'])
def orders(id):
  if 'role' in session:
    if not id=="all":
      cursor.execute('SELECT * FROM ordered where order_id = %s',([id]))
      order = cursor.fetchone()
      if session['user_id'] == order['user_id'] or session['role'] == "superadmin" or session['role']=="cpr" or session['role']=="codev":
        return jsonify(order)
      else:
        return jsonify({"msg":"has no access"})
    elif id=="all":
      if session['role'] != "client":
        cursor.execute('SELECT * FROM ordered ORDER BY order_date DESC')
        orders = cursor.fetchall()
        return jsonify(orders)
      else:
        return jsonify({"msg":"has no access"})

@app.route('/progress/<id>', methods=['GET'])
def progress(id):
  cursor.execute('SELECT * FROM progress WHERE order_id = %s ORDER BY progress_num ASC',([id]))
  progress = cursor.fetchall()
  return jsonify(progress)

@app.route('/del_progress/<id>', methods=['POST'])
def del_progress(id):
  if 'role' in session:
    cursor.execute('DELETE FROM progress WHERE order_id = %s',([id]))
    return jsonify({"msg":"user terhapus"})
  return jsonify({"msg":"has not logged in"})

@app.route('/add_progress/<id>', methods=['POST'])
def add_progress(id):
  if 'title' in request.json and 'description' in request.json and 'state' in request.json:
    title = request.json["title"]
    description = request.json["description"]
    state = request.json["state"]
    doc = request.json["doc"]

    cursor.execute('INSERT INTO progress (order_id, progress_doc, state, progress_desc) VALUES (%s,%s,%s,%s)', (id,doc, state, description ))
  else:
    return jsonify({"msg":"invalid parameters"})
  return jsonify({"msg":"user terhapus"})

@app.route('/services/<service_type>', methods=['GET'])
def services_list(service_type):
  if service_type == "legal":
    cursor.execute('SELECT * FROM legal_list ORDER BY type ASC')
  elif service_type == "translate":
    cursor.execute('SELECT * FROM translate_list')
  elif service_type == "training":
    cursor.execute('SELECT * FROM training_list ORDER BY date DESC')
  services = cursor.fetchall()
  return jsonify(services)

@app.route('/add_service/<service_type>', methods=['POST'])
def add_service(service_type):
  if service_type == "legal":
    if request.method == 'POST' and 'type' in request.json and 'cost' in request.json and 'matter' in request.json:
      type = request.json["type"]
      cost = request.json["cost"]
      matter = request.json["matter"]
      cursor.execute('INSERT INTO legal_list (type, matter, cost) VALUES (%s,%s,%s)', (type, matter, cost))
      mydb.commit()
      cursor.execute('SELECT * FROM legal_list where type = %s',([type]))
      new_service = cursor.fetchone()
      return jsonify(new_service)
  elif service_type == "translate":
    if request.method == 'POST' and 'trans_type' in request.json and 'cost' in request.json and 'lang_from' in request.json and 'lang_to' in request.json:
      trans_type = request.json["trans_type"]
      cost = request.json["cost"]
      lang_to = request.json["lang_to"]
      lang_from = request.json["lang_from"]
      cursor.execute('INSERT INTO translate_list (lang_from, lang_to, trans_type, cost) VALUES (%s,%s,%s,%s)', (lang_from, lang_to, trans_type, cost))
      mydb.commit()
      cursor.execute('SELECT * FROM translate_list where type = %s',([type]))
      new_service = cursor.fetchone()
      return jsonify(new_service)
  elif service_type == "training":
    if request.method == 'POST' and 'training_class' in request.json and 'date_time' in request.json and 'quota' in request.json:
      training_class = request.json["training_class"]
      date_time = request.json["date_time"]
      quota = request.json["quota"]
      cost = request.json["cost"]
      cursor.execute('INSERT INTO training_list (training_class, date_time, quota, cost) VALUES (%s,%s,%s,%s)', (training_class, date_time, quota,cost))
      mydb.commit()
      cursor.execute('SELECT * FROM training_list where training_class = %s',([training_class]))
      new_service = cursor.fetchone()
      return jsonify(new_service)
  return jsonify({"msg":"salah method/gada form nama/email/pq"})

@app.route('/edit_service/<service_type>/<service_id>', methods=['POST'])
def edit_service(service_type, service_id):
  if service_type == "legal":
    if request.method == 'POST' and 'type' in request.json and 'cost' in request.json and 'matter' in request.json:
      type = request.json["type"]
      cost = request.json["cost"]
      matter = request.json["matter"]
      cursor.execute('UPDATE legal_list SET type=%s, matter = %s, cost = %s WHERE service_id = %s', (type, matter, cost, service_id))
      mydb.commit()
      cursor.execute('SELECT * FROM legal_list where type = %s',([type]))
      new_service = cursor.fetchone()
      return jsonify(new_service)

  elif service_type == "translate":
    if request.method == 'POST' and 'trans_type' in request.json and 'cost' in request.json and 'lang_from' in request.json and 'lang_to' in request.json:
      trans_type = request.json["trans_type"]
      cost = request.json["cost"]
      lang_to = request.json["lang_to"]
      lang_from = request.json["lang_from"]
      cursor.execute('UPDATE translate_list lang_from = %s, lang_to = %s, trans_type = %s, cost = %s WHERE service_id = %s', (lang_from, lang_to, trans_type, cost, service_id))
      mydb.commit()
      cursor.execute('SELECT * FROM translate_list where type = %s',([type]))
      new_service = cursor.fetchone()
      return jsonify(new_service)

  elif service_type == "training":
    if request.method == 'POST' and 'training_class' in request.json and 'date_time' in request.json and 'quota' in request.json:
      training_class = request.json["training_class"]
      date_time = request.json["date_time"]
      quota = request.json["quota"]
      cost = request.json["cost"]
      cursor.execute('INSERT INTO training_list (training_class, date_time, quota, cost) VALUES (%s,%s,%s,%s)', (training_class, date_time, quota, cost))
      mydb.commit()
      cursor.execute('SELECT * FROM training_list where training_class = %s',([training_class]))
      new_service = cursor.fetchone()
      return jsonify(new_service)
  return jsonify({"msg":"salah method/gada form nama/email/pq"})

@app.route('/legal_order', methods=['POST'])
def legal_order():
  if 'role' in session:
    if 'legal_service_id' in request.json:
      legal_service_id = request.json["legal_service_id"]
      delivery = request.json["delivery"]
      date = datetime.datetime.now().date()
      user_id = session['user_id']
      voucher = request.json["voucher"]
        
      cursor.execute('SELECT order_id FROM ordered WHERE order_id LIKE "LE%" ORDER BY order_id DESC')
      order = cursor.fetchone()
      if order:
        order_id = "LE0000"+str(int(order['order_id'][2:])+1)
      else:
        order_id = "LE0000"+"1"
      
      cursor.execute('SELECT cost FROM legal_list WHERE service_id = %s',([legal_service_id]))
      cost = cursor.fetchone()
      
      #input orderan ke ordered
      cursor.execute('INSERT INTO ordered (order_id, order_service_id, user_id, order_date, order_cost, order_desc) VALUES (%s,%s,%s,%s,%s, "legal")', (order_id, legal_service_id, user_id, date, cost['cost']))
      mydb.commit()

      #input delivery dan voucher type to legal_order
      cursor.execute('INSERT INTO legal_order (order_id, delivery, voucher) VALUES (%s,%s,%s)', (order_id,delivery,voucher))

      #input voucher kalau ada
      # if 'voucher' in request.json:
      #   voucher = request.json["voucher"]
      #   cursor.execute('UPDATE legal_order SET voucher = %s WHERE order_id = %s', (order_id,voucher))
      #   mydb.commit()

      return jsonify(order_id)
    return jsonify({"msg":"salah method/gada form nama/email/pq"})
  return jsonify({"msg":"not logged in"})

@app.route('/translate_order', methods=['POST'])
def translate_order():
  if 'role' in session:
    if session['role']=="client":
      # if 'translate_service_id' in request.json:
      if 'lang_from' in request.json and 'lang_to' in request.json and 'num_of_pages' in request.json:
        lang_from = request.json["lang_from"]
        lang_to = request.json["lang_to"]
        # translate_service_id = request.json["translate_service_id"]
        num_of_pages = request.json["num_of_pages"]
        order_type = request.json["order_type"]
        delivery = request.json["delivery"]
        date = datetime.datetime.now().date()
        user_id = session['user_id']

        # print(lang_to)

        #menentukan service id
        cursor.execute('SELECT service_id FROM translate_list WHERE lang_from = %s AND lang_to = %s',(lang_from, lang_to))
        translate_service_id = cursor.fetchone() #dict

        # #menentukan order id
        cursor.execute('SELECT order_id FROM ordered WHERE order_id LIKE "TR%" ORDER BY order_id DESC')
        order = cursor.fetchone()
        if order:
          order_num = str(int(order['order_id'][2:])+1)
          order_num = ((4-len(order_num))*"0")+order_num
          order_id = "TR"+order_num
        else:
          order_id = "TR0000"+"1"

        print(translate_service_id['service_id'])

        # #ambil atribut cost
        cursor.execute('SELECT * FROM translate_list WHERE service_id = "%s"',(translate_service_id['service_id']))
        cost = cursor.fetchone()
        # if order_type == "express":
        #   cost = cost*2
        
        print(cost['regular_cost'])

        # #simpan ke tabel ordered
        # cursor.execute('INSERT INTO ordered (order_id, order_service_id, user_id, order_date, order_cost, order_desc) VALUES (%s,%s,%s,%s,%s, "translate")', (order_id, translate_service_id, user_id, date, cost['cost']))
        # mydb.commit()

        # #simpan delivery ke translate order
        # cursor.execute('INSERT INTO translate_order (order_id, delivery, num_of_pages) VALUES (%s,%s,%s)', (order_id,delivery,num_of_pages))
        # mydb.commit()

        # return jsonify(order_id)
      return jsonify({"msg":"salah method/gada form nama/email/pq"})
    return jsonify({"msg":"Has no access"})
  return jsonify({"msg":"not logged in"})

@app.route('/training_order', methods=['POST'])
def add_training_order():
  if 'role' in session:
    if session['role'] == "client":
      if 'training_service_id' in request.json:
        #get quota
        training_service_id = request.json["training_service_id"]
        cursor.execute('SELECT quota from training_list WHERE service_id = %s',([training_service_id]))
        quota = cursor.fetchone()

        #track jumlah order
        cursor.execute('SELECT COUNT(order_id) FROM ordered WHERE order_service_id = %s;',([training_service_id]))
        totalApplicant = cursor.fetchone()
        print(totalApplicant)

        if totalApplicant['COUNT(order_id)'] < quota['quota']:
          date = datetime.datetime.now().date()
          user_id = session['user_id']
          #menentukan order id
          cursor.execute('SELECT order_id FROM ordered WHERE order_id LIKE "TN%" ORDER BY order_id DESC')
          order = cursor.fetchone()
          if order:
            order_num = str(int(order['order_id'][2:])+1)
            order_num = ((4-len(order_num))*"0")+order_num
            order_id = "TN"+order_num
          else:
            order_id = "TN0001"
        
          #cari biaya
          cursor.execute('SELECT cost FROM training_list WHERE service_id = %s',([training_service_id]))
          cost = cursor.fetchone()

          #input order
          cursor.execute('INSERT INTO ordered (order_id, order_service_id, user_id, order_date, order_cost, order_desc) VALUES (%s,%s,%s,%s,%s, "training")', (order_id, training_service_id, user_id, date, cost['cost']))
          mydb.commit()

          return jsonify(order_id)
        else:
          return jsonify({"msg":"quota penuh"})
      return jsonify({"msg":"salah method/gada form nama/email/pq"})
    return jsonify({"msg":"Has no access"})
  return jsonify({"msg":"not logged in"})

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=8080, debug=True)
