from fastapi import Body, Request, Header, APIRouter
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from db_connector import connection as db_connection
from salesforce_connector import sf
from typing import Any, Optional
from utility import create_log
import json

router = APIRouter()
    

@router.post("/FetchLanguage", response_model=dict)
async def fetch_language(request: Request,
    BP_Number: Optional[str] = Header(None, title="BP_Number", convert_underscores=False),
):
    bp_number = BP_Number
    # convert Header Param to JSON
    req_header={"BP_Number":BP_Number}
    try:
       
        cursor = db_connection.cursor()
        
        query = """
            SELECT "LANGUAGE_ID"
            FROM public."MSB_ACCOUNT"
            WHERE "BP_NUMBER" = %s 
        """
        cursor.execute(query, (bp_number,))
        res = cursor.fetchall()
        response = {}
        if len(res) > 0  and len(res[0]) > 0:
            response = {
                "language_ID":res[0][0],
                "message":"Success",
                "status":"0"
            }
        else:
            response = {
                "language_ID":None,
                "message":"Success",
                "status":"0"
            }
        return response
    except Exception as e:
        # Handle exceptions
        print("Exception:", e)
        response = {
            "status": "01",
            "message": "Error Occurred",
            "data": None
        }
        error_message = f"Database error: {e}"
        create_log("select_language",'',json.dumps(req_header),'{"detail":"Internal Server Error"}','Error',error_message)
        return JSONResponse(content=response, status_code=200)
    finally:
         db_connection.commit()
         cursor.close()



@router.post("/SelectLanguage", response_model=dict, name="Check BP")
async def select_language(request: Request,
    BP_Number: Optional[str] = Header(None, title="BP_Number", convert_underscores=False),
):
    bp_number = BP_Number
    try:
        # convert Header Param to JSON
        req_header={"BP_Number":BP_Number}
       
        cursor = db_connection.cursor()
        query = """
            SELECT "LANGUAGE", "LANG_ID"
            FROM public."MSB_LANG"
        """
        cursor.execute(query)
        results = cursor.fetchall()
        
        lang_records = [{
                "language_ID": row[1],
                "language": row[0],
                } for row in results]
        
        response = {}
        if len(lang_records) == 0:
            response = {
                "status": "01",
                "message":"No data available.",
                "data":None
            }
        else:
            response = {
                "status" : "0",
                "message" : "Success",
                "data": lang_records
            }
        create_log("select_language",'',json.dumps(req_header),json.dumps(response),'Info')
        return response
        
    except Exception as e:
        # Handle exceptions
        print("Exception:", e) 
        response = {
            "status": "01",
            "message": "Error Occurred",
            "data": None
        }
        error_message = f"Database error: {e}"
        create_log("select_language",'',json.dumps(req_header),'{"detail":"Internal Server Error"}','Error',error_message)
        return JSONResponse(content=response, status_code=200)
    finally:
         db_connection.commit()
         cursor.close()
     

class SetLanguage(BaseModel):
    LanguageId : str
    salt : str
    password: str

@router.post("/SetLanguagePreference", response_model=dict, name="Set Language")
async def set_Language(request: Request,
                       data: SetLanguage,
                       BP_Number: Optional[str] = Header(None, title="BP_Number", convert_underscores=False),):
    bp_number = BP_Number
    try:
        # convert Header Param to JSON
        req_header={"BP_Number":BP_Number}
       
        cursor = db_connection.cursor()
        
        query_for_accnt = """
            UPDATE "MSB_ACCOUNT"
            SET "LANGUAGE_ID" = %s
            WHERE "BP_NUMBER" = %s
        """
        cursor.execute(query_for_accnt, (data.LanguageId, bp_number,))
        response = {
            "status" : "0",
            "message": "SUCCESS",
            "data": "Language Preference have been Updated."
        }
        create_log("set_Language",json.dumps(await request.json()),json.dumps(req_header),json.dumps(response),'Info')
        return response
    
        
    except Exception as e:
        # Handle exceptions
        print("Exception:", e) 
        response_data = {
            "status": "01",
            "message": "Failure",
            "data": None
        }
        error_message = f"Database error: {e}"
        create_log("set_Language",json.dumps(await request.json()),json.dumps(req_header),'{"detail":"Internal Server Error"}','Error',error_message)
        return JSONResponse(content=response_data, status_code=200) 
        
    finally:
        db_connection.commit()
        cursor.close()
