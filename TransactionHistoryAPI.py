from fastapi import  HTTPException, Header, status, Request ,APIRouter
from pydantic import BaseModel
import psycopg2
from typing import List, Optional
from db_connector import connection as db_connection
from salesforce_connector import sf
from simple_salesforce.exceptions import SalesforceError
from datetime import datetime,timedelta
from fastapi.responses import JSONResponse


from utility import create_log
import json

router = APIRouter()

def convert_date(date_str: str) -> str:
    if date_str == "":
        return date_str
    # Define multiple formats to handle both input date formats
    for fmt in ("%d-%b-%Y", "%d-%B-%Y","%Y%m%d"):
        try:
            return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    raise ValueError(f"Date format for {date_str} is not recognized")

class BPListDetail(BaseModel):
    BpNo : str

    # Method to convert object to a dictionary
    def to_dict(self):
        return {
            "BpNo": self.BpNo
        }

class TransactionHisotryDetails(BaseModel):
    Salt: str = ""
    Password: str = ""
    Transaction_Type : str = ""
    PageNo : str = "1"
    StartDate : str = ""
    EndDate : str = ""
    Bp_List : List[BPListDetail]

@router.post("/Transaction_History", response_model=dict, name="Transaction History")
async def transaction_history_detail(request: Request,data: TransactionHisotryDetails, 
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
        
        bp_list_dicts = [bpRecord.to_dict() for bpRecord in data.Bp_List]

        payload = {
            "bp": BP_Number,
            "PageNumber" : int(data.PageNo) if data.PageNo != '' else 1,
            "Transaction_Type": data.Transaction_Type,
            "StartDate": convert_date(data.StartDate),
            "EndDate" : convert_date(data.EndDate),
            "Bp_List": bp_list_dicts
        }

        response = sf.apexecute('/MSG/TransactionHistory', method='POST', data=payload)
        
        create_log("transaction_history_detail",json.dumps(await request.json()),json.dumps(req_header),json.dumps(response),'Info')
        return response

    except psycopg2.Error as e:
        # Handle database errors and return appropriate HTTP response
        print(f"Database error: {e}")
        response_data = { 
            "status": "02", 
            "message": "Something went wrong. Please try after some time.",
        }
        error_message = f"Database error: {e}"
        create_log("transaction_history_detail",json.dumps(await request.json()),json.dumps(req_header),'{"detail":"Internal Server Error"}','Error',error_message)
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
        create_log("transaction_history_detail",json.dumps(await request.json()),json.dumps(req_header),'{"detail":"Internal Server Error"}','Error',error_message)
        return JSONResponse(content=response_data, status_code=200)
    except Exception as e:
        # Handle database errors and return appropriate HTTP response
        print(f"Database error: {e}")
        response_data = { 
            "status": "02", 
            "message": "Something went wrong. Please try after some time.",
        }
        error_message = f"Database error: {e}"
        create_log("transaction_history_detail",json.dumps(await request.json()),json.dumps(req_header),'{"detail":"Internal Server Error"}','Error',error_message)
        return JSONResponse(content=response_data, status_code=200)
    finally:
        db_connection.commit()
        cursor.close()

class TransactionLineItemHisotryDetails(BaseModel):
    Salt: str = ""
    Password: str = ""
    Transaction_Type : str 
    TransactionNo : str 
    
@router.post("/Transaction_History_LineItems", response_model=dict, name="Transaction Item History")
async def transaction_history_lineItemsdetail(request: Request,data: TransactionLineItemHisotryDetails, 
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
            "bp": BP_Number,
            "Transaction_Type": data.Transaction_Type,
            "TransactionNo": data.TransactionNo
        }

        response = sf.apexecute('/MSG/TransactionHistoryLineItems', method='POST', data=payload)
        
        create_log("transaction_history_lineItemsdetail",json.dumps(await request.json()),json.dumps(req_header),json.dumps(response),'Info')
        return response

    except psycopg2.Error as e:
        # Handle database errors and return appropriate HTTP response
        print(f"Database error: {e}")
        response_data = { 
            "status": "02", 
            "message": "Something went wrong. Please try after some time.",
        }
        error_message = f"Database error: {e}"
        create_log("transaction_history_lineItemsdetail",json.dumps(await request.json()),json.dumps(req_header),'{"detail":"Internal Server Error"}','Error',error_message)
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
        create_log("transaction_history_lineItemsdetail",json.dumps(await request.json()),json.dumps(req_header),'{"detail":"Internal Server Error"}','Error',error_message)
        return JSONResponse(content=response_data, status_code=200)
    except Exception as e:
        # Handle database errors and return appropriate HTTP response
        print(f"Database error: {e}")
        response_data = { 
            "status": "02", 
            "message": "Something went wrong. Please try after some time.",
        }
        error_message = f"Database error: {e}"
        create_log("transaction_history_lineItemsdetail",json.dumps(await request.json()),json.dumps(req_header),'{"detail":"Internal Server Error"}','Error',error_message)
        return JSONResponse(content=response_data, status_code=200)
    finally:
        db_connection.commit()
        cursor.close()

class DealerDetails(BaseModel):
    Salt: str = ""
    Password: str = ""
    Status : str = ""
    
@router.post("/Dealer_List", response_model=dict, name="Dealer List")
async def delaer_list(request: Request,data: DealerDetails, 
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
            "bp": BP_Number,
            "status" : data.Status
        }

        response = sf.apexecute('/MSG/DealerList', method='POST', data=payload)
        
        create_log("transaction_history_lineItemsdetail",json.dumps(await request.json()),json.dumps(req_header),json.dumps(response),'Info')
        return response

    except psycopg2.Error as e:
        # Handle database errors and return appropriate HTTP response
        print(f"Database error: {e}")
        response_data = { 
            "status": "02", 
            "message": "Something went wrong. Please try after some time.",
        }
        error_message = f"Database error: {e}"
        create_log("delaer_list",json.dumps(await request.json()),json.dumps(req_header),'{"detail":"Internal Server Error"}','Error',error_message)
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
        create_log("delaer_list",json.dumps(await request.json()),json.dumps(req_header),'{"detail":"Internal Server Error"}','Error',error_message)
        return JSONResponse(content=response_data, status_code=200)
    except Exception as e:
        # Handle database errors and return appropriate HTTP response
        print(f"Database error: {e}")
        response_data = { 
            "status": "02", 
            "message": "Something went wrong. Please try after some time.",
        }
        error_message = f"Database error: {e}"
        create_log("delaer_list",json.dumps(await request.json()),json.dumps(req_header),'{"detail":"Internal Server Error"}','Error',error_message)
        return JSONResponse(content=response_data, status_code=200)
    finally:
        db_connection.commit()
        cursor.close()


