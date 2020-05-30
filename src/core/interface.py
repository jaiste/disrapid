import mysql.connector as mysql
import logging

class InterfaceHandler:
    # This represents the interface to connect with the mysql database
    #
    def __init__(self, *args, **kwargs):
        # connect to the database
        try:
            host = kwargs.pop('host')
            name = kwargs.pop('name')
            dbpass = kwargs.pop('dbpass')
            user = kwargs.pop('user')

            self._db = mysql.connect(host=host, user=user, passwd=dbpass, database=name)
            self._cursor = self._db.cursor(dictionary=True)

            # set autocommit 1
            self._cursor.execute("SET AUTOCOMMIT=1;")
            self._cursor.execute("COMMIT;")

        except Exception as e:
            logging.fatal(f'db connection failed because of {e}')
        
    def gettestmessage(self, guild_id):
        try:
            query = f"SELECT * FROM testmessages WHERE id={guild_id};"

            self._cursor.execute(query)
            result = self._cursor.fetchone()

            if not result:
                raise Exception(f'no guild id found')

            return result

        except Exception as e:
            logging.warning(e)
            return None