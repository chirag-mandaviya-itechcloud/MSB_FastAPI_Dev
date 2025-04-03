from fastapi import Body, HTTPException, Request, Header, APIRouter
from pydantic import BaseModel
import psycopg2
import psycopg2.extras 
import json
from salesforce_connector import sf
from simple_salesforce.exceptions import SalesforceError
from utility import create_log
from fastapi.responses import JSONResponse


router = APIRouter()

class FetchBankDetails(BaseModel):
    Salt : str
    Password: str

@router.post("/Fetch_Bank_Details", response_model=dict, name="Fetch Bank Detail")
async def fetch_bank_details(request: Request,data: FetchBankDetails, 
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
       
        
        payload = {
            "bp": BP_Number
        }
        
        response = sf.apexecute('/MSG/GetContractorBankDetails', method='POST', data=payload)
        
        create_log("fetch_bank_details",json.dumps(await request.json()),json.dumps(req_header),json.dumps(response),'Info')
        return response

    except psycopg2.Error as e:
        # Handle database errors and return appropriate HTTP response
        print(f"Database error: {e}")
        response_data = { 
            "status": "02", 
            "message": "Something went wrong. Please try after some time.",
        }
        error_message = f"Database error: {e}"
        create_log("fetch_bank_details",json.dumps(await request.json()),json.dumps(req_header),'{"detail":"Internal Server Error"}','Error',error_message)
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
        create_log("fetch_bank_details",json.dumps(await request.json()),json.dumps(req_header),'{"detail":"Internal Server Error"}','Error',error_message)
        return JSONResponse(content=response_data, status_code=200) 
    except Exception as e:
        # Handle database errors and return appropriate HTTP response
        print(f"Database error: {e}")
        response_data = { 
            "status": "02", 
            "message": "Something went wrong. Please try after some time.",
        }
        error_message = f"Database error: {e}"
        create_log("fetch_bank_details",json.dumps(await request.json()),json.dumps(req_header),'{"detail":"Internal Server Error"}','Error',error_message)
        return JSONResponse(content=response_data, status_code=200) 
    finally:
         print(f"Database error: Finally")

class InsertBankDetails(BaseModel):
    AccountNo : str
    BankName : str
    AccountHolderName : str
    BranchName : str
    BankCode : str
    Salt : str
    Password: str

@router.post("/Insert_BankDetails", response_model=dict, name="Insert Bank Details")
async def insert_bank_details(request: Request,data: InsertBankDetails, 
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
       
        
        payload = {
            "bp": BP_Number,
            "operation" : "ADD",
            "AccountNo" : data.AccountNo,
            "BankName": data.BankName,
            "AccountHolderName": data.AccountHolderName,
            "BranchName": data.BranchName,
            "BankCode": data.BankCode
        }
        
        response = sf.apexecute('/MSG/InsertContractorBankDetails', method='POST', data=payload)
        
        create_log("insert_bank_details",json.dumps(await request.json()),json.dumps(req_header),json.dumps(response),'Info')
        return response

    except psycopg2.Error as e:
        # Handle database errors and return appropriate HTTP response
        print(f"Database error: {e}")
        response_data = { 
            "status": "02", 
            "message": "Something went wrong. Please try after some time.",
        }
        error_message = f"Database error: {e}"
        create_log("insert_bank_details",json.dumps(await request.json()),json.dumps(req_header),'{"detail":"Internal Server Error"}','Error',error_message)
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
        create_log("insert_bank_details",json.dumps(await request.json()),json.dumps(req_header),'{"detail":"Internal Server Error"}','Error',error_message)
        return JSONResponse(content=response_data, status_code=200) 
    except Exception as e:
        # Handle database errors and return appropriate HTTP response
        print(f"Database error: {e}")
        response_data = { 
            "status": "02", 
            "message": "Something went wrong. Please try after some time.",
        }
        error_message = f"Database error: {e}"
        create_log("insert_bank_details",json.dumps(await request.json()),json.dumps(req_header),'{"detail":"Internal Server Error"}','Error',error_message)
        return JSONResponse(content=response_data, status_code=200) 
    finally:
         print(f"Database error: Finally")


class UpdateRemoveBankDetails(BaseModel):
    AccountNo : str
    BankName : str
    AccountHolderName : str
    BranchName : str
    BankCode : str
    Operation : str
    Salt : str
    Password: str

@router.post("/Update_Remove_BankDetails", response_model=dict, name="Update Remove Bank Details")
async def update_remove_bank_details(request: Request,data: UpdateRemoveBankDetails, 
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
       
        operationType = data.Operation
        if operationType != 'U' and operationType != 'R' :
            return {
                "status" : "01",
                "message" : "Invalid Operation, Operation should be U or R"
            }
        
        payload = {
            "bp": BP_Number,
            "operation" : "UPDATE" if operationType == 'U' else 'DELETE',
            "AccountNo" : data.AccountNo,
            "BankName": data.BankName,
            "AccountHolderName": data.AccountHolderName,
            "BranchName": data.BranchName,
            "BankCode": data.BankCode
        }
        
        response = sf.apexecute('/MSG/InsertContractorBankDetails', method='POST', data=payload)
        
        create_log("update_remove_bank_details",json.dumps(await request.json()),json.dumps(req_header),json.dumps(response),'Info')
        return response

    except psycopg2.Error as e:
        # Handle database errors and return appropriate HTTP response
        print(f"Database error: {e}")
        response_data = { 
            "status": "02", 
            "message": "Something went wrong. Please try after some time.",
        }
        error_message = f"Database error: {e}"
        create_log("update_remove_bank_details",json.dumps(await request.json()),json.dumps(req_header),'{"detail":"Internal Server Error"}','Error',error_message)
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
        create_log("update_remove_bank_details",json.dumps(await request.json()),json.dumps(req_header),'{"detail":"Internal Server Error"}','Error',error_message)
        return JSONResponse(content=response_data, status_code=200)
    except Exception as e:
        # Handle database errors and return appropriate HTTP response
        print(f"Database error: {e}")
        response_data = { 
            "status": "02", 
            "message": "Something went wrong. Please try after some time.",
        }
        error_message = f"Database error: {e}"
        create_log("update_remove_bank_details",json.dumps(await request.json()),json.dumps(req_header),'{"detail":"Internal Server Error"}','Error',error_message)
        return JSONResponse(content=response_data, status_code=200)
    finally:
         print(f"Database error: Finally")


