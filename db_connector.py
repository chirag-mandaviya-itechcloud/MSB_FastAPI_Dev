import psycopg2
import urllib.parse
import os

connection =None

encoded_password = urllib.parse.quote("password")
# Your database URL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:"+encoded_password+"@localhost/Demo")
#DATABASE_URL = os.getenv("DATABASE_URL","postgres://u7jfrk63ausn8k:p014f4d8f0fe7e5cc5f87f41198334444ffbee619def85d6325b3aa1b79955d9b@ec2-18-203-50-109.eu-west-1.compute.amazonaws.com:5432/dcrm7eal8kqfkb")
connection = None
def initialize_database():
    try:
        connection = psycopg2.connect(DATABASE_URL)
        cursor = connection.cursor()

        # Iterate over all SQL script files and execute them
        SQL_SCRIPT_FOLDER = os.path.join(os.path.dirname(__file__), "tablescripts")
        for script_filename in os.listdir(SQL_SCRIPT_FOLDER):
            if script_filename.endswith(".sql"):
                script_path = os.path.join(SQL_SCRIPT_FOLDER, script_filename)
                with open(script_path, "r") as script_file:
                    cursor.execute(script_file.read())

    except psycopg2.Error as e:
        print(f"Database error: {e}")
        # Handle database errors and return appropriate HTTP response or raise an exception
    finally:
        connection.commit()
        cursor.close()
    
    return connection

db_connection = initialize_database()
connection= db_connection

