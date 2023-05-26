from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from .models import Restaurant, MenuItem, User, UserToken
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
  if request.method == 'POST':
      newRestaurant = Restaurant(name = request.form['name'])
      db.session.add(newRestaurant)
      flash('New Restaurant %s Successfully Created' % newRestaurant.name)
      db.session.commit()
      return redirect(url_for('main.showRestaurants'))
  else:
      return render_template('newRestaurant.html', user = getUser())

#Edit a restaurant
@main.route('/restaurant/<int:restaurant_id>/edit/', methods = ['GET', 'POST'])
def editRestaurant(restaurant_id):
  editedRestaurant = db.session.query(Restaurant).filter_by(id = restaurant_id).one()
  if request.method == 'POST':
      if request.form['name']:
        editedRestaurant.name = request.form['name']
        flash('Restaurant Successfully Edited %s' % editedRestaurant.name)
        return redirect(url_for('main.showRestaurants'))
  else:
    return render_template('editRestaurant.html', restaurant = editedRestaurant, user = getUser())


#Delete a restaurant
@main.route('/restaurant/<int:restaurant_id>/delete/', methods = ['GET','POST'])
def deleteRestaurant(restaurant_id):
  restaurantToDelete = db.session.query(Restaurant).filter_by(id = restaurant_id).one()
  if request.method == 'POST':
    db.session.delete(restaurantToDelete)
    flash('%s Successfully Deleted' % restaurantToDelete.name)
    db.session.commit()
    return redirect(url_for('main.showRestaurants', restaurant_id = restaurant_id))
  else:
    return render_template('deleteRestaurant.html',restaurant = restaurantToDelete, user = getUser())

#Show a restaurant menu
@main.route('/restaurant/<int:restaurant_id>/')
@main.route('/restaurant/<int:restaurant_id>/menu/')
def showMenu(restaurant_id):
    restaurant = db.session.query(Restaurant).filter_by(id = restaurant_id).one()
    items = db.session.query(MenuItem).filter_by(restaurant_id = restaurant_id).all()
    return render_template('menu.html', items = items, restaurant = restaurant, user = getUser())
     


#Create a new menu item
@main.route('/restaurant/<int:restaurant_id>/menu/new/',methods=['GET','POST'])
def newMenuItem(restaurant_id):
  restaurant = db.session.query(Restaurant).filter_by(id = restaurant_id).one()
  if request.method == 'POST':
      newItem = MenuItem(name = request.form['name'], description = request.form['description'], price = request.form['price'], course = request.form['course'], restaurant_id = restaurant_id)
      db.session.add(newItem)
      db.session.commit()
      flash('New Menu %s Item Successfully Created' % (newItem.name))
      return redirect(url_for('main.showMenu', restaurant_id = restaurant_id))
  else:
      return render_template('newmenuitem.html', restaurant_id = restaurant_id, user = getUser())

#Edit a menu item
@main.route('/restaurant/<int:restaurant_id>/menu/<int:menu_id>/edit', methods=['GET','POST'])
def editMenuItem(restaurant_id, menu_id):

    editedItem = db.session.query(MenuItem).filter_by(id = menu_id).one()
    restaurant = db.session.query(Restaurant).filter_by(id = restaurant_id).one()
    if request.method == 'POST':
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
        return redirect(url_for('main.showMenu', restaurant_id = restaurant_id))
    else:
        return render_template('editmenuitem.html', restaurant_id = restaurant_id, menu_id = menu_id, item = editedItem, user = getUser())


#Delete a menu item
@main.route('/restaurant/<int:restaurant_id>/menu/<int:menu_id>/delete', methods = ['GET','POST'])
def deleteMenuItem(restaurant_id,menu_id):
    restaurant = db.session.query(Restaurant).filter_by(id = restaurant_id).one()
    itemToDelete = db.session.query(MenuItem).filter_by(id = menu_id).one() 
    if request.method == 'POST':
        db.session.delete(itemToDelete)
        db.session.commit()
        flash('Menu Item Successfully Deleted')
        return redirect(url_for('main.showMenu', restaurant_id = restaurant_id))
    else:
        return render_template('deleteMenuItem.html', item = itemToDelete, user = getUser())

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
        newUser = User(name = request.form['name'], email = request.form['email'], password = security.generate_password_hash(request.form['password'], method="scrypt"))
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
