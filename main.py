import credentials
password = credentials.password
username = credentials.username

from functionality import*

def main():
    server, conn, curs = connect_to_db(username, password)


    print('Welcome to the Library, how can we help? ("help" for options)')
    user_id = -1
    while True:
        user_in = input('>').strip()
        tokens = user_in.split(" ")
        command = tokens[0]

        if command == "test":
            test(conn,curs)
        elif command == "help":
            help()
        elif command == "quit":
            print('Thanks for visiting!')
            break
        elif command == "logout":
            print("Logged out")
            user_id = -1


        elif command == "makeaccount":
            user_id = makeaccount(conn,curs,tokens)
        elif command == "login":
            user_id = login(conn, curs, tokens)
        elif command == "addfriend":
            if user_id < 0: print("Not logged in")
            else:addfriend(conn, curs, user_id, tokens)
        elif command == "removefriend":
            if user_id < 0: print("Not logged in")
            else: removefriend(conn, curs, user_id, tokens)
        elif command == "finduser":
            if user_id < 0: print("Not logged in")
            else: finduser(conn, curs, tokens)

        else:
            print('Invalid command')



    close(server, conn, curs)


if __name__ == '__main__':
    main()
