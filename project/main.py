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

def getTime():
    return calendar.timegm(datetime.utcnow().utctimetuple())

def getUser():
    user = None
    if ('token' in session):
        token = db.session.query(UserToken).filter_by(token = f'{session["token"]}').one_or_none()
        if (token == None):
            return None
        time = getTime()
        if (token.tolu < time - 2592000): # One month token expiry period
            db.session.delete(token)
            db.session.commit()
            session.pop('token', None)
            return None
        token.tolu = time
        db.session.commit()
        user = db.session.query(User).filter_by(id = token.id).one_or_none()
    return user

#Show all restaurants
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
        comment = Comment(title = request.form['title'], description = request.form['description'], name = request.form['name'], restaurantid = restaurant_id)
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
        newItem = MenuItem(name = request.form['name'], description = request.form['description'], price = request.form['price'], course = request.form['course'], restaurant_id = restaurant_id)
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
        user = db.session.query(User).filter_by(email = request.form['email']).one_or_none()
        if user == None or not security.check_password_hash(user.password, request.form['password']):
            flash('Invalid username or password')
            return redirect(url_for('main.showLogin'))
        token = None
        while (token == None):
            temp_token = secrets.token_hex(16)
            if db.session.query(UserToken).filter_by(token = temp_token).one_or_none() != None:
                logging.warning("Duplicate token " + temp_token)
            else:
                token = UserToken(id = user.id, token = temp_token, tolu = getTime())
        session['token'] = token.token
        db.session.add(token)
        db.session.commit()
        return redirect(url_for('main.showRestaurants'))
    else:
        return render_template("login.html", user = getUser())

@main.route('/signup/', methods=['GET','POST'])
def showSignup():
    if request.method == 'POST':
        if request.form['password'] != request.form['password_verification']:
            flash('Passwords do not match')
            return redirect(url_for('main.showSignup'))
        if db.session.query(User).filter_by(name = request.form['name']).one_or_none() or db.session.query(User).filter_by(email = request.form['email']).one_or_none():
            flash('Username or email address already registered')
            return redirect(url_for('main.showSignup'))
        newUser = User(name = request.form['name'], email = request.form['email'], password = security.generate_password_hash(request.form['password'], method="scrypt"), permission = 0, restaurant = None)
        db.session.add(newUser)
        flash('Account created')
        db.session.commit()
        return redirect(url_for('main.showLogin'))
    else:
        return render_template("signup.html", user = getUser())

@main.route('/logout/', methods=['GET','POST'])
def signOut():
    if request.method == 'POST':
        db.session.delete(db.session.query(UserToken).filter_by(token = f'{session["token"]}').one_or_none())
        db.session.commit()
        session.pop('token', None)
        return redirect(url_for('main.showRestaurants'))
    else:
        return render_template("logout.html", user = getUser())
