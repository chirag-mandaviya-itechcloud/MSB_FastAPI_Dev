import base64
from fastapi import Body, FastAPI, HTTPException, Request, Header, APIRouter, status, UploadFile
from fastapi.responses import HTMLResponse
import httpx
import hashlib
from pydantic import BaseModel
import psycopg2
import psycopg2.extras 
from typing import List, Dict, Union
from typing import Any, Optional
from fastapi.responses import JSONResponse
from authenticator import verify_password
import xml.etree.ElementTree as ET
import random
import json
from datetime import datetime,timedelta
from db_connector import connection as db_connection
from salesforce_connector import sf
from utility import generate_otp,create_log, sendOTP
import os

router = APIRouter()
DAILY_OTP_GENERATION_LIMIT = os.getenv("DAILY_OTP_GENERATION_LIMIT", 6)
OTP_MATCH_MAX_TRY = os.getenv("OTP_MATCH_MAX_TRY", 5)

@router.post("/BPCheck", response_model=dict, name="Check BP")
async def bp_check(request: Request,
                       BP_Number: Optional[str] = Header(None, title="BP_Number", convert_underscores=False)):
    otp = generate_otp()
    bp_number = request.query_params.get("IP_CONTRACTOR") if request.query_params.get("IP_CONTRACTOR") else BP_Number
    current_datetime = datetime.now()
    password = ''
    try:
        # convert Header Param to JSON
        req_header={"BP_Number":bp_number}

        if bp_number == None or bp_number == "":
            # BP number not found
            response = {
                "status": "02",
                "message": "Please enter IP_CONTRACTOR"
            }
            return response

        # create database cursor
        cursor = db_connection.cursor()

        # query for get msb_account from bp_number
        query = f"""
                SELECT "BP_NUMBER", "NAME", "USER_TYPE", "EMAIL", "MOBILE_NUMBER", "BLOCK"
                FROM public."MSB_ACCOUNT"
                WHERE "BP_NUMBER" = '{bp_number}'
            """

        cursor.execute(query)
        results = cursor.fetchall()

        if results:
            for res in results:
                bp_number = res[0]
                mobile_number = res[4]
                block_status = res[5]

            # query for get msb_credential from bp_number
            for_contractor = f"""
                SELECT "BP_NUMBER", "ENCP_PASSWORD", "EXPIRED", "CREATED_BY", 
                "CREATED_AT", "MODIFIED_BY", "MODIFIED_AT"
                FROM public."MSB_CREDENTIAL"
                WHERE "BP_NUMBER" = '{bp_number}'
            """

            cursor.execute(for_contractor)
            val = cursor.fetchall()

            if val is None or len(val)==0:
                password = ''
                validity = 'VALID'
                # Created Credential Record IF not exist
                # query for create msb_credential
                sql_query="""
                    INSERT INTO public."MSB_CREDENTIAL"
                        ("BP_NUMBER","EXPIRED",
                        "CREATED_BY", "CREATED_AT", "MODIFIED_BY","MODIFIED_AT")
                    VALUES
                        (%s, %s, %s, %s, %s, %s)
                    """

                # Extract values from estimate_data dictionary
                values = (
                    bp_number, "N", bp_number, current_datetime, bp_number, current_datetime
                )
                # Execute the SQL query
                cursor.execute(sql_query, values)

            if val:
                for res in val:
                    password = res[1]
                    validity = 'VALID' if (block_status is None or block_status == 'N') else 'INVALID'

            if password == '' or password is None:
                # query for get msb_otp
                cursor.execute('''
                    SELECT * 
                    FROM "MSB_OTP" 
                    WHERE "BP_NUMBER" = %s
                    AND "CREATED_AT"::date = CURRENT_DATE
                ''', (bp_number,))

                result = cursor.fetchall()

                if(len(result) > 20):
                    return {
                        "status": "04",
                        "message": "Oops! You have reached today's OTP Limits."
                    }
                # query for update the otp
                update_old_otp = """
                    UPDATE "MSB_OTP"
                    SET "CONSUMED_STATUS" = 'YES',
                    "MODIFIED_AT" = %s
                    WHERE "BP_NUMBER" = %s
                """

                cursor.execute(update_old_otp, (current_datetime, bp_number,))
                
                sms_message = f"{otp} আপনার প্রগতি ক্লাব পেইন্টার অ্যাপ-এ প্রবেশ করার গোপন নাম্বার। অনুগ্রহ করে নাম্বারটি নিরাপত্তার স্বার্থে আপনার কাছে গোপন রাখুন।"

                # send otp
                sendOTP(mobileno=mobile_number,message=sms_message,bp_number=bp_number)
                
                current_datetime = datetime.now()
                valid_upto_datetime = current_datetime + timedelta(minutes=15)
                # query for create new otp and insert it into msb_otp
                sql_query="""
                    INSERT INTO public."MSB_OTP"
                        ("BP_NUMBER","MOBILE_NUMBER","OTP","COUNT","VALID_UPTO", "CONSUMED_STATUS","SMS_STATUS",
                        "CREATED_BY", "CREATED_AT", "MODIFIED_BY","MODIFIED_AT")
                    VALUES
                        (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """


                # Extract values from estimate_data dictionary
                values = (
                    bp_number, mobile_number or "",otp,0,valid_upto_datetime,
                    "NO","SENT","API",current_datetime,"API",current_datetime
                )
                # Execute the SQL query
                cursor.execute(sql_query, values)

                # query for add msb_sms object
                outbound_log_query = """INSERT INTO "MSB_SMS"
                ("CONTACT_NO", "DELIVRED_STATUS", "CREATED_ON",
                "DELIVERY_MESSAGE")
                VALUES
                (%s, %s, %s, %s)
                """

                ob_values = (
                    mobile_number or "", "SENT", current_datetime, sms_message
                )

                # Execute the SQL query
                cursor.execute(outbound_log_query, ob_values)
                # response when otp sent.
                response = {
                    "data":{
                        "code":3,
                        "message":"OTP Sent"
                    },
                    "message":"Success",
                    "status":"200"
                }

                create_log("bp_check",json.dumps({"BP_Number":BP_Number}),json.dumps(req_header),json.dumps(response),'Info')
                return response
            else:
                # response when there is valid BP number
                response = {
                    "data":{
                        "code":2,
                        "message":"Valid BP number"
                    },
                    "message":"Success",
                    "status":"200"
                }

                create_log("bp_check",json.dumps({"BP_Number":BP_Number}),json.dumps(req_header),json.dumps(response),'Info')
                return response
        else:
            # response when BP number not found
            response = {
                "data":{
                    "code":1,
                    "message":"Invalid BP"
                },
                "message":"Success",
                "status":"200"
            }
            create_log("bp_check",json.dumps({"BP_Number":BP_Number}),json.dumps(req_header),json.dumps(response),'Info')
            return response
    except Exception as e:
        # Handle exceptions
        print("Exception:", e) 
        response_data = {
            "status": "02",
            "message": "Something went wrong. Please try after some time.",
            "data": None
        }
        error_message = f"Database error: {e}"
        create_log("bp_check",json.dumps({"BP_Number":BP_Number}),json.dumps(req_header),'{"detail":"Internal Server Error"}','Error',error_message)
        return JSONResponse(content=response_data, status_code=200)
    finally:
        # commit all database operations and close cursor
        db_connection.commit()
        cursor.close()
    
     

class validateOTPDetail(BaseModel):
    BP_Number: str
    password: str
    mobile_No: str
    imei: str
    version: str
    otp: str
    source: str


@router.post("/ValidateOtp", response_model=dict, name="Create Password")
async def validateOTP(
    request: Request,
    data: validateOTPDetail,
    BP_Number: Optional[str] = Header(
        None, title="BP_Number", convert_underscores=False
    ),
):
    bp_number = data.BP_Number if data.BP_Number else BP_Number
    count = 0
    try:
        # convert Header Param to JSON
        req_header = {"BP_Number": BP_Number}

        # connect database
        cursor = db_connection.cursor()
        current_datetime = datetime.now()
        otp = data.otp
        password = data.password

        # query for get msb_account from bp_number
        query = f"""
                SELECT "BP_NUMBER", "NAME", "USER_TYPE", "EMAIL", "MOBILE_NUMBER", "BLOCK"
                FROM public."MSB_ACCOUNT"
                WHERE "BP_NUMBER" = '{bp_number}' 
            """
        cursor.execute(query)
        results = cursor.fetchall()

        if results is None or len(results) == 0:
            # BP number not found
            response = {
                "status": "01",
                "message": "Not a valid BP Number.",
                "data": None,
            }
            create_log(
                "create_password",
                json.dumps(await request.json()),
                json.dumps(req_header),
                json.dumps(response),
                "Info",
            )
            return response

        # query for get otp count
        cursor.execute(
            (
                'SELECT "COUNT"'
                ' FROM public."MSB_OTP" '
                ' Where "BP_NUMBER" = %s AND "VALID_UPTO">= %s AND "CONSUMED_STATUS" = %s'
            ),
            (bp_number, current_datetime, "NO"),
        )
        ans = cursor.fetchall()

        if ans is not None and len(ans) != 0:
            for res in ans:
                count = res[0]

            if count > 5:
                # OTP count > 5
                response = {
                    "status": "01",
                    "message": "Too Many Attempts. Regenerate OTP",
                }
                create_log(
                    "create_password",
                    json.dumps(await request.json()),
                    json.dumps(req_header),
                    json.dumps(response),
                    "Info",
                )
                return response

        # query for get msb_otp obj from bp number
        cursor.execute(
            """
            SELECT "BP_NUMBER", "MOBILE_NUMBER", "OTP", "COUNT", "VALID_UPTO", "CONSUMED_STATUS"
            FROM public."MSB_OTP" 
            WHERE "BP_NUMBER" = %s AND "OTP" = %s
        """,
            (bp_number, otp),
        )
        result = cursor.fetchall()

        if result is None or len(result) == 0:
            # update the otp count
            inc_otp = """
                UPDATE "MSB_OTP"
                SET "COUNT" = "COUNT" + 1,
                "MODIFIED_AT" = %s
                WHERE "BP_NUMBER" = %s AND "CONSUMED_STATUS" = 'NO'
            """

            cursor.execute(
                inc_otp,
                (
                    current_datetime,
                    bp_number,
                ),
            )
            # response
            response = {"status": "400", "message": "Bad Request"}
            create_log(
                "create_password",
                json.dumps(await request.json()),
                json.dumps(req_header),
                json.dumps(response),
                "Info",
            )
            return response

        # For contractor and painter, update the cred table with password
        else:
            for res in result:
                if res[5] == "YES":
                    return {"status": "01", "message": "OTP Expired."}
            # final_password = hashlib.md5(password.encode()).hexdigest()
            current_datetime = datetime.now()

            # query for update the password in msb credential object
            cursor.execute(
                """
                UPDATE "MSB_CREDENTIAL"
                SET "ENCP_PASSWORD" = %s,
                    "MODIFIED_BY" = %s,
                    "MODIFIED_AT" = %s
                WHERE "BP_NUMBER" = %s
            """,
                (
                    password,
                    "HEROKU APP",
                    current_datetime,
                    bp_number,
                ),
            )

            # query for change the consumed status of otp
            query_for_accnt = """
                UPDATE "MSB_OTP"
                SET "CONSUMED_STATUS" = 'YES',
                    "MODIFIED_AT" = %s
                WHERE "BP_NUMBER" = %s
            """
            cursor.execute(
                query_for_accnt,
                (
                    current_datetime,
                    bp_number,
                ),
            )

            # success response
            response = {"status": "200", "message": "Credentails Updated"}
            create_log(
                "create_password",
                json.dumps(await request.json()),
                json.dumps(req_header),
                json.dumps(response),
                "Info",
            )
            return response

    except Exception as e:
        # Handle exceptions
        print("Exception:", e)
        response_data = {
            "status": "02",
            "message": "Something went wrong. Please try after some time.",
        }
        error_message = f"Database error: {e}"
        create_log(
            "create_password",
            json.dumps(await request.json()),
            json.dumps(req_header),
            '{"detail":"Internal Server Error"}',
            "Error",
            error_message,
        )
        return JSONResponse(content=response_data, status_code=200)

    finally:
        # commit all database operation and close the connection
        db_connection.commit()
        cursor.close()


class GenerateOTP(BaseModel):
    BP_Number: str
    source: str
    version: str


@router.post("/ForgotPassword", response_model=dict)
async def generate_new_otp(
    request: Request,
    BP_Number: Optional[str] = Header(
        None, title="BP_Number", convert_underscores=False
    ),
):
    bp_number = request.query_params.get("IP_CONTRACTOR") if request.query_params.get("IP_CONTRACTOR") else BP_Number
    current_datetime = datetime.now()
    try:
        # convert Header Param to JSON
        req_header = {"BP_Number": BP_Number}

        cursor = db_connection.cursor()
        otp = generate_otp()
        # considering this will always be triggered crotp is send once
        current_date = datetime.now().date()

        # Get the start and end of the current day
        start_of_day = datetime.combine(current_date, datetime.min.time())
        end_of_day = datetime.combine(current_date, datetime.max.time())

        # query for get otp
        cursor.execute(
            """
            SELECT * 
            FROM "MSB_OTP" 
            WHERE "BP_NUMBER" = %s 
            AND "CREATED_AT" >= %s 
            AND "CREATED_AT" <= %s
        """,
            (bp_number, start_of_day, end_of_day),
        )
        result = cursor.fetchall()

        if len(result) > DAILY_OTP_GENERATION_LIMIT:
            # daily otp limit reached
            response = {
                "status": "01",
                "message": "Daily Limit of OTP Generation Reached, try again tomorrow.",
            }
            create_log(
                "generate_new_otp",
                json.dumps(await request.json()),
                json.dumps(req_header),
                json.dumps(response),
                "Info",
            )
            return response
        else:
            # query for get msb account
            cursor.execute(
                """
                SELECT "BP_NUMBER", "MOBILE_NUMBER"
                FROM public."MSB_ACCOUNT" 
                WHERE "BP_NUMBER" = %s 
                """,
                (bp_number,),
            )
            result = cursor.fetchall()
            if result is None or len(result) == 0:
                # response otp failed to send
                return {
                    "data": {"code": 4, "message": "OTP Failed to Send"},
                    "message": "Success",
                    "status": "200",
                }

            for res in result:
                mobile_number = res[1]

            # query for update consumed status
            update_old_otp = """
                UPDATE "MSB_OTP"
                SET "CONSUMED_STATUS" = 'YES',
                "MODIFIED_AT" = %s
                WHERE "BP_NUMBER" = %s
            """

            cursor.execute(
                update_old_otp,
                (
                    current_datetime,
                    bp_number,
                ),
            )

            sms_message = f"{otp} আপনার প্রগতি ক্লাব পেইন্টার অ্যাপ-এ প্রবেশ করার গোপন নাম্বার। অনুগ্রহ করে নাম্বারটি নিরাপত্তার স্বার্থে আপনার কাছে গোপন রাখুন।"

            # sms_url = f"https://api.asianpaints.com/v1/sendsms/crm_sms/send_crm_sms?mobile_no={mobile_number}&message={otp}%20is%20your%20OTP%20for%20Asian%20Paints%20Masterstrokes%20Login.%20Do%20not%20share%20the%20OTP%20with%20anyone%20for%20security%20reasons."
            # sms_resp = httpx.get(sms_url)

            sendOTP(mobileno=mobile_number, message=sms_message, bp_number=bp_number)

            valid_upto_datetime = current_datetime + timedelta(minutes=15)
            # query for create otp object
            sql_query = """
                INSERT INTO public."MSB_OTP"
                    ("BP_NUMBER", "MOBILE_NUMBER", "OTP", "COUNT", "VALID_UPTO", "CONSUMED_STATUS", "SMS_STATUS",
                    "CREATED_BY", "CREATED_AT", "MODIFIED_BY", "MODIFIED_AT")
                VALUES
                    (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """

            values = (
                bp_number,
                mobile_number or "",
                otp,
                0,
                valid_upto_datetime,
                "NO",
                "SENT",
                "API",
                current_datetime,
                "API",
                current_datetime,
            )

            # Execute the SQL query
            cursor.execute(sql_query, values)

            # query for add msb_sms object
            outbound_log_query = """INSERT INTO "MSB_SMS"
            ("CONTACT_NO", "DELIVRED_STATUS", "CREATED_ON",
            "DELIVERY_MESSAGE")
            VALUES
            (%s, %s, %s, %s)
            """
            ob_values = (mobile_number or "", "SENT", current_datetime, sms_message)

            # Execute the SQL query
            cursor.execute(outbound_log_query, ob_values)

            # response for otp send
            response = {
                "data": {"code": 3, "message": "OTP Sent"},
                "message": "Success",
                "status": "200",
            }
           
            return response

    except Exception as e:
        # Handle exceptions
        print("Exception:", e)
        response_data = {
            "status": "02",
            "message": "OTP generation failed due to exception.",
        }
        error_message = f"Database error: {e}"
        create_log(
            "generate_new_otp",
            json.dumps(await request.json()),
            json.dumps(req_header),
            '{"detail":"Internal Server Error"}',
            "Error",
            error_message,
        )
        return JSONResponse(content=response_data, status_code=200)

    finally:
        # commit all database operation and close the connection
        db_connection.commit()
        cursor.close()


class ValidateOTP(BaseModel):
    BP_Number: str
    otp: str
    password: str
    mobile_No: str
    version: str
    source: str
    imei: str


@router.post("/ValidateOtpNoUpdate", response_model=dict)
async def validate_otp(
    request: Request,
    data: ValidateOTP,
    BP_Number: Optional[str] = Header(
        None, title="BP_Number", convert_underscores=False
    ),
):
    bp_number = data.BP_Number if data.BP_Number else BP_Number
    try:
        # convert Header Param to JSON
        req_header = {"BP_Number": BP_Number}

        cursor = db_connection.cursor()
        otp = data.otp
        current_datetime = datetime.now()
        count = 0

        # query for get the count of msb otp
        cursor.execute(
            (
                'SELECT "COUNT"'
                ' FROM public."MSB_OTP" '
                ' Where "BP_NUMBER" = %s AND "VALID_UPTO">= %s AND "CONSUMED_STATUS" = %s'
            ),
            (bp_number, current_datetime, "NO"),
        )
        ans = cursor.fetchall()

        if ans is not None and len(ans) != 0:
            for res in ans:
                count = res[0]

            if count > OTP_MATCH_MAX_TRY:
                response = {
                    "status": "01",
                    "message": "Too Many Attempts. Regenerate OTP",
                }
                create_log(
                    "validate_otp",
                    json.dumps(await request.json()),
                    json.dumps(req_header),
                    json.dumps(response),
                    "Info",
                )
                return response

        # query for get the msb otp object from bp number
        cursor.execute(
            """
            SELECT "BP_NUMBER", "MOBILE_NUMBER", "OTP", "COUNT", "VALID_UPTO"
            FROM public."MSB_OTP"
            WHERE "BP_NUMBER" = %s AND "OTP" = %s
        """,
            (bp_number, otp),
        )
        result = cursor.fetchall()

        if result is None or len(result) == 0:
            # query for update the count of otp
            inc_otp = """
                UPDATE public."MSB_OTP"
                SET "COUNT" = "COUNT" + 1,
                "MODIFIED_AT" = %s
                WHERE "BP_NUMBER" = %s AND "CONSUMED_STATUS" = 'NO'
            """

            cursor.execute(
                inc_otp,
                (
                    current_datetime,
                    bp_number,
                ),
            )
            
            response = {
                "status": "404",
                "message": "Invalid BP Number or OTP",
            }
            create_log(
                "validate_otp",
                json.dumps(await request.json()),
                json.dumps(req_header),
                json.dumps(response),
                "Info",
            )
            return response

        else:
            response = {
                "status": "200",
                "message": "Valid OTP",
            }
            create_log(
                "validate_otp",
                json.dumps(await request.json()),
                json.dumps(req_header),
                json.dumps(response),
                "Info",
            )
            return response

    except Exception as e:
        # Handle exceptions
        print("Exception:", e)
        response_data = {
            "status": "02",
            "message": "Something went wrong. Please try after some time.",
        }
        error_message = f"Database error: {e}"
        create_log(
            "validate_otp",
            json.dumps(await request.json()),
            json.dumps(req_header),
            '{"detail":"Internal Server Error"}',
            "Error",
            error_message,
        )
        return JSONResponse(content=response_data, status_code=200)

    finally:
        # commit all database operation and close the connection
        db_connection.commit()
        cursor.close()


class SignUp(BaseModel):
    bpNumber: str
    salt: str
    password: str
    version: str
    source: str

@router.post("/SignUpNew", response_model=dict)
async def sign_up(
    request: Request,
    data: SignUp,
    BP_Number: Optional[str] = Header(
         None, title="BP_Number", convert_underscores=False
     ),
):
    bp_number = data.bpNumber if data.bpNumber else BP_Number
    try:
        # convert Header Param to JSON
        req_header = {"BP_Number": BP_Number}
        cursor = db_connection.cursor()
        current_datetime = datetime.now()

        result = verify_password(data.password, data.salt, bp_number, db_connection)
        if result.get("status") == "0":
            return JSONResponse(status_code=200, content={"status": "0", "message": "Success"})
        else:
            return JSONResponse(status_code=200, content={"status": "01", "message": "Password Match Failed."})       

    except Exception as e:
        # Handle exceptions
        print("Exception:", e)
        response_data = {
            "status": "02",
            "message": "Something went wrong. Please try after some time.",
        }
        error_message = f"Database error: {e}"
        create_log(
            "SignUpNew",
            json.dumps(await request.json()),
            json.dumps(req_header),
            '{"detail":"Internal Server Error"}',
            "Error",
            error_message,
        )
        return JSONResponse(content=response_data, status_code=200)

    finally:
        # commit all database operation and close the connection
        db_connection.commit()
        cursor.close()


class ChangePassword(BaseModel):
    bpNumber: str
    salt: str
    password: str
    newPassword: str
    version: str
    source: str

@router.post("/ChangePassword", response_model=dict)
async def sign_up(
    request: Request,
    data: ChangePassword,
    BP_Number: Optional[str] = Header(
         None, title="BP_Number", convert_underscores=False
     ),
):
    
    bp_number = data.bpNumber if data.bpNumber else BP_Number
    try:
        # convert Header Param to JSON
        req_header = {"BP_Number": BP_Number}
        cursor = db_connection.cursor()
        current_datetime = datetime.now()

        result = verify_password(data.password, data.salt, bp_number, db_connection)
        if result.get("status") == "0":
            # query for update the password in msb credential object
            cursor.execute(
                """
                UPDATE "MSB_CREDENTIAL"
                SET "ENCP_PASSWORD" = %s,
                    "MODIFIED_BY" = %s,
                    "MODIFIED_AT" = %s
                WHERE "BP_NUMBER" = %s
            """,
                (
                    data.newPassword,
                    "HEROKU APP",
                    current_datetime,
                    bp_number,
                ),
            )
            return JSONResponse(status_code=200, content={"status": "0", "message": "Password Updated Successfully."})
        else:
            return JSONResponse(status_code=200, content={"status": "401", "message": "Unauthorized"})       

    except Exception as e:
        # Handle exceptions
        print("Exception:", e)
        response_data = {
            "status": "02",
            "message": "Something went wrong. Please try after some time.",
        }
        error_message = f"Database error: {e}"
        create_log(
            "ChangePassword",
            json.dumps(await request.json()),
            json.dumps(req_header),
            '{"detail":"Internal Server Error"}',
            "Error",
            error_message,
        )
        return JSONResponse(content=response_data, status_code=200)

    finally:
        # commit all database operation and close the connection
        db_connection.commit()
        cursor.close()
        