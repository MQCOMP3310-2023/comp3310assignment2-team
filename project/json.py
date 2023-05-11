from flask import Blueprint, jsonify
from .models import Restaurant, MenuItem
from sqlalchemy import text
from . import db
import json as pyjs

json = Blueprint('json', __name__)

#JSON APIs to view Restaurant Information
@json.route('/restaurant/<restaurant_id>/menu/JSON')
def restaurantMenuJSON(restaurant_id):
    # An SQL injection vulnerability was found and fixed here, by switching from string concatenation to SQL parameterisation
    items = db.session.execute(text('select * from menu_item where restaurant_id = %s'), (restaurant_id))
    items_list = [ i._asdict() for i in items ]
    return pyjs.dumps(items_list)


@json.route('/restaurant/<restaurant_id>/menu/<int:menu_id>/JSON')
def menuItemJSON(restaurant_id, menu_id):
    # An SQL injection vulnerability was found and fixed here, by switching from string concatenation to SQL parameterisation
    Menu_Item = db.session.execute(text('select * from menu_item where id = %s limit 1'), (str(menu_id)))
    items_list = [ i._asdict() for i in Menu_Item ]
    return pyjs.dumps(items_list)

@json.route('/restaurant/JSON')
def restaurantsJSON():
    restaurants = db.session.execute(text('select * from restaurant'))
    rest_list = [ r._asdict() for r in restaurants ]
    return pyjs.dumps(rest_list)


