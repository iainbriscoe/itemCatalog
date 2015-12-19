from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, CatalogItem, User
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)


# Connect to Database and create database session
engine = create_engine('sqlite:///itemscatalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(
        random.choice(string.ascii_uppercase + string.digits) for x in range(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)

@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    print "access token received %s " % access_token

    app_id = json.loads(open('fb_client_secrets.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (
        app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v2.4/me"
    # strip expire tag from access token
    token = result.split("&")[0]


    url = 'https://graph.facebook.com/v2.4/me?%s&fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    # print "url sent for API access:%s"% url
    # print "API JSON result: %s" % result
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    
    # The token must be stored in the login_session in order to properly logout, let's strip out the information before the equals sign in our token
    stored_token = token.split("=")[1]
    login_session['access_token'] = stored_token

    # Get user picture
    url = 'https://graph.facebook.com/v2.4/me/picture?%s&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    # see if user exists
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']

    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '

    flash("Now logged in as %s" % login_session['username'])
    return output


@app.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    # The access token must be included to successfully logout
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (facebook_id,access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    del login_session['username']
    return "you have been logged out"



def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    try:
        user = session.query(User).filter_by(id=user_id).one()
        return user
    except:
        return None

def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None




@app.route('/')
@app.route('/categories')
def showAllItems():
    categories = session.query(Category).order_by(asc(Category.name))
    items = session.query(CatalogItem).order_by(asc(CatalogItem.name))
    if 'username' not in login_session:
        # BLOCKED OUT FOR TESTING return render_template('publicitems.html', categories=categories, items=items)
        return render_template('publicItems.html', categories=categories, items=items)
    else:
        return render_template('items.html', categories=categories, items=items)

@app.route('/categories/<int:category_id>/')
@app.route('/categories/<int:category_id>/items')
def showCategory(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    categories = session.query(Category).all()
    #creator = getUserInfo(category.user_id)
    items = session.query(CatalogItem).filter_by(category_id=category_id).all()
    try:
        if 'username' not in login_session:
          #BLOCKED OUT FOR TESTING  return render_template('publicCategory.html', category=category, categories=categories, items=items)
            return render_template('publicCategory.html', category=category, categories=categories, items=items)
        else:
            return render_template('category.html', category=category, categories=categories, items=items)
    except:
        return render_template('publicCategory.html', category=category,  categories=categories, items=items)

@app.route('/categories/<int:category_id>/items/<int:item_id>')
def showItemDescription(category_id, item_id):
    category = session.query(Category).filter_by(id=category_id).one()
    categories = session.query(Category).all()
    #ADD CREATOR LATER
    item = session.query(CatalogItem).filter_by(id=item_id).one()
    try:
        if 'username' not in login_session or creator.id != login_session.get('user_id'):
           # BLOCKED OUT FOR TESTING  return render_template('publicItemDescription.html', category=category, categories=categories, item=item)
            return render_template('publicItemDescription.html', category=category, categories=categories, item=item)
        else:
            return render_template('itemDescription.html', category=category, categories=categories, item=item)
    except:
        return render_template('itemDescription.html', category=category, categories=categories, item=item)

@app.route('/category/new', methods=['GET','POST'])
def newCategory():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        # USE WHEN USER IS IMPLIMENTED    newCategory = Category(name=request.form['name'], user_id=login_session.get('user_id'))
        newCategory = Category(name=request.form['name'], user_id=login_session.get('user_id'))    
        session.add(newCategory)
        flash('New Category %s Sucessfully Created' % newCategory.name)
        session.commit()
        return redirect(url_for('showAllItems'))
    else:
        return render_template('newCategory.html')

@app.route('/category/<int:category_id>/edit', methods=['GET', 'POST'])
def editCategory(category_id):
    if 'username' not in login_session:
        return redirect('/login')
    editedCategory = session.query(Category).filter_by(id=category_id).one()
    if request.method == 'POST':
        if request.form['name']:
            editedCategory.name = request.form['name']
            flash('Category: %s Successfully Edited' % editedCategory.name)
            session.commit()
            return redirect(url_for('showAllItems'))
    else:
        return render_template('editCategory.html', category = editedCategory)


@app.route('/category/<int:category_id>/delete', methods=['GET', 'POST'])
def deleteCategory(category_id):
    if 'username' not in login_session:
        return redirect('/login')
    deleteCategory = session.query(Category).filter_by(id=category_id).one()
    deleteItems = session.query(CatalogItem).filter_by(category_id=category_id).all()
    if request.method == 'POST':
        session.delete(deleteCategory)
        
        for item in deleteItems:
            session.delete(item)
        flash('%s Successfully Deleted' % deleteCategory.name)
        session.commit()
        return redirect(url_for('showAllItems'))
    else:
        return render_template('confirmDeleteCategory.html', category = deleteCategory)

    

@app.route('/items/new', methods=['GET','POST'])
def newItem():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newItem = CatalogItem(name=request.form['name'], category_id=request.form['category'], description=request.form['description'], user_id=login_session.get('user_id'))
        session.add(newItem)
        flash("New Item %s Sucessfully Created" % newItem.name)
        session.commit()
        return redirect(url_for('showAllItems'))
    else:
        categories = session.query(Category).all()
        return render_template('newItem.html', categories=categories)



@app.route('/items/<int:item_id>/edit', methods=['GET','POST'])
def editItem(item_id):
    if 'username' not in login_session:
        return redirect('/login')
    editedItem = session.query(CatalogItem).filter_by(id=item_id).one()
    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
            editedItem.description = request.form['description']
            flash('Item: %s Successfully Edited' % editedItem.name)
            session.commit()
            return redirect(url_for('showAllItems'))
    else:
        return render_template('editItem.html', item = editedItem)
    

@app.route('/items/<int:item_id>/delete', methods=['GET','POST'])
def deleteItem(item_id):
    if 'username' not in login_session:
        return redirect('/login')
    deleteItem = session.query(CatalogItem).filter_by(id=item_id).one()
    if request.method == 'POST':
        session.delete(deleteItem)
        flash('%s Successfully Deleted' % deleteItem.name)
        session.commit()
        return redirect(url_for('showAllItems'))
    else:
        return render_template('confirmDeleteItem.html', item = deleteItem)




# JSON APIs to view Restaurant Information
@app.route('/categories/<int:category_id>/items/JSON')
def categoryJSON(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    items = session.query(CatalogItem).filter_by(
        category_id=category_id).all()
    return jsonify(CatalogItems=[i.serialize for i in items])


@app.route('/categories/<int:category_id>/items/<int:item_id>/JSON')
def itemsJSON(category_id, item_id):
    item = session.query(CatalogItem).filter_by(id=item_id).one()
    return jsonify(item=item.serialize)


@app.route('/categories/JSON')
def categoriesJSON():
    categories = session.query(Category).all()
    return jsonify(categories=[c.serialize for c in categories])





if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
