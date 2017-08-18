# here we import the sqlalchemy class from the package
from flask.ext.sqlalchemy import SQLAlchemy
# import password hash algortihms from werkzeug
from werkzeug import generate_password_hash, check_password_hash

# create an instance of the alchemy class
db = SQLAlchemy()

# here we create a python class to model the users attributes
class User(db.Model):
  __tablename__ = 'users'
  uid = db.Column(db.Integer, primary_key = True)
  firstname = db.Column(db.String(100))
  lastname = db.Column(db.String(100))
  email = db.Column(db.String(120), unique=True)
  pwdhash = db.Column(db.String(54))

# create a constructor to set each of these attributes
  def __init__(self, firstname, lastname, email, password):
    # .title() saves the name with frst letter capitalised !
    self.firstname = firstname.title()
    self.lastname = lastname.title()
    # email saved in lover case
    self.email = email.lower()
    self.set_password(password)

# passwords are encryptes right away using the set_password function
  def set_password(self, password):
    # uses generate_password_hash function from library to encrypt
    self.pwdhash = generate_password_hash(password)

  def check_password(self, password):
    return check_password_hash(self.pwdhash, password)
