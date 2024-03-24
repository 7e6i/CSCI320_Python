import credentials
password = credentials.password
username = credentials.username

from functionality import*

def main():
    #server, conn, curs = connect_to_db(username, password)


    print('Welcome to the Library, how can we help? ("help" for options)')
    while True:
        user_in = input('>').strip()
        tokens = user_in.split(" ")
        command = tokens[0]

        if command == "help":
            help()
        elif command == "quit":
            print('Thanks for visiting!')
            break
        elif command == "makeaccount":
            makeaccount(tokens)
        else:
            print('Invalid command')

    # curs.execute("""SELECT * FROM p320_07."Book";""")
    # print(curs.fetchall())

    #close(server, conn, curs)


if __name__ == '__main__':
    main()
