import psycopg2
from sshtunnel import SSHTunnelForwarder
import datetime
import random
from collections import defaultdict
import hashlib

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


def help(user_id):
    if(user_id == -1):
        print('Below are valid commands and their uses\n'
              '========= BASIC =========\n'
              'help: displays this information regardless of menu\n'
              'quit: exits the program regardless of menu\n'
              '========= ACCOUNTS =========\n'
              'makeaccount: makes a new account\n'
              'login: logs in if username and password match database entry\n'
              '========= BOOKS =========\n'
              'search: find any book\n'
              )
    else:
        print('Below are valid commands and their uses\n'
              '========= BASIC =========\n'
              'help: displays this information regardless of menu\n'
              'quit: exits the program regardless of menu\n'
              '========= ACCOUNTS =========\n'
              'makeaccount: makes a new account\n'
              'login: logs in if username and password match database entry\n'
              'logout: logs out of current account\n'
              
              '========= FRIENDS =========\n'
              'addfriend: adds user to friends list\n'
              'removefriend: removes friend from friends list\n'
              'finduser: returns users with similar email\n'
              
              '========= COLLECTIONS =========\n'
              'createcollection: creates a collection with a name\n'
              'deletecollection: deletes entered collection from database\n'
              'viewcollections: views all collections of the logged in user\n'
              'editcollectionname: edits entered collection name to entered new name\n'
              'addbook: adds a book to the collection\n'
              'removebook: removes a book from a collection\n'
              
              '========= BOOKS =========\n'
              'search: find any book\n'
              'read: start or stop a book reading session given page number\n'
              'read random book: start reading a random book in a collection at page 0\n'
              'rate: rate a book between 1 and 5 stars\n'
              'recommend: gives various types of recommendations on books\n'
              
              '======== USER =========\n'
              'profile: see user profile with top books, number of collection, and friends'
              )

def makeaccount(conn, curs):

    username = input('Enter a username\n>').strip()

    curs.execute("""SELECT username FROM p320_07."Reader";""")
    data = curs.fetchall()
    usernames = [row[0] for row in data]
    if username in usernames:
        print("That username is taken")
        return -1

    password = input('Enter a password\n>').strip()
    email = input('Enter your email\n>').strip()
    fname = input('Enter your first name\n>').strip()
    lname = input('Enter your last name\n>').strip()


    curs.execute("""SELECT MAX(user_id) FROM p320_07."Reader";""")
    data = curs.fetchall()

    next_id = data[0][0] + 1
    current_date = datetime.datetime.now()

    salt = "wtf is pdm"
    salted_pass = password+salt
    hashed = hashlib.md5(salted_pass.encode()).hexdigest()


    # print(username, password, email, fname, lname, next_id)

    curs.execute("""INSERT INTO p320_07."Reader"
        (user_id, username, password, email, first_name, last_name, created_date, last_access)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s);""",
                 (next_id, username, hashed, email, fname, lname, current_date, current_date))

    conn.commit()
    print("New account created and logged in")
    return next_id


def login(conn, curs):

    username = input("Enter your username: ")
    password = input("Enter your password: ")

    curs.execute("""SELECT user_id,username,password FROM p320_07."Reader";""")
    data = curs.fetchall()
    users = dict()
    for user in data:
        users[user[1]] = [user[0], user[2]]

    salt = "wtf is pdm"
    salted_pass = password + salt
    hashed = hashlib.md5(salted_pass.encode()).hexdigest()

    if username not in users or users[username][1] != hashed:
        print("Username doesn't exist or wrong password")
        return -1

    user_id = users[username][0]
    curs.execute("""UPDATE p320_07."Reader" SET last_access = %s WHERE user_id = %s;""",
                 (datetime.datetime.now(), user_id))
    conn.commit()
    print("Logged in")
    return user_id


def addfriend(conn, curs, passed_user_id):

    friend_username = input("Enter the username you want to follow: ")
    friend_id = -1

    curs.execute("""SELECT user_id, username FROM p320_07."Reader";""")
    reader_data = curs.fetchall()
    for reader in reader_data:
        if friend_username == reader[1]: friend_id = reader[0]

    if friend_id == -1:
        print("There is no user with that username")
        return -1

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


def removefriend(conn, curs, passed_user_id):

    friend_username = input("Enter the username of the friend you want to delete: ")
    friend_id_input = -1

    curs.execute("""SELECT user_id, username FROM p320_07."Reader";""")
    reader_data = curs.fetchall()
    for reader in reader_data:
        if friend_username == reader[1]: friend_id_input = reader[0]

    if friend_id_input == -1:
        print("There is no user with that username")
        return -1

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

def display_user_profile(curs, user_id):

    choose_profile = input("Do you want to look at your profile (1) or someone else's (2): ")

    if choose_profile == "1":
        curs.execute("""SELECT COUNT(*) From p320_07."Bookshelf" B WHERE B.user_id = %s""",
                     (user_id,))
        collection_number_query = curs.fetchall()
        collection_number = collection_number_query[0][0]

        curs.execute("""Select R.username from p320_07."Reader" R Join p320_07."Friendship" F
                        ON R.user_id = F.friend_id Where F.user_id = %s""", (user_id,))
        following_query = curs.fetchall()
        following = ""

        for follow in following_query:
            following += f"{follow[0]}\n\t"

        curs.execute("""Select R.username from p320_07."Reader" R Join p320_07."Friendship" F
                            ON R.user_id = F.user_id Where F.friend_id = %s""", (user_id,))
        follower_query = curs.fetchall()
        followers = ""

        for follower in follower_query:
            followers += f"{follower[0]}\n\t"

        curs.execute("""Select B.title, R.rating from p320_07."Book" B INNER JOIN p320_07."Rates" R ON
                        B.book_id = R.book_id where R.user_id = %s ORDER BY R.rating DESC""", (user_id,))
        top_books_query = curs.fetchall()
        top_ten_books = ""
        i = 1
        for books in top_books_query:
            if i <= 10:
                top_ten_books += f"\t{i}: {books[0]}\n"
                i += 1

        print(f"You have {collection_number} collections")
        print(f"Your are following:\n\t{following.strip()}")
        print(f"You are followed by:\n\t{followers.strip()}")
        print(f"Your top ten books are:\n\t{top_ten_books.strip()}")

    elif choose_profile == "2":
        profile_username = input("Enter the username of the profile you want to look at: ")
        profile_id = -1

        curs.execute("""SELECT user_id, username FROM p320_07."Reader";""")
        reader_data = curs.fetchall()
        for reader in reader_data:
            if profile_username == reader[1]: profile_id = reader[0]
        if profile_id == -1:
            print("There is no user with that username")
            return -1

        curs.execute("""SELECT COUNT(*) From p320_07."Bookshelf" B WHERE B.user_id = %s""",
                    (profile_id,))
        collection_number_query = curs.fetchall()
        collection_number = collection_number_query[0][0]

        curs.execute("""Select R.username from p320_07."Reader" R Join p320_07."Friendship" F
                                ON R.user_id = F.friend_id Where F.user_id = %s""", (profile_id,))
        following_query = curs.fetchall()
        following = ""

        for follow in following_query:
            following += f"{follow[0]}\n\t"

        curs.execute("""Select R.username from p320_07."Reader" R Join p320_07."Friendship" F
                                    ON R.user_id = F.user_id Where F.friend_id = %s""", (profile_id,))
        follower_query = curs.fetchall()
        followers = ""

        for follower in follower_query:
            followers += f"{follower[0]}\n\t"

        curs.execute("""Select B.title, R.rating from p320_07."Book" B INNER JOIN p320_07."Rates" R ON
                                B.book_id = R.book_id where R.user_id = %s ORDER BY R.rating DESC""", (profile_id,))
        top_books_query = curs.fetchall()
        top_ten_books = ""
        i = 1
        for books in top_books_query:
            if i <= 10:
                top_ten_books += f"\t{i}: {books[0]}\n"
                i += 1
        print(f"=========================================")
        print(f"{profile_username}'s PROFILE")
        print(f"=========================================")
        print(f"\n{profile_username} has {collection_number} collections")
        print(f"{profile_username} is following:\n\t{following.strip()}")
        print(f"{profile_username} is followed by:\n\t{followers.strip()}")
        print(f"{profile_username}'s top books (capped at 10) are:\n\t{top_ten_books.strip()}")

    else:
        print("you must input at 1 or a 2")




def finduser(conn, curs):

    email = input("Enter the email of the user you want to find: ")
    curs.execute("""SELECT username,email FROM p320_07."Reader" WHERE user_id IN 
            (SELECT user_id FROM p320_07."Reader" WHERE email LIKE %s);""", ('%%' + email + '%%',))
    data = curs.fetchall()
    print('Username\t\tEmail')
    for user in data: print(f'{user[0]}\t\t{user[1]}')

def friends(conn, curs, user_id):
    curs.execute("""SELECT username FROM p320_07."Reader" WHERE user_id IN 
                (SELECT friend_id FROM p320_07."Friendship" WHERE user_id = %s);""", (user_id,))
    data = curs.fetchall()
    print(data)


def create_collection(conn, curs, user_id):
    # get the whole name including spaces
    name = input("Enter the name of your collection: ")

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


def add_to_collection(conn, curs, user_id):
    # get book user wants to add and the name of the collection,
    add_book = int(input("Enter the bookID number: "))
    collection_name = input("Enter the name of the collection you want to add the book to: ")

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


def delete_from_collection(conn, curs, user_id):
    # get book user wants to remove and the name of the collection,
    remove_book = int(input("Enter the bookID number: "))
    collection_name = input("Enter the name of the collection you want to delete the book to: ")

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


def read(conn, curs, user_id):
    # Invalid if the inputted number of tokens is incorrect

    # Invalid if book id is not an integer
    book_id = input("Enter Book ID: ")
    try:
        book_int = int(book_id)
    except:
        print('Invalid entry; book id must be an integer')
        return -1

    decision = input("input start if you want to start reading or input stop if you want to stop reading: ")

    if decision == 'start':
        start_reading(conn, curs, book_id, user_id)
    elif decision == 'stop':
        stop_reading(conn, curs, book_id, user_id)
    else:
        print('Invalid entry; must say "start" or "stop" as the third token')
        return -1


def start_reading(conn, curs, book_id, user_id):
    start_page = input("Enter the page you are starting on: ")

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


def stop_reading(conn, curs, book_id, user_id):
    end_page = input("enter the page number you finished on: ")

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


def read_random(conn, curs, user_id):
    # Invalid if collection id is not an integer
    collection_id = input("enter the collection id: ")
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


def rate(conn, curs, user_id):
    # Invalid if the inputted number of tokens is incorrect

    book_id = input("enter the book ID: ")
    rating = input("enter your rating: ")

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

def foryou(conn, curs, user_id):
    curs.execute("""
                        SELECT book_id
                        FROM p320_07."Reads"
                        WHERE user_id = %s
                     """, (user_id,))
    books_read = curs.fetchall()
    if not books_read:
        print('Invalid entry; you must read a book first')
        return -1
    # Find genres from books in read history
    curs.execute("""
        SELECT g.name, g.genre_id, COUNT(*) AS genre_count
        FROM p320_07."Reads" r
        INNER JOIN p320_07."Book" b ON r.book_id = b.book_id
        INNER JOIN p320_07."Genre" g ON b.genre_id = g.genre_id
        WHERE r.user_id = %s
        GROUP BY g.name, g.genre_id
        ORDER BY genre_count DESC
    """,(user_id,))

    top_genres = curs.fetchall()

    top_genre_id = top_genres[0][1]
    curs.execute("""
                    SELECT rd.user_id, COUNT(*) AS session_count
                    FROM p320_07."Reader" rd
                    INNER JOIN p320_07."Reads" r ON rd.user_id = r.user_id
                    INNER JOIN p320_07."Book" b ON r.book_id = b.book_id
                    WHERE b.genre_id = %s
                    GROUP BY rd.user_id
                    ORDER BY session_count DESC
                    LIMIT 5;
                """, (top_genre_id,))
    similar_users = curs.fetchall()

    # Initialize a dictionary to count how many times each book has been read by similar users
    book_read_counts = defaultdict(int)

    # Loop over similar users and collect books they've read in the favorite genre
    for user in similar_users:
        user_id_temp = user[0]  # Assuming the first element is the user ID
        curs.execute("""
                        SELECT b.title, b.book_id
                        FROM p320_07."Book" b
                        INNER JOIN p320_07."Reads" r ON b.book_id = r.book_id
                        WHERE r.user_id = %s
                     """, (user_id_temp,))
        books = curs.fetchall()
        for book in books:
            # Increment the count for each book read by a similar user
            book_read_counts[book[1]] += 1

    # Filter out books the current user has already read
    curs.execute("""
                    SELECT b.title, b.book_id
                    FROM p320_07."Book" b
                    INNER JOIN p320_07."Reads" r ON b.book_id = r.book_id
                    WHERE r.user_id = %s
                 """, (user_id,))
    books_read_by_current_user = {book[0] for book in curs.fetchall()}

    common_unread_books = {book_id
                           for book_id, count in book_read_counts.items()
                           if book_id not in books_read_by_current_user}

    # Fetch details of these common, unread books
    if common_unread_books:
        placeholders = ', '.join(['%s'] * len(common_unread_books))
        curs.execute(f"""
                        SELECT title, book_id
                        FROM p320_07."Book"
                        WHERE book_id IN ({placeholders})
                     """, tuple(common_unread_books))
        recommended_books = curs.fetchall()

        num_books_to_display = min(5, len(recommended_books))
        books_to_display = random.sample(recommended_books, num_books_to_display)

        # Display the recommended books
        print(f"Here are books that users similar to you like:")
        for book in books_to_display:
            print(f"- {book[0]} (Book ID: {book[1]})")
    else:
        print("No common unread books found among users with similar tastes.")

def recommend(conn, curs, user_id):
    filter = input('Do you want: (t)rending, (c)ommon among followers, (n)ew, or personalized (f)or you?\n>')

    match filter.strip().lower():
        # trending
        case 't':
            # Display trending books
            curs.execute("""
                SELECT b.title, b.book_id, COUNT(*) AS session_count
                FROM p320_07."Reads" r
                INNER JOIN p320_07."Book" b ON r.book_id = b.book_id
                WHERE r.end_time > CURRENT_DATE - INTERVAL '90' day
                GROUP BY b.title, b.book_id
                ORDER BY session_count DESC
                LIMIT 20;
            """)

            top_books = curs.fetchall()

            # Print all top books
            if top_books:
                print("Top 20 books in the last 90 days:")
                # Pleasant string formatting
                i = 1
                max_title_length = max(len(b[0]) for b in top_books)
                max_id_length = max(len(str(b[1])) for b in top_books)
                for book in top_books:
                    print(f"#{i:2} - {book[1]:{max_id_length}}: {book[0]:{max_title_length}} ({book[2]} times read)")
                    i+=1
        # common among followers
        case 'c':
            # Display most popular books among people following me
            curs.execute("""
                SELECT b.title, b.book_id, COUNT(*) AS session_count
                FROM p320_07."Friendship" f
                INNER JOIN p320_07."Reads" r ON f.user_id = r.user_id
                INNER JOIN p320_07."Book" b ON r.book_id = b.book_id
                WHERE f.friend_id = %s
                GROUP BY b.title, b.book_id
                ORDER BY session_count DESC
                LIMIT 20;
            """,(user_id,))

            top_books = curs.fetchall()

            # Print more top books
            if top_books:
                print("Top 20 books among users following you:")
                # Pleasant string formatting
                i = 1
                max_title_length = max(len(b[0]) for b in top_books)
                max_id_length = max(len(str(b[1])) for b in top_books)
                for book in top_books:
                    print(f"#{i:2} - {book[1]:{max_id_length}}: {book[0]:{max_title_length}} ({book[2]} times read)")
                    i+=1
            else:
                print("You either have no users following you or they have not read any books!")
        # newly released
        case 'n':
            # Display most popular newly released books during this calendar month
            curs.execute("""
                    SELECT b.title, b.book_id, COUNT(*) AS session_count
                    FROM (
                        SELECT DISTINCT rel.book_id
                        FROM p320_07."Released" rel
                        WHERE EXTRACT(MONTH FROM rel.date) = EXTRACT(MONTH FROM CURRENT_DATE)
                        AND EXTRACT(YEAR FROM rel.date) = EXTRACT(YEAR FROM CURRENT_DATE)
                    ) AS distinct_books
                    INNER JOIN p320_07."Reads" r ON distinct_books.book_id = r.book_id
                    INNER JOIN p320_07."Book" b ON distinct_books.book_id = b.book_id
                    GROUP BY b.title, b.book_id
                    ORDER BY session_count DESC
                    LIMIT 5;
                """)

            top_books = curs.fetchall()

            # Print all top books
            if top_books:
                print("Top 5 newly released books in the current calendar month:")
                # Pleasant string formatting
                i = 1
                max_title_length = max(len(b[0]) for b in top_books)
                max_id_length = max(len(str(b[1])) for b in top_books)
                for book in top_books:
                    print(f"#{i:2} - {book[1]:{max_id_length}}: {book[0]:{max_title_length}} ({book[2]} times read)")
                    i += 1
        # for you page
        case 'f':
            foryou(conn, curs, user_id)
        case default:
            print("Invalid search command. You must enter t, c, n, or f")

def search(curs):
    filter = input('search for a book by (t)itle, (r)elease date, (a)uthors, (p)ublisher, (g)enre: ')
    keyword = input("add keyword(s): ")

    match filter:

        # title --------
        case 't':
            curs.execute(f"""SELECT DISTINCT p320_07."Book".book_id , p320_07."Book".title , p320_07."Released".date
            FROM p320_07."Book" JOIN p320_07."Released" ON p320_07."Book".book_id = p320_07."Released".book_id
            WHERE title LIKE '%{keyword}%' ORDER BY  p320_07."Book".title ASC, p320_07."Released".date ASC;""")
            querys = curs.fetchall()
            title_search = list()

            if len(querys) == 0:
                print("Could not find a Book with that Title!")
                return

            for query in querys:
                title_search.append((query[0],))

            print_book(curs, title_search)

        # release date --------
        case 'r':
            # not working properly, can only search by whole date YYYY-MM-DD
            curs.execute(f"""SELECT DISTINCT p320_07."Released".book_id, p320_07."Book".title, p320_07."Released".date
            FROM p320_07."Released" JOIN p320_07."Book"  
            ON p320_07."Released".book_id = p320_07."Book".book_id WHERE date = '{keyword}'
            ORDER BY  p320_07."Book".title ASC, p320_07."Released".date ASC;""")
            querys = curs.fetchall()
            released_search = list()

            if len(querys) == 0:
                print("Could not find a Book with that release date!")
                return

            for query in querys:
                released_search.append((query[0],))

            print_book(curs, released_search)

        # author --------
        case 'a':
            # get the first and last name separated
            # ALWAYS search for a first name, last name is not required
            first_name = keyword.split()[0]
            last_name = ''

            curs.execute(f"""SELECT DISTINCT  A.book_id , B.title, R.date 
                        FROM p320_07."Writes" A JOIN p320_07."Contributor" C 
                            ON A.contributor_id = C.contributor_id JOIN p320_07."Book" B
                            ON A.book_id = B.book_id JOIN p320_07."Released" R
                            ON A.book_id = R.book_id WHERE C.first_name LIKE '%{first_name}%' 
                            OR C.last_name LIKE '%{last_name}%' 
                            ORDER BY B.title ASC, R.date ASC;""")
            querys = curs.fetchall()
            author_search = list()

            if len(querys) == 0:
                print("Could not find a Author with that name!")
                return

            for query in querys:
                if (query[0],) in author_search:
                    pass
                else:
                    author_search.append((query[0],))
            # for all the collections the user made
            print_book(curs, author_search)

        # publisher --------
        case 'p':
            # get the first and last name separated
            # ALWAYS search for a first name, last name is NOT required
            first_name = keyword.split()[0]
            last_name = ''


            curs.execute(f"""SELECT P.book_id, B.title, R.date FROM p320_07."Publishes" P 
                            INNER JOIN p320_07."Contributor" C
                            ON P.contributor_id = C.contributor_id LEFT JOIN p320_07."Book" B
                            ON P.book_id = B.book_id LEFT JOIN p320_07."Released" R
                            ON P.book_id = R.book_id
                            WHERE C.first_name LIKE '%{first_name}%' 
                            OR C.last_name LIKE '%{last_name}%'
                            ORDER BY B.title ASC, R.date ASC;""")
            querys = curs.fetchall()
            publisher_search = list()

            if len(querys) == 0:
                print("Could not find a Publisher with that name!")
                return

            for query in querys:
                if (query[0],) in publisher_search:
                    pass
                else:
                    publisher_search.append((query[0],))

            print_book(curs, publisher_search)

        # genre --------
        case 'g':

            curs.execute(f"""SELECT B.book_id, B.title, R.date FROM p320_07."Book" B 
                            INNER JOIN p320_07."Genre" G 
                            ON B.genre_id = G.genre_id LEFT JOIN p320_07."Released" R
                            ON B.book_id = R.book_id
                            WHERE G.name LIKE '%{keyword}%'
                            ORDER BY B.title ASC, R.date ASC; """)
            querys = curs.fetchall()
            genre_search = list()

            if len(querys) == 0:
                print("Could not find a Genre with that name!")
                return

            for query in querys:
                if (query[0],) in genre_search:
                    pass
                else:
                    genre_search.append((query[0],))

            print_book(curs, genre_search)

        case default:
            print("Invalid search command. Enter a valid command:\n\t(t)itle, "
                  "(r)elease date, (a)uthors, (p)ublisher, (g)enre")

def print_book(curs, data):
    author_list = []
    publisher_list = []
    star_rating = None

    # AUTHOR ------------------------------------------------
    # get book id from data(above cursor fetches all return a list of book ids, which is data here)
    for id in data:
        for number in id:
            curs.execute(f"""SELECT contributor_id FROM p320_07."Writes" WHERE book_id ={number}""")
            authors = curs.fetchall()

            # get author(s) names
            for author in authors:
                for author_id in author:
                    curs.execute(f"""SELECT first_name, last_name FROM p320_07."Contributor" 
                                        WHERE contributor_id = {author_id}""")
                    authornames = curs.fetchall()

                    for names in authornames:
                        author_list.append(names[0] + " " + names[1] + " ")

            # PUBLISHERS ------------------------------------------------

            curs.execute(f"""SELECT contributor_id FROM p320_07."Publishes" WHERE book_id ={number}""")
            publishers = curs.fetchall()

            # get publisher(s) names
            for publisher in publishers:
                for publisher_id in publisher:
                    curs.execute(f"""SELECT first_name, last_name FROM p320_07."Contributor" 
                                        WHERE contributor_id = {publisher_id}""")
                    publishernames = curs.fetchall()

                    for names in publishernames:
                        publisher_list.append(names[0] + " " + names[1] + " ")

            # RATING ------------------------------------------------

            curs.execute(f"""SELECT AVG(rating) FROM p320_07."Rates" WHERE book_id ={number}""")
            rating = curs.fetchall()
            for rates in rating:
                for rate in rates:
                    star_rating = rate

        # printing information from book
        curs.execute(f"""SELECT * FROM p320_07."Book" WHERE book_id = {number}""")
        books = curs.fetchall()

        for book in books:
            print(f"Title: {book[1]}\nID: {book[0]}\nAudience: {book[2]}\nLength: {book[3]}")
        print("Author(s): ", author_list)
        print("Publisher(s): ", publisher_list)

        # making sure none doesn't get the 2 decimal places
        if star_rating is not None:
            print(f"Star Rating: {star_rating:.2f}\n")
        else:
            # will simply print None
            print(f"Star Rating: {star_rating}\n")

        # reset variables for next book
        author_list = []
        publisher_list = []
        star_rating = None