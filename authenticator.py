import hashlib
import json
from fastapi import FastAPI, Request, Depends, APIRouter

router = APIRouter()

# Function to verify password
def verify_password(input_password, salt, bp_number, db_connection):
    try:
        # Create a cursor to execute SQL queries using the existing connection
        cursor = db_connection.cursor()
        # Fetch the original_password from the "CREDENTIALS" table based on bp_number
        # print("hey" + bp_number)
        query = """
        SELECT "ENCP_PASSWORD" FROM public."MSB_CREDENTIAL" WHERE "BP_NUMBER" = %s
        AND ( "EXPIRED" = 'F' OR "EXPIRED" = 'N')
        """
        cursor.execute(query, (bp_number,))
        result = cursor.fetchone()
        passw = str(result[0]) if result else None
        # print(passw)

        if result:
            original_password = passw

            final_password = hashlib.md5((salt + original_password.upper()).encode()).hexdigest()

            if final_password.upper() == input_password:
                return {"status": "0", "message": "Password Matched."}
            else:
                return {"status": "01", "message": "Password Match Failed."}
        else:
            return {"status": "error", "message": "No BP Exists"}

    except Exception as e:
        return {"status": "error", "message": str(e)}

    finally:
        db_connection.commit()
        cursor.close()

