import psycopg2
from sshtunnel import SSHTunnelForwarder

import credentials

password = credentials.password
username = credentials.username


def connect_to_db():
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


def main():
    server, conn, curs = connect_to_db()

    curs.execute("""SELECT * FROM p320_07."Book";""")
    print(curs.fetchall())

    close(server, conn, curs)


if __name__ == '__main__':
    main()
