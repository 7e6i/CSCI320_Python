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
          'search filter keyword(s)\n\tsearch for a book by (t)itle, (r)elease date, (a)uthors, (p)ublisher, (g)enre\n'
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


def test(conn, curs):
    #for when you want to test stuff quickly
    curs.execute("""SELECT user_id,username,password FROM p320_07."Reader";""")
    data = curs.fetchall()
    users = dict()
    for user in data:
        users[user[1]] = [user[0],user[2]]
    print(users)

def search(curs, tokens):
    #add switch statement and parameter filter to search for certain things :)
    filter = tokens[1]
    keyword = ' '.join(tokens[2:])
    print ("filter ", filter)
    print("\nkeyword ", keyword)
    match filter:
        # title
        case 't':
            curs.execute(f"""SELECT * FROM p320_07."Book" WHERE title LIKE '%{keyword}%';""")
            title_search = curs.fetchall()
            for book in title_search:
                print(f"ID: {book[0]}, Title: {book[1]}, Audience: {book[2]}, Length: {book[3]}\n")

        # release date
        case 'r':
            # curs.execute(f"""SELECT * FROM p320_07."Released" WHERE date LIKE '%{keyword}%' AND book_id =
            #                 (SELECT book_id FROM p320_07."Book" WHERE ;""")
            curs.execute(f"""SELECT book_id FROM p320_07."Released" WHERE date LIKE '%{keyword}%'""")
        # author
        case 'a':
            # curs.execute(f"""SELECT * FROM p320_07."Writes" WHERE contributor_id IN
            #               (SELECT contributor_id FROM p320_07."Contributor" WHERE first_name LIKE '%{keyword}%');""")
            curs.execute(f"""SELECT A.book_id FROM p320_07."Writes" A INNER JOIN p320_07."Contributor" C 
                            ON A.contributor_id = C.contributor_id WHERE C.first_name LIKE '%{keyword}%'""")
            author_search = curs.fetchall()

            # for all the collections the user made
            for id in author_search:
                for number in id:
                    curs.execute(f"""SELECT * FROM p320_07."Book" WHERE book_id = {number}""")
                    data = curs.fetchall()
                    for book in data:
                        print(f"ID: {book[0]}, Title: {book[1]}, Audience: {book[2]}, Length: {book[3]}\n")

        # publisher
        case 'p':
            # curs.execute(f"""SELECT * FROM p320_07."Book" WHERE title LIKE '%{keyword}%';""")
            curs.execute(f"""SELECT P.book_id FROM p320_07."Publishes" P INNER JOIN p320_07."Contributor" C
                            ON P.contributor_id = C.contributor_id WHERE C.first_name LIKE '%{keyword}%'""")
            publisher_search = curs.fetchall()
            for id in publisher_search:
                for number in id:
                    curs.execute(f"""SELECT * FROM p320_07."Book" WHERE book_id = {number}""")
                    data = curs.fetchall()
                    for book in data:
                        print(f"ID: {book[0]}, Title: {book[1]}, Audience: {book[2]}, Length: {book[3]}\n")
        # genre
        case 'g':
            # curs.execute(f"""SELECT * FROM p320_07."Book" WHERE title LIKE '%{keyword}%';""")
            curs.execute(f"""SELECT B.book_id FROM p320_07."Book" B INNER JOIN p320_07."Genre" G 
                            ON B.genre_id = G.genre_id WHERE G.name LIKE '%{keyword}%'; """)
            genre_search = curs.fetchall()
            for id in genre_search:
                for number in id:
                    curs.execute(f"""SELECT * FROM p320_07."Book" WHERE book_id = {number}""")
                    data = curs.fetchall()
                    for book in data:
                        print(
                            f"ID: {book[0]}, Title: {book[1]}, Audience: {book[2]}, Length: {book[3]}\n")
