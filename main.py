import credentials
password = credentials.password
username = credentials.username

from functionality import *

def main():
    server, conn, curs = connect_to_db(username, password)

    print('Welcome to the Library, how can we help? ("help" for options)')
    user_id = -1
    while True:

        user_in = input('>').strip()
        tokens = user_in.split(" ")
        command = tokens[0]

        if command == "help":
            help(user_id)
        elif command == "quit":
            print('Thanks for visiting!')
            break
        elif command == "logout":
            print("Logged out")
            user_id = -1

        elif command == "makeaccount":
            user_id = makeaccount(conn,curs)

        elif command == "login":
            user_id = login(conn, curs)

        elif command == "finduser":
            if user_id < 0:
                print("Not logged in")
            else:
                finduser(conn, curs)

        elif command == "addfriend":
            if user_id < 0:
                print("Not logged in")
            else:
                addfriend(conn, curs, user_id)
                
        elif command == "removefriend":
            if user_id < 0:
                print("Not logged in")
            else:
                removefriend(conn, curs, user_id)
                
        elif command == "friends":
            if user_id < 0:
                print("Not logged in")
            else:
                friends(conn, curs, user_id)
             
        elif command == "createcollection":
            if user_id<0:
                print("Not logged in")
            else:
                create_collection(conn, curs, user_id)
                print(f"\nCollection was successfully created!")

        elif command == "addbook":
            if user_id < 0:
                print("Not logged in")
            else:
                add_to_collection(conn, curs, user_id)

        elif command == "removebook":
            if user_id < 0:
                print("Not logged in")
            else:
                delete_from_collection(conn, curs, user_id)

        elif command == "deletecollection":
            if user_id < 0:
                print("Not logged in")
            else:
                delete_collection(conn, curs, user_id)

        elif command == "viewcollections":
            if user_id < 0:
                print("Not logged in")
            else:
                view_collections(curs, user_id)

        elif command == "editcollectionname":
            if user_id < 0:
                print("Not logged in")
            else:
                edit_collection_name(conn, curs, user_id)
        
        elif command == "read":
            if user_id<0:
                print("Not logged in")
            else:
                read(conn,curs,user_id)

        elif command == "read random book":
            if user_id<0:
                print("Not logged in")
            else:
                read_random(conn, curs, user_id)
                
        elif command == "rate":
            if user_id<0:
                print("Not logged in")
            else:
                rate(conn,curs,user_id)

        elif command == "recommend":
            if user_id<0:
                print("Not logged in")
            else:
                recommend(conn,curs,user_id)
                
        elif command == "search":
            search(curs)

        elif command == "profile" and user_id != -1:
            if user_id != -1:
                display_user_profile(curs, user_id)
            else:
                print("Not logged in")
            
        else:
            print('Invalid command')

    close(server, conn, curs)
        
if __name__ == '__main__':
    main()