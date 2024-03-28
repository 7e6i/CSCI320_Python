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
            curs.execute(f"""SELECT book_id FROM p320_07."Released" WHERE date LIKE '%{keyword}%'""")

        # author
        case 'a':
            # get the first and last name separated
            # ALWAYS search for a first name, last name is not required
            first_name = keyword.split()[0]
            last_name = ''
            if len(tokens) > 3:
                last_name = keyword.split()[1]

            curs.execute(f"""SELECT A.book_id FROM p320_07."Writes" A INNER JOIN p320_07."Contributor" C 
                            ON A.contributor_id = C.contributor_id WHERE C.first_name LIKE '%{first_name}%' 
                            OR C.last_name LIKE '%{last_name}%';""")
            author_search = curs.fetchall()

            # for all the collections the user made
            print_book(curs,author_search)

        # publisher
        case 'p':
            # curs.execute(f"""SELECT * FROM p320_07."Book" WHERE title LIKE '%{keyword}%';""")
            curs.execute(f"""SELECT P.book_id FROM p320_07."Publishes" P INNER JOIN p320_07."Contributor" C
                            ON P.contributor_id = C.contributor_id WHERE C.first_name LIKE '%{keyword}%'""")
            publisher_search = curs.fetchall()
            print_book(curs,publisher_search)
        # genre
        case 'g':
            # curs.execute(f"""SELECT * FROM p320_07."Book" WHERE title LIKE '%{keyword}%';""")
            curs.execute(f"""SELECT B.book_id FROM p320_07."Book" B INNER JOIN p320_07."Genre" G 
                            ON B.genre_id = G.genre_id WHERE G.name LIKE '%{keyword}%'; """)
            genre_search = curs.fetchall()
            print_book(curs,genre_search)


def print_book(curs, data):
    author_list = []
    publisher_list = []

    # AUTHOR ------------------------------------------------
    # get book contributor information first for AUTHOR
    for id in data:
        for number in id:
            curs.execute(f"""SELECT contributor_id FROM p320_07."Writes" WHERE book_id ={number}""")
            authors = curs.fetchall()

            # get author(s) names
            for author in authors:
                for author_id in author:
                    curs.execute(f"""SELECT first_name, last_name FROM p320_07."Contributor" WHERE contributor_id = {author_id}""")
                    authornames = curs.fetchall()
                    for names in authornames:
                        author_list.append(names[0] + " " + names[1] + " ")

            print("Author(s): ", author_list)

     # PUBLISHERS ------------------------------------------------
    for id in data:
        for number in id:
            curs.execute(f"""SELECT contributor_id FROM p320_07."Publishes" WHERE book_id ={number}""")
            publishers = curs.fetchall()

            # get publisher(s) names
            for publisher in publishers:
                for publisher_id in publisher:
                    curs.execute(
                        f"""SELECT first_name, last_name FROM p320_07."Contributor" WHERE contributor_id = {publisher_id}""")
                    publishernames = curs.fetchall()
                    for names in publishernames:
                        publisher_list.append(names[0] + " " + names[1] + " ")

            print("Publisher(s): ", publisher_list)

            current_rate = 0
            # RATING ------------------------------------------------
            for id in data:
                for number in id:
                    curs.execute(f"""SELECT AVG(rating) FROM p320_07."Rates" WHERE book_id ={number}""")
                    rating = curs.fetchall()
                    print("Rating: ", rating)

                    for rates in rating:
                        print ("Rates: ", rates)

                        for rate in rates:
                            print ("rate: ", rate)
                            print("number of ratings: ", len(rating))



                        # for rate_number in rate:
                        #     print("ratenumber: ", rate_number)
                    #         curs.execute(
                    #             f"""SELECT first_name, last_name FROM p320_07."Contributor" WHERE contributor_id = {publisher_id}""")
                    #         rated = curs.fetchall()
                    #         for stars in rated:
                    #             print("stars: ", stars)
                    #
                    # print("Publisher(s): ", publisher_list)



            curs.execute(f"""SELECT * FROM p320_07."Book" WHERE book_id = {number}""")
            books = curs.fetchall()
            for book in books:
                print(
                    f"ID: {book[0]}, Title: {book[1]}, Audience: {book[2]}, Length: {book[3]}\n")
