from functools import wraps
from bson import ObjectId
from pymongo import MongoClient
import jwt
import datetime
import hashlib
from flask import Flask, flash, render_template, jsonify, request, redirect, session, url_for
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os
from os.path import join, dirname
from dotenv import load_dotenv

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["UPLOAD_FOLDER"] = "./static/uploads"
app.secret_key = os.environ.get("SECRET_KEY")

TOKEN_KEY = os.environ.get("TOKEN_KEY")
SECRET_KEY = os.environ.get("SECRET_KEY")
MONGODB_CONNECTION_STRING = os.environ.get("MONGODB_CONNECTION_STRING")
DB_NAME =  os.environ.get("DB_NAME")

client = MongoClient(MONGODB_CONNECTION_STRING)
db = client[DB_NAME]

@app.route("/")
def home():
    token_receive = request.cookies.get("mytoken")
    packages = list(db.packages.find())
    try:
        if token_receive:
            payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
            user = db.users.find_one({"username": payload['id']})
        else:
            user = None
            
        for package in packages:
            package['_id'] = str(package['_id'])
            
        return render_template("index.html", packages=packages, user=user)

    except jwt.ExpiredSignatureError:
        for package in packages:
            package['_id'] = str(package['_id'])
            
        return render_template("index.html", packages=packages)

# user regis
@app.route("/user_signup", methods=["POST"])
def user_signup():
    username_receive = request.form["username"]
    nama_receive = request.form["nama_lengkap"]
    pw_receive = request.form["password"]
    pw_hash = hashlib.sha256(pw_receive.encode("utf-8")).hexdigest()

    user_exists = bool(db.users.find_one({"username": username_receive}))
    if user_exists:
        return jsonify(
            {
                "result": "error_uname",
                "msg": f"An account with username {username_receive} is already exists. Please Login!",
            }
        )
    else:
        doc = {
            "username": username_receive,
            "name": nama_receive,
            "password": pw_hash,
            "profile_pic_real": "profile_pics/profile_placeholder.png",
            "profile_info": "",
            "role": "user",
        }
        db.users.insert_one(doc)
        return jsonify({"result": "success"})


# user login
@app.route("/sign_in", methods=["POST"])
def sign_in():
    # Sign in
    username_receive = request.form["username_give"]
    password_receive = request.form["password_give"]
    pw_hash = hashlib.sha256(password_receive.encode("utf-8")).hexdigest()
    result = db.users.find_one(
        {
            "username": username_receive,
            "password": pw_hash,
        }
    )
    if result:
        payload = {
            "id": username_receive,
            # the token will be valid for 60 minutes
            "exp": datetime.utcnow() + timedelta(minutes=60),
            "role": result['role']
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

        response = jsonify(
            {
                "result": "success",
                "token": token,
                "role": result['role']  # Tambahkan peran pengguna ke respons
            }
        )
        response.set_cookie("mytoken", token)
        return response
    else:
        return jsonify(
            {
                "result": "fail",
                "msg": "Kami tidak dapat menemukan pengguna dengan kombinasi username/password tersebut.",
            }
        )


@app.route("/login")
def login():
    token_receive = request.cookies.get("mytoken")
    try:
        if token_receive:
            payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])

        return render_template("login.html")

    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return render_template("login.html")

    
@app.route("/logout")
def logout():
    response = redirect(url_for('login'))
    response.delete_cookie('mytoken')
    return response
    
@app.route("/sign_up/check_dup", methods=["POST"])
def check_dup():
    username_receive = request.form['username_give']
    exists = bool(db.users.find_one({"username": username_receive}))
    return jsonify({'result': 'success', 'exists': exists})

@app.route('/detai')
def detail():
    return render_template("detail.html")

@app.route('/pesan', methods=['GET'])
def pesan():
    package_id = request.args.get('package_id')
    package = db.packages.find_one({"_id": ObjectId(package_id)})
    if not package:
        return "Package not found", 404
    
    token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        user = db.users.find_one({"username": payload["id"]})
        if not user:
            return redirect(url_for("login"))
        
        return render_template("pesan.html", package=package, user=user)
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("login"))


@app.route('/submit_booking', methods=['POST'])
def submit_booking():
    token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        user = db.users.find_one({"username": payload["id"]})

        package_id = request.form["package_id"]
        additional_package = request.form["additional_package"]
        num_participants = int(request.form["num_participants"])
        total_cost = int(request.form["total_cost"])

        booking = {
            "user_id": user["_id"],
            "package_id": ObjectId(package_id),
            "additional_package": additional_package,
            "num_participants": num_participants,
            "total_cost": total_cost,
            "status": "pending",
            "created_at": datetime.utcnow()
        }
        
        result = db.bookings.insert_one(booking)
        booking_id = str(result.inserted_id)
        
        return jsonify({"result": "success", "booking_id": booking_id})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("login"))
    
@app.route('/cek_pesanan/<user_id>', methods=['GET'])
def cek_pesanan(user_id):
    token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        user_id = ObjectId(user_id)
        bookings = list(db.bookings.find({"user_id": user_id}))

        # Include package details in each booking
        for booking in bookings:
            package = db.packages.find_one({"_id": booking["package_id"]})
            booking["package"] = package
        
        return render_template("cekpesan.html", bookings=bookings)
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("login"))
    except Exception as e:
        return f"An error occurred: {str(e)}", 500


@app.route('/detail_pesan/<booking_id>', methods=['GET'])
def detail_pesan(booking_id):
    token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        booking_id = ObjectId(booking_id)
        booking = db.bookings.find_one({"_id": booking_id})
        user = db.packages.find_one({"_id": booking["user_id"]})
        package = db.packages.find_one({"_id": booking["package_id"]})
        
        return render_template("cekpesan.html", booking=booking, package=package, user=user)
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("login"))


@app.route('/upload_payment_proof', methods=['POST'])
def upload_payment_proof():
    token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        
        booking_id = request.form["booking_id"]
        payment_proof = request.files["payment_proof"]
        
        if payment_proof:
            filename = secure_filename(payment_proof.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            payment_proof.save(filepath)
            
            db.bookings.update_one(
                {"_id": ObjectId(booking_id)},
                {"$set": {"payment_proof": filepath, "status": "waiting_for_approval"}}
            )
            
            return jsonify({"result": "success"})
        else:
            return jsonify({"result": "fail", "msg": "No file uploaded."})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("login"))


@app.route('/admin_panel', methods=['GET', 'POST'])
def admin_panel():
    token_receive = request.cookies.get("mytoken")
    payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
    print(payload)
    unique_users = set()  # Initialize a set to keep track of unique users
    if payload["role"] != "admin":
        return redirect(url_for("login"))
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    total_cost_approved_bookings = 0  # Initialize total cost for approved bookings
    total_monthly_earnings = 0  # Initialize total monthly earnings
    
    bookings = list(db.bookings.find({}))
    
    for booking in bookings:
        if booking["status"] == "approved":
            total_cost_approved_bookings += booking["total_cost"]
        
        booking_date = booking["_id"].generation_time  # Assuming _id is an ObjectId
        if booking_date.month == current_month and booking_date.year == current_year:
            total_monthly_earnings += booking["total_cost"]
        
        # Add user to the set of unique users
        unique_users.add(booking["user_id"])

    user = db.users.find_one({"username": payload["id"]})
    
    return render_template("admin_panel.html", 
                           user=user, 
                           total_cost_approved_bookings=total_cost_approved_bookings, 
                           bookings=bookings, 
                           total_users=len(unique_users), 
                           total_monthly_earnings=total_monthly_earnings)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}


@app.route('/admin/wisata', methods=['GET', 'POST'])

def manage_wisata():
    packages = db.packages.find()
    return render_template('manage_wisata.html',packages=packages)

@app.route('/admin/add')
def add():
    packages = []  # Initialize packages list
    
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'photo' not in request.files:
            flash('No file part')
            return redirect(request.url)
        
        file = request.files['photo']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
            # Get form data
            package_name = request.form.get('package_name')
            price = request.form.get('price')
            facilities = request.form.get('facilities')
            
            # Save to MongoDB
            package = {
                "package_name": package_name,
                "price": price,
                "facilities": facilities,
                "photo": filename,
                "created_at": datetime.utcnow()
            }
            db.packages.insert_one(package)
            flash('Package successfully added')
    
    # Retrieve posted data from MongoDB
    packages = db.packages.find()
    return render_template('add.html', packages=packages)

@app.route('/admin/edit/<package_id>', methods=['GET', 'POST'])

def edit(package_id):
    package = db.packages.find_one({"_id": ObjectId(package_id)})

    if request.method == 'POST':
        package_name = request.form.get('package_name')
        price = request.form.get('price')
        facilities = request.form.get('facilities')

        # Handle photo upload
        if 'photo' in request.files:
            file = request.files['photo']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                photo = filename
            else:
                photo = package['photo']  # Keep old photo if no new photo uploaded
        else:
            photo = package['photo']

        # Update package in MongoDB
        db.packages.update_one(
            {"_id": ObjectId(package_id)},
            {"$set": {
                "package_name": package_name,
                "price": price,
                "facilities": facilities,
                "photo": photo,
                "updated_at": datetime.utcnow()
            }}
        )
        flash('Package successfully updated')
        return redirect(url_for('manage_wisata'))

    return render_template('edit_wisata.html', package=package)


@app.route('/admin/delete/<package_id>', methods=['POST'])

def delete(package_id):
    db.packages.delete_one({"_id": ObjectId(package_id)})
    flash('Package successfully deleted')
    return redirect(url_for('manage_wisata'))

@app.route('/admin/orders')
def view_orders():
    token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        bookings = list(db.bookings.find({}))
        
        # Include package details in each booking
        for booking in bookings:
            package = db.packages.find_one({"_id": booking["package_id"]})
            booking["package"] = package
            
            user = db.users.find_one({"_id": booking["user_id"]})
            if user:
                booking["username"] = user["username"]
            else:
                booking["username"] = "Unknown"
        
        return render_template("view_order.html", bookings=bookings)
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("login"))
    except Exception as e:
        return f"An error occurred: {str(e)}", 500

@app.route('/admin/orders/approve/<booking_id>')
def approve_order(booking_id):
    db.bookings.update_one({"_id": ObjectId(booking_id)}, {"$set": {"status": "approved"}})
    return redirect(url_for('view_orders'))

@app.route('/admin/orders/reject/<booking_id>')
def reject_order(booking_id):
    db.bookings.update_one({"_id": ObjectId(booking_id)}, {"$set": {"status": "rejected"}})
    return redirect(url_for('view_orders'))

@app.route("/user/<username>")
def user(username):
    # an endpoint for retrieving a user's profile information
    # and all of their posts
    token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        # if this is my own profile, True
        # if this is somebody else's profile, False
        status = username == payload["id"]  

        user_info = db.users.find_one({"username": payload["id"]})
        return render_template("user.html", user_info=user_info, status=status)
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))

@app.route('/admin/profile', methods=['GET', 'POST'])
def profile():
    token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        user = db.users.find_one({"username": payload['id']})
        
        if request.method == 'POST':
            name = request.form['name']
            profile_info = request.form['profile_info']
            
            # Handle profile picture upload
            if 'profile_pic' in request.files and request.files['profile_pic'].filename != '':
                file = request.files['profile_pic']
                profile_pic_filename = secure_filename(file.filename)
                profile_pic_path = os.path.join(app.config['UPLOAD_FOLDER'], profile_pic_filename)
                file.save(profile_pic_path)
                profile_pic_path = os.path.join('profile_pics', profile_pic_filename)
            else:
                profile_pic_path = user['profile_pic_real']
            
            # Update user data
            update_data = {
                "name": name,
                "profile_info": profile_info,
                "profile_pic_real": profile_pic_path
            }
            
            # Update password if provided
            if 'password' in request.form and request.form['password']:
                pw_receive = request.form['password']
                hashed_password = hashlib.sha256(pw_receive.encode("utf-8")).hexdigest()
                update_data['password'] = hashed_password
            
            db.users.update_one({"username": payload['id']}, {"$set": update_data})
            session['username'] = user['username']  # Set the username from updated user data
            flash('Profile successfully updated')
            return redirect(url_for('profile'))
        
        return render_template('profile.html', user=user)
    except jwt.ExpiredSignatureError:
        flash('Token has expired. Please log in again.')
        return redirect(url_for('login'))
    except jwt.InvalidTokenError:
        flash('Invalid token. Please log in again.')
        return redirect(url_for('login'))


if __name__ == "__main__":
    app.run("0.0.0.0", port=5000, debug=True)