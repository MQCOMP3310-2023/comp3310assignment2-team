from . import db

class Restaurant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)

    @property
    def serialize(self):
       """Return object data in easily serializeable format"""
       return {
           'name'         : self.name,
           'id'           : self.id,
       }
 
class MenuItem(db.Model):
    name = db.Column(db.String(80), nullable = False)
    id = db.Column(db.Integer, primary_key = True)
    description = db.Column(db.String(250))
    price = db.Column(db.String(8))
    course = db.Column(db.String(250))
    restaurant_id = db.Column(db.Integer,db.ForeignKey('restaurant.id'))
    restaurant = db.    relationship(Restaurant)

    @property
    def serialize(self):
       """Return object data in easily serializeable format"""
       return {
           'name'       : self.name,
           'description' : self.description,
           'id'         : self.id,
           'price'      : self.price,
           'course'     : self.course,
       }
    
class Comment(db.Model):
    title = db.Column(db.String(80), nullable = False)
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(250), nullable = False)
    name = db.Column(db.String(80))
    restaurantid = db.Column(db.Integer, db.ForeignKey('restaurant.id'))
    restaurant = db.relationship(Restaurant)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'title'      : self.title,
            'id'         : self.id,
            'description': self.description,
            'name'       : self.name,
        }

class User(db.Model):
    name = db.Column(db.String(50), nullable = False)
    email = db.Column(db.String(50), nullable = False)
    id = db.Column(db.Integer, primary_key = True)
    password = db.Column(db.String(50), nullable = False)
    totp = db.Column(db.String(32))
    totp_verified = db.Column(db.Boolean())

    @property
    def serialize(self):
        """Return object data in easily serializeable format, not including password for security"""
        return {
            'name'       : self.name,
            'email'      : self.email,
            'id'         : self.id,
        }

class UserToken(db.Model):
    id = db.Column(db.Integer, nullable = False)
    token = db.Column(db.String(50), nullable = False)
    tolu = db.Column(db.Integer, nullable = False)
    uid = db.Column(db.Integer, primary_key = True)
    trusted = db.Column(db.Boolean, default=False)

    @property
    def serialize(self):
        """Return object data in easily serializable format"""
        return {
            'id'         : self.id,
            'token'      : self.token,
            'tolu'       : self.tolu,
        }
