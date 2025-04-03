from fastapi import  HTTPException, Header, status, Request ,APIRouter
from pydantic import BaseModel
import psycopg2
from typing import List, Optional
from db_connector import connection as db_connection
from salesforce_connector import sf
from simple_salesforce.exceptions import  SalesforceError
from fastapi.responses import JSONResponse

from utility import create_log
import json

router = APIRouter()


class LoyaltyPoints(BaseModel):
    Salt: str = ""
    Password: str = ""

@router.post("/LoyalityPoints", response_model=dict, name="Get Loyalty Points")
async def get_loyalty_points(request: Request,data: LoyaltyPoints, 
                                BP_Number: str = Header(..., convert_underscores=False),
                                App_Ver: str = Header(..., convert_underscores=False),
                                Android_Ver: str = Header(..., convert_underscores=False),
                                Device_Id: str = Header(..., convert_underscores=False),
                                Device_Mod: str = Header(..., convert_underscores=False),
                                Source: str = Header(..., convert_underscores=False)):
     
    try:
        # convert Header Param to JSON
        req_header={"BP_Number":BP_Number,"App_Ver":App_Ver,"Android_Ver":Android_Ver,
                    "Device_Id":Device_Id,"Device_Mod":Device_Mod,"Source":Source}
       
        cursor = db_connection.cursor()
        
        payload = {
           "bp": BP_Number
        }

        sf_response = sf.apexecute('/MSB/LoyaltyPoints', method='POST', data=payload)
        
        create_log("get_loyalty_points",json.dumps(await request.json()),json.dumps(req_header),json.dumps(sf_response),'Info')
        return sf_response

    except psycopg2.Error as e:
        # Handle database errors and return appropriate HTTP response
        print(f"Database error: {e}")
        response_data = { 
            "status": "02", 
            "message": "Something went wrong. Please try after some time.",
        }
        error_message = f"Database error: {e}"
        create_log("get_loyalty_points",json.dumps(await request.json()),json.dumps(req_header),'{"detail":"Internal Server Error"}','Error',error_message)
        return JSONResponse(content=response_data, status_code=200) 
    except SalesforceError as e:
        # Access the error message from the exception
        error_message = e.content[0]['message']
        print(f"Salesforce error: {error_message}")
        response_data = { 
            "status": "02", 
            "message": "Something went wrong. Please try after some time.",
        }
        error_message = f"Database error: {e}"
        create_log("get_loyalty_points",json.dumps(await request.json()),json.dumps(req_header),'{"detail":"Internal Server Error"}','Error',error_message)
        return JSONResponse(content=response_data, status_code=200) 
    except Exception as e:
        # Handle database errors and return appropriate HTTP response
        print(f"Database error: {e}")
        response_data = { 
            "status": "02", 
            "message": "Something went wrong. Please try after some time.",
        }
        error_message = f"Database error: {e}"
        create_log("get_loyalty_points",json.dumps(await request.json()),json.dumps(req_header),'{"detail":"Internal Server Error"}','Error',error_message)
        return JSONResponse(content=response_data, status_code=200) 
    finally:
        db_connection.commit()
        cursor.close()

