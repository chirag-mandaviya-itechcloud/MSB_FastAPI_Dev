from fastapi import  HTTPException, Header, status, Request ,APIRouter
from pydantic import BaseModel
from typing import List, Optional
from db_connector import connection as db_connection
from datetime import datetime,timedelta
import random
import os
import json
import string
import base64

import requests

CURRENT_FISCAL_YEAR = os.getenv("FISCAL_YEAR", "2023")

SMSAPIKEY= os.getenv("SMSAPIKEY", "P4SVbiZktWsAmPePFyFbqEdYctqtq6qE")
SMSAPITOKEN= os.getenv("SMSAPITOKEN", "dqzfk7s0-l3xiufgr-2guoud17-ik8ocmk0-qmd4lsic")

otpSMSLink="https://api.asianpaints.com/v1/msb-sent-sms?apikey="+SMSAPIKEY
SMSLink="https://api.asianpaints.com/v1/msbsend-sms/SendSMS"



def create_log( method_name: str,
                    request: str,
                    request_header: str,
                    response: str,
                    log_type: str,
                    error_message: str = None,
                    sfid: str = None):
    try:
        cursor = db_connection.cursor()
        # Define the SQL query to insert log information into the table
        sql_query="""
            INSERT INTO public."MSB_SYSTEM_LOG"
                ("MODULE","REQUEST_PAYLOAD","REQUEST_HEADER","RESPONSE_PAYLOAD",  "TYPE","ERROR_MESSAGE","SF_ID")
            VALUES
                (%s,%s, %s,%s, %s, %s,%s)
            """

            # Extract values from estimate_data dictionary
        values = (
            method_name,
            request,
            request_header,
            response,
            log_type,
            error_message,
            sfid
        )
        # Execute the SQL query
        cursor.execute(sql_query, values)
        db_connection.commit()
    except Exception as e:
        # Handle any exceptions that might occur during the database operation
        raise HTTPException(status_code=500, detail=f"Error storing log: {str(e)}")

    finally:
        # Close the database connection
        db_connection.commit()
        cursor.close()

def generate_otp():
    return random.randint(100000, 999999)

def sendOTP( mobileno: str,  message: str ,
            bp_number: str,):
    try:
        cursor = db_connection.cursor()
        current_datetime = datetime.now()
        random_string = ''.join(random.choices(string.ascii_uppercase + string.digits, k=3))
        csms_id = f"{random_string}{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # convert Header Param to JSON
        req_header={"BP_Number":bp_number}
        
        if mobileno==None or message==None :
            return {
                "status" : '01',
                "message" : 'Mobile No And Message Required'
            }
        
        payload_data = {
            "api_token" : SMSAPITOKEN,
            "sid": "AP_Longcode",
            "sms": message,
            "msisdn": mobileno,
            "csms_id": csms_id
        }
        
        payload_data = {
            "msg":  base64.b64encode(message.encode('utf-8')).decode('utf-8'),
            "mob": mobileno,
        }

        headers = {"Content-Type": "application/json"}
        response = requests.post(SMSLink, json = payload_data, headers=headers)
        #headers = {"Content-Type": "application/x-www-form-urlencoded"}
        #response = requests.post(otpSMSLink, data=payload_data, files = payload_data)
        responsejson = response.json()
 
        create_log("sendOTP",json.dumps(payload_data),json.dumps(req_header),json.dumps(responsejson),'Info')
        
        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            
            if responsejson.get("status") == 'SUCCESS':
                # Return the JSON data
                return {
                    "status" : '0',
                    "message" : 'OTP sent successfully.'
                }
            else:
                # Return the JSON data
                return {
                    "status" : '01',
                    "message" : 'OTP sent failed.'
                }
        else:     
            return {
                "status" : '01',
                "message": "Failed to call external API"
            }
        
        
    except Exception as e:
        response = {
            "status" : '01',
            "message": f"Error in send OTP: {str(e)}"
        }
        error_message = f"Database error: {e}"
        create_log("sendOTP",'',json.dumps(req_header),'{"detail":"Internal Server Error"}','Error',error_message)
        return response
    finally:
        # Close the database connection
        db_connection.commit()
        cursor.close()

def sendSMS(
    mobileno: str,
    message: str,
    bp_number: str,
):
    try:
        cursor = db_connection.cursor()
        current_datetime = datetime.now()
        random_string = "".join(
            random.choices(string.ascii_uppercase + string.digits, k=3)
        )
        csms_id = f"{random_string}{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # convert Header Param to JSON
        req_header = {"BP_Number": bp_number}

        if mobileno == None or message == None:
            return {"status": "01", "message": "Mobile No And Message Required"}

        payload_data = {
            "api_token": SMSAPITOKEN,
            "sid": "AP_Longcode",
            "sms": message,
            "msisdn": mobileno,
            "csms_id": csms_id,
        }

        payload_data = {
            "msg":  base64.b64encode(message.encode('utf-8')).decode('utf-8'),
            "mob": mobileno,
        }

        headers = {"Content-Type": "application/json"}
        response = requests.post(SMSLink, json = payload_data, headers=headers)

        #headers = {"Content-Type": "application/x-www-form-urlencoded"}
        #response = requests.post(otpSMSLink, payload_data, headers=headers)
        responsejson = response.json()

        create_log(
            "sendSMS",
            json.dumps(payload_data),
            json.dumps(req_header),
            json.dumps(responsejson),
            "Info",
        )

        # query for add msb_sms object
        outbound_log_query = """INSERT INTO "MSB_SMS"
        ("CONTACT_NO", "DELIVRED_STATUS", "CREATED_ON",
        "DELIVERY_MESSAGE")
        VALUES
        (%s, %s, %s, %s)
        """
        ob_values = (mobileno or "", "SENT", current_datetime, message)

        # Execute the SQL query
        cursor.execute(outbound_log_query, ob_values)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            if responsejson.get("status") == "SUCCESS":
                # Return the JSON data
                return {"status": "0", "message": "SMS sent successfully."}
            else:
                # Return the JSON data
                return {"status": "01", "message": "SMS sent failed."}
        else:
            return {"status": "01", "message": "Failed to call external API"}

    except Exception as e:
        response = {"status": "01", "message": f"Error in send SMS: {str(e)}"}
        error_message = f"Database error: {e}"
        create_log(
            "sendOTP",
            "",
            json.dumps(req_header),
            '{"detail":"Internal Server Error"}',
            "Error",
            error_message,
        )
        return response
    finally:
        # Close the database connection
        db_connection.commit()
        cursor.close()

def get_last_day_of_month(year, month):
    """Returns the last day of the given month."""
    next_month = month % 12 + 1  # Get the next month (March if Feb, Jan if Dec)
    next_month_year = year + (1 if month == 12 else 0)  # Increment year if December
    last_day = datetime(next_month_year, next_month, 1) - timedelta(days=1)
    return last_day.replace(hour=23, minute=59, second=59)  # Set time to 23:59:59

def convert_date(date_str: str) -> str:
    if date_str == "":
        return date_str
    # Define multiple formats to handle both input date formats
    for fmt in ("%d-%b-%Y", "%d-%B-%Y","%Y%m%d", "%Y%m%d%H%M%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    raise ValueError(f"Date format for {date_str} is not recognized")


def get_fiscal_year_dates():
    # get and convert date to YYYY-MM-DD format
    today_date = datetime.today()
    
    current_fy_start_date = convert_date(os.getenv("CURRENT_FY_START_DATE", f"{today_date.year}-04-01"))
    current_fy_end_date = convert_date(os.getenv("CURRENT_FY_END_DATE", f"{today_date.year+1}-03-31"))
    last_fy_start_date = convert_date(os.getenv("LAST_FY_START_DATE", f"{today_date.year-1}-04-01"))
    last_fy_end_date = convert_date(os.getenv("LAST_FY_END_DATE", f"{today_date.year}-03-31"))
    
    fy_start_ty = datetime.strptime(current_fy_start_date, "%Y-%m-%d")
    fy_end_ty = datetime.strptime(current_fy_end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
    
    fy_start_ly = datetime.strptime(last_fy_start_date, "%Y-%m-%d")
    fy_end_ly = datetime.strptime(last_fy_end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)

    return fy_start_ly, fy_end_ly, fy_start_ty, fy_end_ty


def get_month_dates():
    today = datetime.today()
    first_day_this_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_day_last_month = get_last_day_of_month(today.year, today.month -1 )
    first_day_last_month = last_day_last_month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    return first_day_last_month, last_day_last_month, first_day_this_month, today