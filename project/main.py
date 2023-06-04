import io
import sys
import tempfile
import typing

import pyotp
import pyqrcode
from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from .models import Restaurant, MenuItem, Comment, User, UserToken
from sqlalchemy import asc
from werkzeug import security
from datetime import datetime
import calendar
import secrets
import logging
from . import db

main = Blueprint('main', __name__)


#
# HELPER METHODS
#

def getTime():
    return calendar.timegm(datetime.utcnow().utctimetuple())


def create_session(email, password):
    user = db.session.query(User).filter_by(email=email).one_or_none()

    if user is None:
        return None

    # Check password
    if security.check_password_hash(user.password, password):

        new_token = secrets.token_hex(16)

        # Check for token collision
        if db.session.query(UserToken).filter_by(token=new_token).one_or_none() is not None:
            logging.warning("Generated duplicate token.")
            return None

        # Check is 2fa is required
        # If yes, an "insecure" session is created, and user is redirected to next steps
        token = None
        if user.totp is not None and user.totp_verified is True:
            token = UserToken(id=user.id, token=new_token, tolu=getTime(), trusted=False)
        else:
            token = UserToken(id=user.id, token=new_token, tolu=getTime(), trusted=True)

        session['token'] = token.token
        db.session.add(token)
        db.session.commit()

        return user, token

    return None


def get_session_token(token: str) -> UserToken:
    return db.session.query(UserToken).filter_by(token=token).one_or_none()


def upgrade_session(user: User, token: UserToken, code):
    if pyotp.TOTP(user.totp).verify(code):
        token.trusted = True
        db.session.commit()

    return user, token


def destroy_session():
    token = session.get("token")

    if token is None:
        return

    db.session.delete(db.session.query(UserToken).filter_by(token=token).one_or_none())
    db.session.commit()

    session.pop('token', None)


def getUser(insecure=False):
    if 'token' not in session:
        return None

    token = session.get('token')
    token_object = db.session.query(UserToken).filter_by(token=token).one_or_none()

    if token_object is None:
        return None

    if token_object.tolu < getTime() - 2592000:  # One month token expiry period
        db.session.delete(token)
        db.session.commit()

        session.pop('token', None)

        return None

    if insecure is False and not token_object.trusted:
        return None

    token_object.tolu = getTime()
    db.session.commit()

    user = db.session.query(User).filter_by(id=token_object.id).one_or_none()
    return user


#
# VIEW METHODS
#


# Show all restaurants
@main.route('/')
@main.route('/restaurant/')
def showRestaurants():
  restaurants = db.session.query(Restaurant).order_by(asc(Restaurant.name))
  return render_template('restaurants.html', restaurants = restaurants, user = getUser())

#Create a new restaurant
@main.route('/restaurant/new/', methods=['GET','POST'])
def newRestaurant():
  user = getUser()
  if request.method == 'POST':
      if user.restaurant == None:
        newRestaurant = Restaurant(name = request.form['name'])
        db.session.add(newRestaurant)
        db.session.commit()
        user.restaurant = newRestaurant.id
        if user.permission == 0:
          user.permission = 1
        db.session.commit() # commit twice because the first one generates a restaurant ID
        flash('New Restaurant %s Successfully Created' % newRestaurant.name)
      else:
        flash('User already belongs to a restaurant')
      return redirect(url_for('main.showRestaurants'))
  else:
      return render_template('newRestaurant.html', user = user)

#Edit a restaurant
@main.route('/restaurant/<int:restaurant_id>/edit/', methods = ['GET', 'POST'])
def editRestaurant(restaurant_id):
  user = getUser()
  editedRestaurant = db.session.query(Restaurant).filter_by(id = restaurant_id).one()
  if request.method == 'POST':
      if user != None and user.restaurant == restaurant_id:
        if request.form['name']:
          editedRestaurant.name = request.form['name']
          db.session.commit()
          flash('Restaurant Successfully Edited %s' % editedRestaurant.name)
      else:
        flash('Failed to edit restaurant')
      return redirect(url_for('main.showRestaurants'))
  else:
    return render_template('editRestaurant.html', restaurant = editedRestaurant, user = user)


#Delete a restaurant
@main.route('/restaurant/<int:restaurant_id>/delete/', methods = ['GET','POST'])
def deleteRestaurant(restaurant_id):
  user = getUser()
  restaurantToDelete = db.session.query(Restaurant).filter_by(id = restaurant_id).one()
  if request.method == 'POST':
    if user != None and user.restaurant == restaurant_id:
      db.session.delete(restaurantToDelete)
      flash('%s Successfully Deleted' % restaurantToDelete.name)
      user.restaurant = None
      if user.permission == 1:
        user.permission = 0
      db.session.commit()
    else:
      flash('Failed to delete restaurant')
    return redirect(url_for('main.showRestaurants', restaurant_id = restaurant_id))
  else:
    return render_template('deleteRestaurant.html',restaurant = restaurantToDelete, user = user)

#Show a restaurant menu and comments
@main.route('/restaurant/<int:restaurant_id>/')
@main.route('/restaurant/<int:restaurant_id>/menu/')
def showMenu(restaurant_id):
    user = getUser()
    restaurant = db.session.query(Restaurant).filter_by(id = restaurant_id).one()
    items = db.session.query(MenuItem).filter_by(restaurant_id = restaurant_id).all()
    comments = db.session.query(Comment).filter_by(restaurantid = restaurant_id).all()
    return render_template('menu.html', comments = comments, items = items, restaurant = restaurant, user = getUser())
     

#Create a new comment
@main.route('/restaurant/<int:restaurant_id>/comment/new/', methods=['GET', 'POST'])
def newComment(restaurant_id):
   user = getUser()
   if request.method == 'POST':
      if user != None and user.permission == 0:
        comment = Comment(
            title = request.form['title'],
            description = request.form['description'],
            restaurantid = restaurant_id,
            userid = user.id,
            username = False if 'name' in request.form else True
        )
        db.session.add(comment)
        db.session.commit()
        flash('New Comment %s Successfully Created' % (comment.title))
        return redirect(url_for('main.showMenu', restaurant_id = restaurant_id, user = user))
      else:
         flash('Failed to create comment')
         return redirect(url_for('main.showMenu', restaurant_id = restaurant_id, user = user))
   else:
      return render_template('newcomment.html', restaurant_id = restaurant_id, user = user)

#Create a new menu item
@main.route('/restaurant/<int:restaurant_id>/menu/new/',methods=['GET','POST'])
def newMenuItem(restaurant_id):
  user = getUser()
  restaurant = db.session.query(Restaurant).filter_by(id = restaurant_id).one()
  if request.method == 'POST':
      if user != None and user.restaurant == restaurant_id:
        print(request.form['name'])
        if(request.form['name'].value == "anonymous"):
           username = user.name
        newItem = MenuItem(name = request.form['name'], description = request.form['description'], price = request.form['price'], course = request.form['course'], restaurant_id = restaurant_id, username = username)
        db.session.add(newItem)
        db.session.commit()
        flash('New Menu %s Item Successfully Created' % (newItem.name))
      else:
        flash('Failed to create menu item')
      return redirect(url_for('main.showMenu', restaurant_id = restaurant_id))
  else:
      return render_template('newmenuitem.html', restaurant_id = restaurant_id, user = user)

#Edit a menu item
@main.route('/restaurant/<int:restaurant_id>/menu/<int:menu_id>/edit', methods=['GET','POST'])
def editMenuItem(restaurant_id, menu_id):
    user = getUser()
    editedItem = db.session.query(MenuItem).filter_by(id = menu_id).one()
    restaurant = db.session.query(Restaurant).filter_by(id = restaurant_id).one()
    if request.method == 'POST':
        if user != None and user.restaurant == restaurant_id:
          if request.form['name']:
              editedItem.name = request.form['name']
          if request.form['description']:
              editedItem.description = request.form['description']
          if request.form['price']:
              editedItem.price = request.form['price']
          if request.form['course']:
              editedItem.course = request.form['course']
          db.session.add(editedItem)
          db.session.commit()
          flash('Menu Item Successfully Edited')
        else:
          flash('Failed to edit menu item')
        return redirect(url_for('main.showMenu', restaurant_id = restaurant_id))
    else:
        return render_template('editmenuitem.html', restaurant_id = restaurant_id, menu_id = menu_id, item = editedItem, user = user)


#Delete a menu item
@main.route('/restaurant/<int:restaurant_id>/menu/<int:menu_id>/delete', methods = ['GET','POST'])
def deleteMenuItem(restaurant_id,menu_id):
    user = getUser()
    restaurant = db.session.query(Restaurant).filter_by(id = restaurant_id).one()
    itemToDelete = db.session.query(MenuItem).filter_by(id = menu_id).one() 
    if request.method == 'POST':
        if user != None and user.restaurant == restaurant_id:
          db.session.delete(itemToDelete)
          db.session.commit()
          flash('Menu Item Successfully Deleted')
        else:
          flash('Failed to delete menu item')
        return redirect(url_for('main.showMenu', restaurant_id = restaurant_id))
    else:
        return render_template('deleteMenuItem.html', item = itemToDelete, user = user)

@main.route('/login/', methods=['GET','POST'])
def showLogin():
    if request.method == 'POST':
        email = str(request.form.get("email"))
        password = str(request.form.get("password"))

        if email is None or password is None:
            flash('Something went wrong')
            return redirect(url_for('main.showLogin'))

        user, token = create_session(email, password)

        if token is None:
            flash('Invalid username or password')
            return redirect(url_for('main.showLogin'))

        if token.trusted is False:
            return redirect(url_for('main.login2FA'))

        return redirect(url_for('main.showRestaurants'))

    if request.method == 'GET':
        return render_template("login.html", user=getUser())


@main.route('/login/stage2', methods=['GET', 'POST'])
def login2FA():
    user = getUser(insecure=True)

    if request.method == 'POST':
        code = str(request.form.get("code"))

        if user is None or code is None:
            destroy_session()
            return redirect(url_for('main.showLogin'))

        user, token = upgrade_session(user, get_session_token(session.get('token')), code)

        # Check if session upgrade was successful
        if not token.trusted:
            destroy_session()
            return redirect(url_for('main.showLogin'))

        return redirect(url_for('main.showRestaurants'))

    if request.method == 'GET':
        return render_template('login2FA.html', user=user)


@main.route('/signup/', methods=['GET', 'POST'])
def showSignup():
    if request.method == 'POST':
        if request.form['password'] != request.form['password_verification']:
            flash('Passwords do not match')
            return redirect(url_for('main.showSignup'))
        if db.session.query(User).filter_by(name=request.form['name']).one_or_none() or db.session.query(
                User).filter_by(email=request.form['email']).one_or_none():
            flash('Username or email address already registered')
            return redirect(url_for('main.showSignup'))
        newUser = User(name=request.form['name'], email=request.form['email'],
                       password=security.generate_password_hash(request.form['password'], method="scrypt"))
        db.session.add(newUser)
        flash('Account created')
        db.session.commit()
        return redirect(url_for('main.showLogin'))
    else:
        return render_template("signup.html", user=getUser())


@main.route('/account/', methods=['GET'])
def accountSettings():
    return render_template("account.html", user=getUser())


@main.route('/logout/', methods=['POST'])
def signOut():
    destroy_session()
    return redirect(url_for('main.showRestaurants'))


@main.route('/totp/', methods=['GET', 'POST'])
def totp():
    user = getUser()

    if request.method == 'POST':

        # Sanity check for users with 2fa already enabled
        if user.totp is not None and user.totp_verified is True:
            return redirect(url_for('main.accountSettings'))

        # Generate secret key and redirect to qr code page
        user.totp = pyotp.random_base32()
        db.session.commit()
        return redirect(url_for('main.totp'), code=303)

    elif request.method == 'GET':

        if user.totp is None:
            redirect(url_for('main.accountSettings'))

        url = pyotp.TOTP(user.totp).provisioning_uri(name=user.email, issuer_name='COMP3310 Restaurant App')
        qr = pyqrcode.create(url)

        svg = tempfile.SpooledTemporaryFile(max_size=16 * 1024, mode="rw+b")
        qr.svg(svg, scale=7)

        svg.seek(0)
        svg_string = str(svg.read())

        return render_template('totp.html', user=user, qr=svg_string)


@main.route('/totp/verify/', methods=['POST'])
def totp2():
    user = getUser()
    if user is None:
        return redirect(url_for('main.showRestaurants'))

    code = str(request.form.get("code"))
    if code is None:
        return redirect(url_for('main.accountSettings'))

    if len(code) == 6 and pyotp.TOTP(user.totp).verify(code):
        user.totp_verified = True
        db.session.commit()
        return redirect(url_for('main.accountSettings'), code=303)
    else:
        user.totp = None
        user.totp_verified = False
        db.session.commit()
        return redirect(url_for('main.accountSettings'), code=303)
