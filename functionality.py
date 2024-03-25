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
          'logout\n\tlogs out of current account'
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

    print("Logged in")
    return users[username][0]

def test(conn, curs):
    #for when you want to test stuff quickly
    curs.execute("""SELECT user_id,username,password FROM p320_07."Reader";""")
    data = curs.fetchall()
    users = dict()
    for user in data:
        users[user[1]] = [user[0],user[2]]



    print(users)