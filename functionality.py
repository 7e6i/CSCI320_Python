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
          'collection new|del name\n\tcreates or deletes collection with title name\n'
          'read bookid start|stop page\n\tstart or stop a book reading session given page number\n'
          'rate bookid rating\n\trate a book between 1 and 5 stars'
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
    username = tokens[1]
    password = tokens[2]

    if len(tokens)!=3:
        print('Invalid entry')
        return -1

    curs.execute("""SELECT user_id,username,password FROM p320_07."Reader";""")
    data = curs.fetchall()
    users = dict()
    for user in data:
        users[user[1]] = [user[0], user[2]]

    if username not in users or users[username][1] != password:
        print("Username doesn't exist or wrong password")
        return -1

    user_id = users[username][0]
    curs.execute("""UPDATE p320_07."Reader" SET last_access = %s WHERE user_id = %s;""",(datetime.datetime.now(),user_id))
    conn.commit()
    print("Logged in")
    return user_id

def collection(conn, curs, tokens):
    pass
def read(conn, curs, tokens, user_id):
    # Invalid if the inputted number of tokens is incorrect
    if len(tokens)!=4:
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
                SET end_time = %s, end_page = %s WHERE user_id = %s AND book_id = %s;""",
                (end_time, end_int, user_id, book_id))

    conn.commit()
    print("Stopped reading session, pages %s->%s" % (start_int, end_int))

# still need to add
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
        print('Invalid entry; book id must be an integer')
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
    #for when you want to test stuff quickly
    curs.execute("""SELECT user_id,username,password FROM p320_07."Reader";""")
    data = curs.fetchall()
    users = dict()
    for user in data:
        users[user[1]] = [user[0],user[2]]

    print(users)