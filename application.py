import os,json
# key: XII2wcgk2yS3EwYILZav3Q
# secret: s26z27NPJ9IXS2240jZTj3lkX0VHK2DwZKRwyfXqc
from flask import Flask, session,render_template,session,request,flash,redirect,jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import login_required
import requests
app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

@app.route("/")
@login_required
def index():
  """this will show the search box"""
  return render_template("index.html")

@app.route("/login",methods=["POST","GET"])
def login():
  """user login"""
  #forget if any 
  session.clear()

  username=request.form.get("username")
  password=request.form.get("password")

  if request.method=="POST":

    if not request.form.get("username"):
      return render_template("error.html",message="must provide username")

    elif not request.form.get("password"):
      return render_template("error.html",message="must provide passord")

    userdata=db.execute("SELECT * FROM users WHERE username=:username",{"username":username})

    userrow=userdata.fetchone()

    if userrow==None or not check_password_hash(userrow[2],password):
      return render_template("error.html",message="invalid username/password")
    
    session["user_id"]=userrow[0]
    session["user_name"]=userrow[1]

    return redirect("/")
  
  else:
    return render_template("login.html")

@app.route("/logout")
def logout():

  session.clear()

  return redirect("/")


@app.route("/register",methods=["POST","GET"])
def register():
  session.clear()
  username=request.form.get("username")
  password=request.form.get("password")
  passconfirm=request.form.get("confirmation")

  if request.method=="POST":

    if not request.form.get("username"):
      return render_template("error.html",message="must provide username")

    userexist=db.execute("SELECT * FROM users WHERE username=:username",{"username":username}).fetchone()

    if userexist:
      return render_template("error.html",message="Username exist already please choose others")

    elif not password:
      return render_template("error.html",message="please provide password")
    elif not passconfirm:
      return render_template("error.html",message="please provide confirm password")
    elif not password==passconfirm:
      return render_template("error.html",message="password didn`t match")

    hashedpass=generate_password_hash(password,method='pbkdf2:sha256', salt_length=8)

    db.execute("INSERT INTO users (username,password) VALUES (:username,:password)",{"username":username,"password":hashedpass})

    db.commit()

    flash('Account created','info')

    return redirect("/login")

  else:
    return render_template("register.html")

@app.route("/search",methods=["GET"])
@login_required
def search():
  query=request.args.get("book")

  if not query:
    return render_template("error.html",message="please provide book")

  
  seachquery="%"+query+"%"
  seachquery=seachquery.title()

  bookrow=db.execute("SELECT * FROM books WHERE \
                      isbn LIKE :seachquery OR \
                      title LIKE :seachquery OR \
                      author LIKE :seachquery LIMIT 14",
                      {"seachquery":seachquery})
                    
  if bookrow.rowcount==0:
    return render_template("error.html",message="we can`t find books with that description.")

  books=bookrow.fetchall()

  return render_template("results.html",books=books)

@app.route("/book/<isbn>",methods=["GET","POST"])
@login_required
def book(isbn):
  if request.method=="POST":
    currentuser=session["user_id"]

    rating=request.form.get("rating")
    comment=request.form.get("comment")

    row=db.execute("SELECT id FROM books WHERE isbn=:isbn",{"isbn":isbn})
    bookid=row.fetchone()
    bookid=bookid[0]

    row1=db.execute("SELECT * FROM reviews WHERE user_id=:user_id AND book_id=:book_id ",{"user_id": currentuser,"book_id":bookid})

    if row1.rowcount==1:
      flash('You have already submitted a review for this book','warning')
      return redirect("/book/"+isbn)

    rating=int(rating)

    db.execute("INSERT INTO reviews (user_id,book_id,comment,rating) VALUES (:user_id,:book_id,:comment,:rating)",{"user_id":currentuser,"book_id":bookid,"comment":comment,"rating":rating})

    db.commit()

    flash('Review submitted!','info')

    return redirect("/book/"+isbn)

  else:
    row=db.execute("SELECT * FROM books WHERE isbn=:isbn",{"isbn":isbn})
    bookinfo=row.fetchall()

    key=os.getenv("GOODREADS_KEY")

    query=requests.get("https://www.goodreads.com/book/review_counts.json",params={"key":key,"isbns":isbn})
    response=query.json()
    response=response['books'][0]

    bookinfo.append(response)

    row=db.execute("SELECT id FROM books WHERE isbn=:isbn",{"isbn":isbn})
    book=row.fetchone()
    book=book[0]

    res=db.execute("SELECT users.username, comment, rating FROM users INNER JOIN reviews ON users.user_id = reviews.user_id WHERE book_id = :book ",{"book": book})
    reviews=res.fetchall()

    return render_template("book.html",bookInfo=bookinfo,reviews=reviews)




@app.route("/api/<isbn>", methods=['GET'])
@login_required
def api_call(isbn):

    

    row = db.execute("SELECT title, author, year, isbn, \
                    COUNT(reviews.id) as review_count, \
                    AVG(reviews.rating) as average_score \
                    FROM books \
                    INNER JOIN reviews \
                    ON books.id = reviews.book_id \
                    WHERE isbn = :isbn \
                    GROUP BY title, author, year, isbn",
                    {"isbn": isbn})

    
    if row.rowcount != 1:
        return jsonify({"Error": "Invalid book ISBN"}), 422

     
    tmp = row.fetchone()

    # Convert to dict
    result = dict(tmp.items())

    
    result['average_score'] = float('%.2f'%(result['average_score']))

    return jsonify(result)