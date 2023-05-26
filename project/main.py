from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from .models import Restaurant, MenuItem, User
from sqlalchemy import asc
from . import db

main = Blueprint('main', __name__)

def getUser():
    user = None
    if ('email' in session):
        user = db.session.query(User).filter_by(email = f'{session["email"]}').one_or_none()
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
        user = db.session.query(User).filter_by(email = request.form['email'], password = request.form['password']).one_or_none()
        if user == None:
            flash('Invalid username or password')
            return redirect(url_for('main.showLogin'))
        session['email'] = user.email
        return redirect(url_for('main.showRestaurants'))
    else:
        return render_template("login.html", user = getUser())

@main.route('/signup/', methods=['GET','POST'])
def showSignup():
    if request.method == 'POST':
        if request.form['password'] != request.form['password_verification']:
            flash('Passwords do not match')
            return redirect(url_for('main.showSignup'))
        newUser = User(name = request.form['name'], email = request.form['email'], password = request.form['password'])
        db.session.add(newUser)
        flash('Account created')
        db.session.commit()
        return redirect(url_for('main.showLogin'))
    else:
        return render_template("signup.html", user = getUser())

@main.route('/logout/', methods=['GET','POST'])
def signOut():
    if request.method == 'POST':
        session.pop('email', None)
        return redirect(url_for('main.showRestaurants'))
    else:
        return render_template("logout.html", user = getUser())
