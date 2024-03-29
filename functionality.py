import psycopg2
from sshtunnel import SSHTunnelForwarder
import datetime


def connect_to_db(username, password):
    server = SSHTunnelForwarder(('starbug.cs.rit.edu', 22),
                            ssh_username=username,
                            ssh_password=password,
                            remote_bind_address=('127.0.0.1', 5432))

    server.start()
    print("SSH tunnel established")
    params = {
        'database': "p320_07",
        'user': username,
        'password': password,
        'host': '127.0.0.1',
        'port': server.local_bind_port
    }

    conn = psycopg2.connect(**params)
    curs = conn.cursor()
    print("Database connection established")

    return server, conn, curs


def close(server, conn, curs):
    server.close()
    conn.close()
    curs.close()


def help():
    print('Below are valid commands and their uses\n'
          '---------------------------\n'
          'help\n\tdisplays this information regardless of menu\n'
          'quit\n\texits the program regardless of menu\n'
          
          '========= ACCOUNTS =========\n'
          'makeaccount username password email firstname lastname\n\tmakes a new account with specified info\n'
          'login username password\n\tlogs in if username and password match database entry\n'
          'logout\n\tlogs out of current account\n'
          '========= FRIENDS =========\n'
          'addfriend username\n\tadds user to friends list\n'
          'removefriend username\n\tremoves friend from friends list\n'
          'finduser email\n\treturns users with similar email\n'
          '========= COLLECTIONS =========\n'
          'createcollection name \n\tcreates a collection with a name\n'
          'deletecollection \n\tdeletes entered collection from database\n'
          'viewcollections \n\tviews all collections of the logged in user\n'
          'editcollectionname \n\tedits entered collection name to entered new name\n'
          'addbook bookid collection name \n\tadds a book to the collection\n'
          'removebook bookid collection name \n\tremoves a book from a collection\n'
          '========= READ/RATE =========\n'
          'read bookid start|stop page\n\tstart or stop a book reading session given page number\n'
          'read collectionid\n\tstart reading a random book in a collection at page 0\n'
          'rate bookid rating\n\trate a book between 1 and 5 stars'
          )


def makeaccount(conn,curs, tokens):

    if len(tokens)!=6:
        print('Invalid entry')
        return -1

    # print(tokens[1:])

    username = tokens[1]
    password = tokens[2]
    email = tokens[3]
    fname = tokens[4]
    lname = tokens[5]

    curs.execute("""SELECT username FROM p320_07."Reader";""")
    data = curs.fetchall()
    usernames = [row[0] for row in data]
    if username in usernames:
        print("That username is taken")
        return -1

    curs.execute("""SELECT MAX(user_id) FROM p320_07."Reader";""")
    data = curs.fetchall()

    next_id = data[0][0] + 1
    current_date = datetime.datetime.now()

    #print(username, password, email, fname, lname, next_id)

    curs.execute("""INSERT INTO p320_07."Reader"
        (user_id, username, password, email, first_name, last_name, created_date, last_access)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s);""",
        (next_id, username, password, email, fname, lname, current_date, current_date))

    conn.commit()
    print("New account created and logged in")
    return next_id


def login(conn, curs, tokens):
    if len(tokens)!=3:
        print('Invalid entry')
        return -1

    username = tokens[1]
    password = tokens[2]

    curs.execute("""SELECT user_id,username,password FROM p320_07."Reader";""")
    data = curs.fetchall()
    users = dict()
    for user in data:
        users[user[1]] = [user[0], user[2]]

    if username not in users or users[username][1] != password:
        print("Username doesn't exist or wrong password")
        return -1

    user_id = users[username][0]
    curs.execute("""UPDATE p320_07."Reader" SET last_access = %s WHERE user_id = %s8;""",(datetime.datetime.now(),user_id))
    conn.commit()
    print("Logged in")
    return user_id


def addfriend(conn, curs, passed_user_id, tokens):
    if len(tokens) != 2:
        print('Invalid entry')
        return

    friend_username = tokens[1]
    friend_id = -1

    curs.execute("""SELECT user_id, username FROM p320_07."Reader";""")
    reader_data = curs.fetchall()
    for reader in reader_data:
        if friend_username == reader[1]: friend_id = reader[0]

    if friend_id == -1:
        print("There is no user with that username")
        return

    curs.execute("""SELECT user_id, friend_id FROM p320_07."Friendship";""")
    friend_data = curs.fetchall()

    for friend in friend_data:
        if passed_user_id == friend[0] and friend_id == friend[1]:
            print('Already friends')
            return

    curs.execute("""INSERT INTO p320_07."Friendship"
        (user_id, friend_id)
        VALUES (%s, %s);""",
        (passed_user_id, friend_id))

    conn.commit()
    print("Friend added")


def removefriend(conn, curs, passed_user_id, tokens):
    if len(tokens) != 2:
        print('Invalid entry')
        return

    friend_username = tokens[1]
    friend_id_input = -1
    friendship_exist = False

    curs.execute("""SELECT user_id, username FROM p320_07."Reader";""")
    reader_data = curs.fetchall()
    for reader in reader_data:
        if friend_username == reader[1]: friend_id_input = reader[0]

    if friend_id_input == -1:
        print("There is no user with that username")
        return

    curs.execute("""SELECT user_id, friend_id FROM p320_07."Friendship";""")
    friend_data = curs.fetchall()

    for friend in friend_data:
        if passed_user_id == friend[0] and friend_id_input == friend[1]:

            curs.execute("""DELETE FROM p320_07."Friendship" 
                WHERE user_id=%s AND friend_id = %s;""",
                (passed_user_id, friend_id_input))

            print("Friendship was deleted")
            conn.commit()

            return

    print("No friend was found")


def finduser(conn, curs, tokens):
    if len(tokens) != 2:
        print('Invalid entry')
        return
    email = tokens[1]
    curs.execute("""SELECT username,email FROM p320_07."Reader" WHERE user_id IN 
            (SELECT user_id FROM p320_07."Reader" WHERE email LIKE %s);""", ('%%' + email + '%%',))
    data = curs.fetchall()
    print('Username\t\tEmail')
    for user in data: print(f'{user[0]}\t\t{user[1]}')
 

def create_collection(conn, curs, tokens, user_id):
    if len(tokens) == 1:
        print('Invalid collection name')
        return

    # get the whole name including spaces
    name = ' '.join(tokens[1:])

    # get the next available id
    curs.execute("""SELECT MAX(collection_id) FROM p320_07."Collection";""")
    data = curs.fetchall()
    next_collection = data[0][0] + 1

    # adding new collection with the collection name into Collection table
    curs.execute(f"""INSERT INTO p320_07."Collection" (collection_id, collection_name)
                    VALUES ({next_collection}, '{name}'); """)

    # adding new instance of a collection on the Bookshelf with the current user's id
    curs.execute(f"""INSERT INTO p320_07."Bookshelf" (user_id, collection_id)
                    VALUES ({user_id}, {next_collection}); """)

    # add to database
    conn.commit()

    print(f"Collection was successfully created!")

    
def add_to_collection(conn, curs, tokens, user_id):
    # get book user wants to add and the name of the collection,
    add_book = int(tokens[1])
    collection_name = ' '.join(tokens[2:])  # should be spelled EXACTLY like in the database

    #   figure out collection id with the name they inputted
    curs.execute(f"""SELECT collection_id FROM p320_07."Collection" WHERE collection_name = '{collection_name}'""")
    collection_id = curs.fetchall()

    #   if the collection doesn't exist with that name
    if len(collection_id) == 0:
        print(f"\nCannot find collection named {collection_name}.")
        return

    # see what the users collections are
    curs.execute(f"""SELECT collection_id FROM p320_07."Bookshelf" WHERE user_id = {user_id} """)
    data = curs.fetchall()

    # if the book is added, it will be made to True in the loop, used for later if unsuccessful to add
    added = False

    # for all the collections the user made
    for id in data:
        # if they have the collection we want to add to
        if id in collection_id:
            # get the collection id from the tuple id
            for number in id:
                try:
                    # try to add the book to the Collection
                    curs.execute(f"""INSERT INTO p320_07."CollectionContains" (book_id, collection_id) 
                                    VALUES ({add_book}, {number}); """)
                except Exception as e:
                    print("\nThis book is already in the Collection or it does not exist!")
                    conn.rollback() # clear SQL query
                    return

                else:
                    # book was added successfully
                    print(f"Added Book with id {add_book} to {collection_name}.")
                    added = True
                break

    if not added:
        print(f"\nYou do not own this Collection!")
        return

    # will only commit if everything passes
    conn.commit()


def delete_from_collection(conn, curs, tokens, user_id):
    # get book user wants to remove and the name of the collection,
    remove_book = int(tokens[1])
    collection_name = ' '.join(tokens[2:])  # should be spelled EXACTLY like in the database

    # figure out collection id with the name they inputted
    curs.execute(f"""SELECT collection_id FROM p320_07."Collection" WHERE collection_name = '{collection_name}'""")
    collection_id = curs.fetchall()

    # if the collection doesn't exist with that name
    if len(collection_id) == 0:
        print(f"\nCannot find collection named {collection_name}.")
        return

    # see what the users collections are
    curs.execute(f"""SELECT collection_id FROM p320_07."Bookshelf" WHERE user_id = {user_id} """)
    data = curs.fetchall()

    # for all the collections the user made
    for id in data:
        # if they have the collection we want to add to
        if id in collection_id:
            # get the collection id from the tuple id
            for number in id:
                curs.execute(f"""DELETE FROM p320_07."CollectionContains" WHERE book_id = {remove_book} 
                                AND collection_id = {number} """)

    print(f"\n Book #{remove_book} was removed from {collection_name} or it was not previously in the Collection")

    # will only commit if everything passes
    conn.commit()

    
def delete_collection(conn, curs, user_id):
    # gets the name of the collection the user wishes to delete
    name_of_collection = input("Enter the collection name: ")

    # determine the collection id of the named collection
    curs.execute(f"""SELECT a.collection_id FROM p320_07."Collection" a INNER JOIN p320_07."Bookshelf" B on 
                     a.collection_id = B.collection_id WHERE B.user_id = {user_id} 
                     AND a.collection_name = '{name_of_collection}'""")
    collection_id = curs.fetchall()

    # returns fail message if collection cannot be found
    if len(collection_id) == 0:
        print(f"\nCannot find Collection: {name_of_collection}.")
        return

    # for the located id of the determine collection, delete said collection from all tables containing it
    for id in collection_id:
        id = id[0]
        curs.execute(f"""DELETE FROM p320_07."Bookshelf" WHERE collection_id = {id}""")
        curs.execute(f"""DELETE FROM p320_07."Collection" WHERE collection_id = {id}""")
        curs.execute(f"""DELETE FROM p320_07."CollectionContains" WHERE collection_id = {id}""")

    print(f"\n Collection: {name_of_collection} was deleted.")

    # only commits if everything passes
    conn.commit()


def view_collections(curs, user_id):
    # displays the collection of the given user_id
    curs.execute(f"""SELECT a.collection_name FROM p320_07."Collection" a 
                     INNER JOIN p320_07."Bookshelf" B on a.collection_id = B.collection_id 
                     WHERE B.user_id = {user_id}""")
    collections = curs.fetchall()
    for tuple in collections:
        collection = tuple[0]

        # get collection_id
        curs.execute("""SELECT collection_id FROM p320_07."Collection" WHERE collection_name = %s""", (collection,))
        data = curs.fetchall()
        collection_id = data[0][0]

        # get all books in collection and count number of them
        curs.execute("""SELECT book_id FROM p320_07."CollectionContains"
                        WHERE collection_id = %s""", (collection_id,))
        collection_books = curs.fetchall()
        book_count = len(collection_books)

        # get all pages in each book and sum them all up
        total_pages = 0
        for book_id in collection_books:
            curs.execute("""SELECT length FROM p320_07."Book" WHERE book_id = %s""", (book_id,))
            total_pages += curs.fetchall()[0][0]

        print(collection + ": [" + str(book_count) + " books, " + str(total_pages) + " pages total]")


def edit_collection_name(conn, curs, user_id):
    # get the original collection name from input
    collection_name = input("Enter your collection name: ")
    new_name = input("Enter the new name for your collection: ")

    updated = False

    # strip the inputs to remove the \n
    curs.execute(
        f"""SELECT collection_id FROM p320_07."Collection" WHERE collection_name = '{collection_name.strip()}'""")
    collection_id = curs.fetchall()

    for collections in collection_id:

        curs.execute(f"""SELECT user_id FROM p320_07."Bookshelf" WHERE collection_id = {collections[0]}""")
        check_id = curs.fetchall()

        # checking if they own the collection
        for id in check_id:
            if id[0] == user_id:
                # update collection
                curs.execute(f"""UPDATE p320_07."Collection" SET collection_name = '{new_name.strip()}' 
                                 FROM p320_07."Bookshelf" b WHERE collection_name = '{collection_name.strip()}' 
                                 AND b.user_id = {user_id}""")
                updated = True
                print(f"Successfully Changed Collection name from {collection_name} to {new_name}")
                conn.commit()

    if not updated:
        print("You do not own this collection or it does not exist!")

        
def read(conn, curs, tokens, user_id):
    # Invalid if the inputted number of tokens is incorrect
    if len(tokens) != 4:
        print('Invalid entry; incorrect number of tokens')
        return -1

    # Invalid if book id is not an integer
    book_id = tokens[1]
    try:
        book_int = int(book_id)
    except:
        print('Invalid entry; book id must be an integer')
        return -1

    if tokens[2].lower() == 'start':
        start_reading(conn, curs, tokens, user_id)
    elif tokens[2].lower() == 'stop':
        stop_reading(conn, curs, tokens, user_id)
    else:
        print('Invalid entry; must say "start" or "stop" as the third token')
        return -1

      
def start_reading(conn, curs, tokens, user_id):
    book_id = tokens[1]
    start_page = tokens[3]

    # Invalid if the starting page is not an integer
    try:
        start_int = int(start_page)
    except:
        print('Invalid entry; page must be an integer')
        return -1

    # Invalid if the starting page is negative
    if start_int < 0:
        print('Invalid entry; page must be positive')
        return -1

    # Invalid if selected book does not exist
    curs.execute("""SELECT * FROM p320_07."Book" WHERE book_id = %s""",
                 (book_id,))
    data = curs.fetchall()
    if len(data) == 0:
        print('Invalid entry; book does not exist')
        return -1

    # Invalid if ongoing reading session exists on that book
    curs.execute("""SELECT * FROM p320_07."Reads" 
                WHERE user_id = %s AND book_id = %s AND end_time IS NULL;""",
                 (user_id, book_id))
    data = curs.fetchall()
    if len(data) > 0:
        print('Invalid entry; A reading session for this book and user already exists.')
        return -1

    # Valid, create a new reading session with null ending values
    start_time = datetime.datetime.now()
    curs.execute("""INSERT INTO p320_07."Reads"
                (user_id, book_id, start_time, end_time, start_page, end_page)
                VALUES (%s, %s, %s, NULL, %s, NULL);""",
                 (user_id, book_id, start_time, start_int))

    conn.commit()
    print("Started reading session at page %s" % start_page)

    
def stop_reading(conn, curs, tokens, user_id):
    book_id = tokens[1]
    end_page = tokens[3]

    # Invalid if there doesn't exist a reading session with the user and book
    # Invalid if there are multiple reading sessions with the user and book
    curs.execute("""SELECT start_page FROM p320_07."Reads" 
                WHERE user_id = %s AND book_id = %s AND end_page IS NULL""",
                (user_id, book_id))
    data = curs.fetchall()
    if len(data) == 0:
        print('Invalid entry; reading session for book has not been started yet')
        return -1
    if len(data) > 1:
        print('Invalid entry; too many reading sessions for book (fix directly by deleting one)')
        return -1

    start_page = data[0][0]

    # Invalid if the starting page or the ending page are not integers
    try:
        start_int = int(start_page)
        end_int = int(end_page)
    except:
        print('Invalid entry; page must be an integer')
        return -1

    # Invalid if the ending page is negative
    if end_int < 0:
        print('Invalid entry; page must be positive')
        return -1
      
    # Valid, update the reading session with new ending values
    end_time = datetime.datetime.now()
    curs.execute("""UPDATE p320_07."Reads"
                SET end_time = %s, end_page = %s WHERE user_id = %s AND book_id = %s AND end_time IS NULL;""",
                (end_time, end_int, user_id, book_id))

    conn.commit()
    print("Stopped reading session, pages %s->%s" % (start_int, end_int))

    
def read_random(conn, curs, tokens, user_id):
    # Invalid if collection id is not an integer
    collection_id = tokens[1]
    try:
        collection_int = int(collection_id)
    except:
        print('Invalid entry; collection id must be an integer')
        return -1

    # Invalid if selected collection does not exist
    curs.execute("""SELECT * FROM p320_07."Collection" WHERE collection_id = %s""",
                 (collection_int,))
    data = curs.fetchall()
    if len(data) == 0:
        print('Invalid entry; collection does not exist')
        return -1

    # Invalid if no books exist in the collection
    curs.execute("""SELECT * FROM p320_07."CollectionContains" WHERE collection_id = %s""",
                 (collection_int,))
    data = curs.fetchall()
    if len(data) == 0:
        print('Invalid entry; no books exist in collection')
        return -1

    # Valid, select random book from collection until it doesn't already have an ongoing reading session
    valid_book_found = False
    rate_limit = 0
    book_id = 0
    while not valid_book_found and rate_limit < 100:
        curs.execute("""SELECT book_id FROM p320_07."CollectionContains" WHERE collection_id = %s
                                ORDER BY RANDOM() LIMIT 1;""", (collection_int,))
        result = curs.fetchall()

        book_id = result[0][0]

        # Invalid if ongoing reading session exists on that book
        curs.execute("""SELECT * FROM p320_07."Reads" 
                        WHERE user_id = %s AND book_id = %s AND end_time IS NULL;""",
                     (user_id, book_id))
        data = curs.fetchall()
        if len(data) == 0:
            valid_book_found = True
        rate_limit = rate_limit + 1

    if rate_limit >= 100:
        print('Invalid entry; all books in collection are already being read')
    else:
        # Create a new reading session with null ending values and default start page of 0
        start_time = datetime.datetime.now()
        curs.execute("""INSERT INTO p320_07."Reads"
                        (user_id, book_id, start_time, end_time, start_page, end_page)
                        VALUES (%s, %s, %s, NULL, %s, NULL);""",
                     (user_id, book_id, start_time, 0))
        print("Started reading session of book %s at page %s" % (book_id, 0))

    conn.commit()

    
def rate(conn, curs, tokens, user_id):
    # Invalid if the inputted number of tokens is incorrect
    if len(tokens)!=3:
        print('Invalid entry; incorrect number of tokens')
        return -1

    book_id = tokens[1]
    rating = tokens[2]

    # Invalid if book id or rating are not integers
    try:
        book_int = int(book_id)
        rating_int = int(rating)
    except:
        print('Invalid entry; book id and rating must be integers')
        return -1

    # Invalid if selected book does not exist
    curs.execute("""SELECT * FROM p320_07."Book" WHERE book_id = %s""",
                 (book_int,))
    data = curs.fetchall()
    if len(data) == 0:
        print('Invalid entry; book does not exist')
        return -1

    # Invalid if rating is out of bounds
    if rating_int < 0 or rating_int > 5:
        print('Invalid entry; rating must be between 0 and 5 (inclusive)')
        return -1

    # Valid, get whether or not a rating already exists for the book
    curs.execute("""SELECT * FROM p320_07."Rates" 
                WHERE user_id = %s AND book_id = %s""",
                 (user_id, book_int))
    data = curs.fetchall()
    # If rating does not exist, create it
    if len(data) == 0:
        curs.execute("""INSERT INTO p320_07."Rates"
                        (book_id, rating, user_id)
                        VALUES (%s, %s, %s);""",
                     (book_int, rating_int, user_id))
        print("Rated book %s with %s stars" % (book_int, rating_int))
    # Otherwise, update it
    else:
        curs.execute("""UPDATE p320_07."Rates"
                        SET rating = %s WHERE user_id = %s AND book_id = %s;""",
                     (rating_int, user_id, book_int))
        print("Updated rating of book %s to %s stars" % (book_int, rating_int))
    conn.commit()

def test(conn, curs):
    # for when you want to test stuff quickly
    curs.execute("""SELECT user_id,username,password FROM p320_07."Reader";""")
    data = curs.fetchall()
    users = dict()
    for user in data:
        users[user[1]] = [user[0],user[2]]

    print(users)