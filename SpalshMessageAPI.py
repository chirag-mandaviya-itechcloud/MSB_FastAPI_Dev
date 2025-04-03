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
import xml.etree.ElementTree as ET
import random
import json
from datetime import datetime,timedelta
from db_connector import connection as db_connection
from salesforce_connector import sf
from utility import create_log
import os

router = APIRouter()


class SpalshMessage(BaseModel):
    LanguageID : str = "00"
   
@router.post("/SpalshMessage", response_model=dict, name=" Splash Messages")
async def spalsh_message(request: Request, data: SpalshMessage,
                        Source: str = Header(..., title="Source"),
                        App_Ver: str = Header(..., alias="App_Ver"),
                        Android_Ver: str = Header(..., alias="Android_Ver"),
                        Device_Id: str = Header(..., alias="Device_Id"),
                        Device_Mod: str = Header(..., alias="Device_Mod"),):
    
    try:
        # convert Header Param to JSON
        req_header={"App_Ver":App_Ver,"Android_Ver":Android_Ver,
                    "Device_Id":Device_Id,"Device_Mod":Device_Mod,"Source":Source}
       
        cursor = db_connection.cursor()
        
        query = f"""
                SELECT "MESSAGE"
                FROM public."MSG_SPLASH_MESSAGES"
                WHERE "LANGUAGE_ID" = %s AND "TYPE" = 'CONTRACTOR'
            """

        cursor.execute(query, (data.LanguageID,))
        results = cursor.fetchall()         
        
        langRecords = [{
                "messages": row[0]
            } for row in results]
        
        response = {
            "status" : "0",
            "message" : "Success",
            "data": langRecords
        }
        create_log("spalsh_message",json.dumps(await request.json()),json.dumps(req_header),json.dumps(response),'Info')
        return response
        
        
    except Exception as e:
        # Handle exceptions
        print("Exception:", e) 
        response_data = {
            "status": "01",
            "message": "FAILURE",
            "data": None
        }
        error_message = f"Database error: {e}"
        create_log("spalsh_message",json.dumps(await request.json()),json.dumps(req_header),'{"detail":"Internal Server Error"}','Error',error_message)
        return JSONResponse(content=response_data, status_code=200)
    finally:
         db_connection.commit()
         cursor.close()
     
