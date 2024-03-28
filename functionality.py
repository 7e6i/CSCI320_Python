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
          'makeaccount username password email firstname lastname\n\tmakes a new account with specified info\n'
          'login username password\n\tlogs in if username and password match database entry\n'
          'logout\n\tlogs out of current account\n'
          'createcollection name \n\tcreates a collection with a name\n'
          'addbook bookid collection name \n\tadds a book to the collection\n'
          'removebook bookid collection name \n\tremoves a book from a collection\n'
          'addfriend username\n\tadds user to friends list\n'
          'removefriend username\n\tremoves friend from friends list\n'
          'finduser email\n\treturns users with similar email'

          )

def makeaccount(conn,curs, tokens):

    if len(tokens)!=6:
        print('Invalid entry')
        return -1

    #print(tokens[1:])

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




def create_collection(conn, curs, tokens, user_id):
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



def test(conn, curs):
    #for when you want to test stuff quickly
    curs.execute("""SELECT user_id,username,password FROM p320_07."Reader";""")
    data = curs.fetchall()
    users = dict()
    for user in data:
        users[user[1]] = [user[0],user[2]]

    print(users)