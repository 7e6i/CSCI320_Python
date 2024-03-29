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


def makeaccount(conn, curs, tokens):
    if len(tokens) != 6:
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

    # print(username, password, email, fname, lname, next_id)

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

    if len(tokens) != 3:
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
    curs.execute("""UPDATE p320_07."Reader" SET last_access = %s WHERE user_id = %s;""",
                 (datetime.datetime.now(), user_id))
    conn.commit()
    print("Logged in")
    return user_id


def collection(conn, curs, tokens):
    pass


def test(conn, curs):
    # for when you want to test stuff quickly
    curs.execute("""SELECT user_id,username,password FROM p320_07."Reader";""")
    data = curs.fetchall()
    users = dict()
    for user in data:
        users[user[1]] = [user[0], user[2]]
    print(users)


def search(curs, tokens):
    filter = tokens[1]
    keyword = ' '.join(tokens[2:])

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

            if len(tokens) > 3:
                last_name = keyword.split()[1]

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

            if len(tokens) > 3:
                last_name = keyword.split()[1]

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
                print("Could not find a Publisher with that name!")
                return

            for query in querys:
                if (query[0],) in genre_search:
                    pass
                else:
                    genre_search.append((query[0],))

            print_book(curs, genre_search)


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
            print(f"Star Rating: {star_rating}")

        # reset variables for next book
        author_list = []
        publisher_list = []
        star_rating = None
