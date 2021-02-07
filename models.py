from flask_sqlalchemy import SQLAlchemy
db=SQLAlchemy()


class Books(db.Model):
    __tablename__="books"
    id=db.Column(db.Integer,primary_key=True)
    isbn=db.Column(db.String,nullable=False)
    title=db.Column(db.String,nullable=False)
    author=db.Column(db.String,nullable=False)
    year=db.Column(db.String,nullable=False)
class users(db.Model):
    __tablename__="users"
    user_id=db.Column(db.Integer,primary_key=True)
    usernname=db.Column(db.String,unique=True,nullable=False)
    password=db.Column(db.String,nullable=False)

class Reviews(db.Model):
    __tablename__="reviews"
    id=db.Column(db.Integer,primary_key=True)
    user_id=db.Column(db.Integer,nullable=False)
    book_id=db.Column(db.Integer,nullable=False)
    comment=db.Column(db.String,nullable=False)
    rating=db.Column(db.Integer,nullable=False)


    

