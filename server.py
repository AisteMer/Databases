
"""
Columbia's COMS W4111.001 Introduction to Databases
Example Webserver
To run locally:
    python server.py
Go to http://localhost:8111 in your browser.
A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""
import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, url_for, Response
import random 

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)

#
# The following is a dummy URI that does not connect to a valid database. You will need to modify it to connect to your Part 2 database in order to use the data.
#
# XXX: The URI should be in the format of: 
#
#     postgresql://USER:PASSWORD@34.148.223.31/proj1part2
#
# For example, if you had username zy2431 and password 123123, then the following line would be:
#
#     DATABASEURI = "postgresql://zy2431:123123@34.148.223.31/proj1part2"
#
# Modify these with your own credentials you received from TA!

DATABASE_USERNAME = "am5678"
DATABASE_PASSWRD = "000271"
DATABASE_HOST = "34.148.223.31"
DATABASEURI = f"postgresql://{DATABASE_USERNAME}:{DATABASE_PASSWRD}@{DATABASE_HOST}/proj1part2"


#
# This line creates a database engine that knows how to connect to the URI above.
#
engine = create_engine(DATABASEURI)

"""
Example of running queries in your database
Note that this will probably not work if you already have a table named 'test' in your database, containing meaningful data. This is only an example showing you how to run queries in your database using SQLAlchemy.


with engine.connect() as conn:
	create_table_command =
	CREATE TABLE IF NOT EXISTS test (
		id serial,
		name text
	)
	
	res = conn.execute(text(create_table_command))
	insert_table_command = INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace')
	res = conn.execute(text(insert_table_command))
	you need to commit for create, insert, update queries to reflect
	conn.commit()

"""


@app.before_request
def before_request():
	"""
	This function is run at the beginning of every web request 
	(every time you enter an address in the web browser).
	We use it to setup a database connection that can be used throughout the request.

	The variable g is globally accessible.
	"""
	try:
		g.conn = engine.connect()
	except:
		print("uh oh, problem connecting to database")
		import traceback; traceback.print_exc()
		g.conn = None

@app.teardown_request
def teardown_request(exception):
	"""
	At the end of the web request, this makes sure to close the database connection.
	If you don't, the database could run out of memory!
	"""
	try:
		g.conn.close()
	except Exception as e:
		pass


#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to, for example, localhost:8111/foobar/ with POST or GET then you could use:
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
# 
# see for routing: https://flask.palletsprojects.com/en/1.1.x/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#
@app.route('/')
def home():
	select_restaurants= text("SELECT * from Restaurant")
	cursor=g.conn.execute(select_restaurants)
	restaurants = cursor.fetchall()
	cursor.close()
	return render_template('home.html', restaurants=restaurants)



@app.route('/login', methods=['POST','GET'])
def login():
	if request.method == 'POST':
		username = request.form['username']
		password = request.form['password']

		check_username = text("SELECT * FROM USERS WHERE username = :username")
		result_username = g.conn.execute(check_username, {"username": username}).fetchone()
		
		if result_username: 
			check_password = text("SELECT * FROM USERS WHERE username = :username AND password = :password")
			result_password = g.conn.execute(check_password, {"username": username, "password": password}).fetchone()

			if result_password:
				return redirect(url_for('user_info', username=username)) 
		
		else: 
			error_message = "Your username or password was incorrect. Please try again!"
			select_restaurants= text("SELECT * from Restaurant")
			cursor=g.conn.execute(select_restaurants)
			restaurants = cursor.fetchall()
			cursor.close()
			return render_template('home.html', restaurants=restaurants, error_message=error_message)
	
	else: 
		select_restaurants= text("SELECT * from Restaurant")
		cursor=g.conn.execute(select_restaurants)
		restaurants = cursor.fetchall()
		cursor.close()
		return render_template('home.html', restaurants=restaurants)
	


@app.route('/login/<username>', methods=['GET'])
def user_info(username):
	select_fav_cuisine = text("SELECT * FROM has_fav WHERE userName = :userName")
	cursor1 = g.conn.execute(select_fav_cuisine, {"userName": username})
	cuisines = cursor1.fetchone()  
	
	select_bookmarks = text("""
		SELECT *  
		FROM BOOKMARK bookmark
		JOIN Restaurant r on bookmark.restaurant_id = r. restaurant_id
		WHERE username= :username
	""")
	
	cursor4=g.conn.execute(select_bookmarks, {"username": username})
	bookmarks = cursor4.fetchall()

	grouped_bookmarks = {}
	for bookmark in bookmarks:
		bookmark_id = bookmark[0]
		if bookmark_id not in grouped_bookmarks:
			grouped_bookmarks[bookmark_id] = []
		grouped_bookmarks[bookmark_id].append(bookmark)


	select_friends = text ("SELECT * FROM has_friendship WHERE username1 = :username")
	cursor2= g.conn.execute(select_friends, {"username": username})
	friends = cursor2.fetchall() 
	



	select_users = text("SELECT * FROM users WHERE username NOT IN (SELECT userName2 FROM has_friendship WHERE username1 = :username) AND username<> :username")
	cursor3= g.conn.execute(select_users,{"username": username})
	users = cursor3.fetchall() 

	cursor1.close()
	cursor2.close()
	cursor3.close()
	cursor4.close()


	return render_template("user_info.html", username=username, cuisines=cuisines, friends=friends, username1=username, users=users, grouped_bookmarks=grouped_bookmarks)

@app.route('/<username>/add_user', methods=['POST','GET'])
def addUser(username):
	if request.method == 'POST':
		username2 = request.form['username2'].strip() 

	insert_friend = text("""
	INSERT INTO has_friendship (userName1, userName2) 
	VALUES (:username1, :username2 )
	""")

	g.conn.execute(insert_friend, {
			'username1': username,
			'username2': username2,
	})

	g.conn.commit()
	
	return redirect(url_for('viewFriend', username=username2))


"""
	request is a special object that Flask provides to access web request information:

	request.method:   "GET" or "POST"
	request.form:     if the browser submitted a form, this contains the data in the form
	request.args:     dictionary of URL arguments, e.g., {a:1, b:2} for http://localhost?a=1&b=2

	See its API: https://flask.palletsprojects.com/en/1.1.x/api/#incoming-request-data
	"""


#for when user searches specifically for a restaurant 
@app.route('/search', methods=['GET'])
def searchRestaurant(): 
	user_input = request.args.get('user_input')
	if user_input.isdigit(): 
		user_input_zip = int(user_input)
	else: 
		user_input_zip = -1 

	search = text("""
    SELECT r.restaurant_id, ac.cuisineName, r.priceTag, r.name, located.zipcode, cuisine.region
    FROM Restaurant r
    JOIN ASSIGN_CUISINE ac ON r.restaurant_id = ac.restaurant_id
    JOIN is_located located ON r.restaurant_id = located.restaurant_id
    JOIN cuisines cuisine ON cuisine.cuisineName = ac.cuisineName
    WHERE ac.cuisineName = :user_input
       OR r.name = :user_input
       OR located.zipcode = :user_input_zip
       OR cuisine.region = :user_input
	""")
	cursor = g.conn.execute(search, {"user_input": user_input, "user_input_zip": user_input_zip})
	restaurants=cursor.fetchall(); 

	restaurant_details={}
	if restaurants: 
		pass 
	else: 
		restaurant_details= {
			'name': "No Matching Results", 
			'restaurant_id': None, 
			'cuisineName': None, 
			'priceTag': None, 
			'zipcode': None, 
			'region': None 
		}
	
	cursor.close() 
	return render_template("searchRestaurant.html", restaurants=restaurants, restaurant_details=restaurant_details) 
	#make inidivial html pages for each restaurant 
	# DEBUG: this is debugging code to see what request looks like
	print(request.args)


@app.route('/view/friend/<username>', methods=['GET'])
def viewFriend(username): 
	username = username.strip()
	select_comments = text("""
						SELECT * FROM RATES 
						JOIN restaurant r on RATES.restaurant_id= r.restaurant_id
						WHERE username= :username
						ORDER BY timestamp DESC
						""")
	
	select_bookmarks = text("""
		SELECT *  
		FROM BOOKMARK bookmark
		JOIN Restaurant r on bookmark.restaurant_id = r. restaurant_id
		WHERE username= :username
	""")
	cursor1=g.conn.execute(select_comments, {"username": username})
	comments = cursor1.fetchall()
	cursor2=g.conn.execute(select_bookmarks, {"username": username})
	bookmarks = cursor2.fetchall()

	print(f"Username being queried: {username}")
	print(f"Number of comments found: {len(comments)}")
	print(f"Number of bookmarks found: {len(bookmarks)}")

	grouped_bookmarks = {}
	for bookmark in bookmarks:
		bookmark_id = bookmark[0]
		if bookmark_id not in grouped_bookmarks:
			grouped_bookmarks[bookmark_id] = []
		grouped_bookmarks[bookmark_id].append(bookmark)

	return render_template("friend.html", comments=comments,username=username, grouped_bookmarks=grouped_bookmarks)

@app.route('/view/<int:restaurant_id>', methods=['GET','POST'])
def viewRestaurant(restaurant_id): 
	select_restaurant = text("SELECT * FROM Restaurant WHERE restaurant_id = :restaurant_id")
	cursor1 = g.conn.execute(select_restaurant, {"restaurant_id": restaurant_id})
	restaurant = cursor1.fetchone()  # Fetch a single restaurant
	
	select_ratings = text("SELECT * FROM RATES WHERE restaurant_id=:restaurant_id")
	cursor2= g.conn.execute(select_ratings, {"restaurant_id": restaurant_id})
	ratings = cursor2.fetchall()  # Fetch all the comments 
	

	select_locations = text("SELECT * FROM IS_LOCATED WHERE restaurant_id=:restaurant_id")
	cursor3= g.conn.execute(select_locations, {"restaurant_id": restaurant_id})
	locations = cursor3.fetchall() #fetch all the locations 

	select_cuisines = text("SELECT * FROM ASSIGN_CUISINE WHERE restaurant_id=:restaurant_id")
	cursor4= g.conn.execute(select_cuisines, {"restaurant_id": restaurant_id})
	cuisines = cursor4.fetchall() #fetch all the cuisines of each res 
	
	select_awards = text("SELECT * FROM AWARDS WHERE restaurant_id=:restaurant_id")
	cursor5= g.conn.execute(select_awards, {"restaurant_id": restaurant_id})
	awards = cursor5.fetchall() #fetch all the awards for a res 

	select_avg_rating = text("SELECT COUNT(*) as numReviews, AVG(rating) as average_rating, restaurant_id FROM RATES WHERE restaurant_id=:restaurant_id GROUP BY restaurant_id ")
	cursor6= g.conn.execute(select_avg_rating, {"restaurant_id": restaurant_id})
	avg_rating = cursor6.fetchall() #fetch avg rating

	if avg_rating: 
		numReviews, average_rating, restaurant_id = avg_rating[0]
		average_rating = float(average_rating) if average_rating is not None else "No ratings yet"
	else: 
		numReviews=0
		average_rating= "No Reviews yet!"

	cursor1.close()
	cursor2.close() 
	cursor3.close()
	cursor4.close()
	cursor5.close()
	cursor6.close()

	if request.method == 'POST':
		username = request.form['username']
		comment = request.form['user_input']
		rating = request.form['rating']

		check_username = text("SELECT * FROM USERS WHERE username = :username")
		cursor7 = g.conn.execute(check_username, {"username": username})
		user_exists = cursor7.fetchone()

		if user_exists: 
			insert_comment = text("""
			INSERT INTO RATES (restaurant_id, userName, rating, comment) 
			VALUES (:restaurant_id, :username, :rating, :comment)
			""")

			g.conn.execute(insert_comment, {
			'restaurant_id': restaurant_id,
			'username': username,
			'rating': rating,
			'comment': comment
			})

			insert_moderate = text("""
			INSERT INTO MODERATES (admin_id, approval, restaurant_id, username)
						  VALUES (:admin_id,:approval,:restaurant_id, :username)
						  """)
			
			g.conn.execute(insert_moderate, {
				'admin_id': 1, 
				"approval": t, 
				'restaurant_id': restaurant_id,
				'username': username

			})

			g.conn.commit()
			cursor7.close()
			return render_template('displayRestaurant.html', restaurant_id=restaurant_id,restaurant=restaurant, ratings=ratings, locations=locations, cuisines=cuisines, awards=awards, avg_rating=average_rating, numReviews=numReviews)
		
		else: 
			error_message = "You must be a user to post a comment!"
			return render_template("displayRestaurant.html", 
                restaurant=restaurant, 
                ratings=ratings, 
                error_message=error_message)

	return render_template("displayRestaurant.html", restaurant=restaurant, ratings=ratings, locations=locations, cuisines=cuisines, awards=awards, avg_rating=average_rating, numReviews=numReviews)


@app.route('/add_to_bookmark/<bookmark_id>', methods=['POST','GET'])
def addEBookmark(bookmark_id):
	list_res = text("SELECT name FROM Restaurant")
	cursor=g.conn.execute(list_res)
	list_res= cursor.fetchall() 

	if request.method == 'POST':
		name = request.form['name']

		get_id = text("SELECT restaurant_id FROM Restaurant WHERE name = :name")
		cursor1 = g.conn.execute(get_id, {"name": name})
		res_id = cursor1.fetchone()  
		res_id = res_id[0]
		print(res_id)

		get_bookmark = text("SELECT bookmarkname, username FROM Bookmark WHERE bookmark_id = :bookmark_id")
		cursor2 = g.conn.execute(get_bookmark, {"bookmark_id": bookmark_id})
		bookmark = cursor2.fetchone()  
            
		if bookmark:
			bookmarkname = bookmark[0]  
			username = bookmark[1]      

		insert_bookmark = text("""
		INSERT INTO Bookmark (bookmark_id, bookmarkname, username, restaurant_id) 
		VALUES (:bookmark_id, :bookmarkname, :username, :res_id)
		""")
		g.conn.execute(insert_bookmark, {
		"bookmark_id": bookmark_id, 
		"bookmarkname": bookmarkname, 
		"username": username, 
		"res_id": res_id
		})

		g.conn.commit()
		cursor1.close() 
		cursor2.close()
		return render_template("addEBookmark.html", bookmark_id=bookmark_id, list_res=list_res)
	
	cursor.close() 

	return render_template("addEBookmark.html", bookmark_id=bookmark_id, list_res=list_res)


@app.route('/login/create_bookmark/<username>', methods=['POST','GET'])
def createBookmark(username): 
	print (username)
	list_res = text("SELECT name FROM Restaurant")
	cursor=g.conn.execute(list_res)
	list_res= cursor.fetchall() 

	if request.method == 'POST':
		bookmarkname = request.form['bookmarkname']
		name = request.form['name']

		get_id = text("SELECT restaurant_id FROM Restaurant WHERE name = :name")
		cursor1 = g.conn.execute(get_id, {"name": name})
		res_id = cursor1.fetchone()  
		res_id = res_id[0]

		while True:
			bookmark_id = random.randint(10, 100)
			check_query = text("SELECT bookmark_id FROM Bookmark WHERE bookmark_id = :bookmark_id")
			cursor1 = g.conn.execute(check_query, {"bookmark_id": bookmark_id})
			num = cursor1.fetchone()
			cursor1.close()
			if not num:
				break  
	
	
		insert_bookmark = text("""
			INSERT INTO Bookmark (bookmark_id, bookmarkname, username, restaurant_id) 
			VALUES (:bookmark_id, :bookmarkname, :username, :res_id)
			""")

		g.conn.execute(insert_bookmark, {
		"bookmark_id": bookmark_id, 
		"bookmarkname": bookmarkname, 
		"username": username, 
		"res_id": res_id
		})

		g.conn.commit()
		return render_template("createBookmark.html", username=username, list_res=list_res)

	return render_template("createBookmark.html", username=username, list_res=list_res)


#
# example of a database query
#
"""
	select_query = "SELECT name from test"
	cursor = g.conn.execute(text(select_query))
	names = []
	for result in cursor:
		names.append(result[0])
	cursor.close()
	"""
	#
	# Flask uses Jinja templates, which is an extension to HTML where you can
	# pass data to a template and dynamically generate HTML based on the data
	# (you can think of it as simple PHP)
	# documentation: https://realpython.com/primer-on-jinja-templating/
	#
	# You can see an example template in templates/index.html
	#
	# context are the variables that are passed to the template.
	# for example, "data" key in the context variable defined below will be 
	# accessible as a variable in index.html:
	#
	#     # will print: [u'grace hopper', u'alan turing', u'ada lovelace']
	#     <div>{{data}}</div>
	#     
	#     # creates a <div> tag for each element in data
	#     # will print: 
	#     #
	#     #   <div>grace hopper</div>
	#     #   <div>alan turing</div>
	#     #   <div>ada lovelace</div>
	#     #
	#     {% for n in data %}
	#     <div>{{n}}</div>
	#     {% endfor %}
	#
#context = dict(data = names)


	#
	# render_template looks in the templates/ folder for files.
	# for example, the below file reads template/index.html
	#
#return render_template("index.html", **context)

#
# This is an example of a different path.  You can see it at:
# 
#     localhost:8111/another
#
# Notice that the function name is another() rather than index()
# The functions for each app.route need to have different names
#
"""
@app.route('/another')
def another():
	return render_template("another.html")


# Example of adding new data to the database
@app.route('/add', methods=['POST'])
def add():
	# accessing form inputs from user
	name = request.form['name']
	
	# passing params in for each variable into query
	params = {}
	params["new_name"] = name
	g.conn.execute(text('INSERT INTO test(name) VALUES (:new_name)'), params)
	g.conn.commit()
	return redirect('/')


@app.route('/login')
def login():
	abort(401)
	this_is_never_executed()

"""

if __name__ == "__main__":
	import click

	@click.command()
	@click.option('--debug', is_flag=True)
	@click.option('--threaded', is_flag=True)
	@click.argument('HOST', default='0.0.0.0')
	@click.argument('PORT', default=8111, type=int)
	def run(debug, threaded, host, port):
		"""
		This function handles command line parameters.
		Run the server using:

			python server.py

		Show the help text using:

			python server.py --help

		"""

		HOST, PORT = host, port
		print("running on %s:%d" % (HOST, PORT))
		app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)

run()
