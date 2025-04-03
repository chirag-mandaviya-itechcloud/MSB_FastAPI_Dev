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

class RedemptionHisotryDetails(BaseModel):
    Salt: str = ""
    Password: str = ""
    TransactionStatus : str = ""
    PageNumber : int = 1
    StartDate : str = ""
    EndDate : str = ""

@router.post("/Redemption_History", response_model=dict, name="Redemption Details")
async def redemption_history_detail(request: Request,data: RedemptionHisotryDetails, 
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
            "PageNumber" : data.PageNumber,
            "TransactionStatus": data.TransactionStatus,
            "StartDate": convert_date(data.StartDate),
            "EndDate" : convert_date(data.EndDate)
        }

        response = sf.apexecute('/MSG/RedemptionHistory', method='POST', data=payload)
        
        create_log("redemption_history_detail",json.dumps(await request.json()),json.dumps(req_header),json.dumps(response),'Info')
        return response

    except psycopg2.Error as e:
        # Handle database errors and return appropriate HTTP response
        print(f"Database error: {e}")
        response_data = { 
            "status": "02", 
            "message": "Something went wrong. Please try after some time.",
        }
        error_message = f"Database error: {e}"
        create_log("redemption_history_detail",json.dumps(await request.json()),json.dumps(req_header),'{"detail":"Internal Server Error"}','Error',error_message)
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
        create_log("redemption_history_detail",json.dumps(await request.json()),json.dumps(req_header),'{"detail":"Internal Server Error"}','Error',error_message)
        return JSONResponse(content=response_data, status_code=200)
    except Exception as e:
        # Handle database errors and return appropriate HTTP response
        print(f"Database error: {e}")
        response_data = { 
            "status": "02", 
            "message": "Something went wrong. Please try after some time.",
        }
        error_message = f"Database error: {e}"
        create_log("redemption_history_detail",json.dumps(await request.json()),json.dumps(req_header),'{"detail":"Internal Server Error"}','Error',error_message)
        return JSONResponse(content=response_data, status_code=200)
    finally:
        db_connection.commit()
        cursor.close()

class CancelRedemptionDetails(BaseModel):
    Salt: str = ""
    Password: str = ""
    TransactionId : int

@router.post("/Cancel_Redemption_Request", response_model=dict, name="Redemption Details")
async def cancel_redemption_detail(request: Request,data: CancelRedemptionDetails, 
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
            "TransactionId" : data.TransactionId
        }

        response = sf.apexecute('/MSG/CancelRedemption', method='POST', data=payload)
        
        create_log("cancel_redemption_detail",json.dumps(await request.json()),json.dumps(req_header),json.dumps(response),'Info')
        return response

    except psycopg2.Error as e:
        # Handle database errors and return appropriate HTTP response
        print(f"Database error: {e}")
        response_data = { 
            "status": "02", 
            "message": "Something went wrong. Please try after some time.",
        }
        error_message = f"Database error: {e}"
        create_log("cancel_redemption_detail",json.dumps(await request.json()),json.dumps(req_header),'{"detail":"Internal Server Error"}','Error',error_message)
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
        create_log("cancel_redemption_detail",json.dumps(await request.json()),json.dumps(req_header),'{"detail":"Internal Server Error"}','Error',error_message)
        return JSONResponse(content=response_data, status_code=200)
    except Exception as e:
        # Handle database errors and return appropriate HTTP response
        print(f"Database error: {e}")
        response_data = { 
            "status": "02", 
            "message": "Something went wrong. Please try after some time.",
        }
        error_message = f"Database error: {e}"
        create_log("cancel_redemption_detail",json.dumps(await request.json()),json.dumps(req_header),'{"detail":"Internal Server Error"}','Error',error_message)
        return JSONResponse(content=response_data, status_code=200)
    finally:
        db_connection.commit()
        cursor.close()



class ProductInfo(BaseModel):
    ProductId: int
    Quantity: int
    GiftName: str
    # Method to convert object to a dictionary
    def to_dict(self):
        return {
            "ProductId": self.ProductId,
            "Quantity": self.Quantity,
            "GiftName": self.GiftName
        }
    
class RedemptionDetails(BaseModel):
    Salt: str = ""
    Password: str = ""
    Points : int
    GiftType : str
    ProductInform : List[ProductInfo]
    BankKey : str

@router.post("/Redemption_Details", response_model=dict, name="Redemption Details")
async def redemption_detail(request: Request,data: RedemptionDetails, 
                                BP_Number: str = Header(..., convert_underscores=False),
                                App_Ver: str = Header(..., convert_underscores=False),
                                Android_Ver: str = Header(..., convert_underscores=False),
                                Device_Id: str = Header(..., convert_underscores=False),
                                Device_Mod: str = Header(..., convert_underscores=False),
                                Source: str = Header(..., convert_underscores=False)):
     
    try:
        response = {
            "status": "03",
            "message": "UnSuccessful",
            "data": None
        }
        # convert Header Param to JSON
        req_header={"BP_Number":BP_Number,"App_Ver":App_Ver,"Android_Ver":Android_Ver,
                    "Device_Id":Device_Id,"Device_Mod":Device_Mod,"Source":Source}
       
        cursor = db_connection.cursor()
        
        query = f"""
                SELECT "BP_NUMBER" , "BLOCK"
                FROM public."MSG_ACCOUNT" 
                WHERE "BP_NUMBER" = %s
            """

        cursor.execute(query, (BP_Number,))
        
        results = cursor.fetchall()         
        
        for res in results:
            if res[1]!=None and res[1]!='N':
                response = {
                    "status": "03",
                    "message": "UnSuccessful",
                    "data": None
                }
                return response
        
        product_list_dicts = [product.to_dict() for product in data.ProductInform]

        payload = {
            "bp": BP_Number,
            "BankKey" : data.BankKey,
            "Points" : data.Points,
            "ProductInform": product_list_dicts,
            "GiftType": data.GiftType
        }

        response = sf.apexecute('/MSG/RedemptionDetail', method='POST', data=payload)
        
        create_log("redemption_detail",json.dumps(await request.json()),json.dumps(req_header),json.dumps(response),'Info')
        return response

    except psycopg2.Error as e:
        # Handle database errors and return appropriate HTTP response
        print(f"Database error: {e}")
        response_data = { 
            "status": "02", 
            "message": "Something went wrong. Please try after some time.",
        }
        error_message = f"Database error: {e}"
        create_log("redemption_detail",json.dumps(await request.json()),json.dumps(req_header),'{"detail":"Internal Server Error"}','Error',error_message)
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
        create_log("redemption_detail",json.dumps(await request.json()),json.dumps(req_header),'{"detail":"Internal Server Error"}','Error',error_message)
        return JSONResponse(content=response_data, status_code=200)
    except Exception as e:
        # Handle database errors and return appropriate HTTP response
        print(f"Database error: {e}")
        response_data = { 
            "status": "02", 
            "message": "Something went wrong. Please try after some time.",
        }
        error_message = f"Database error: {e}"
        create_log("redemption_detail",json.dumps(await request.json()),json.dumps(req_header),'{"detail":"Internal Server Error"}','Error',error_message)
        return JSONResponse(content=response_data, status_code=200)
    finally:
        db_connection.commit()
        cursor.close()


class RedemptionCheckDetails(BaseModel):
    Salt: str = ""
    Password: str = ""
    balancePoints : str = ""

@router.post("/Redemption_Check", response_model=dict, name="Redemption Details")
async def redemption_check_detail(request: Request,data: RedemptionCheckDetails, 
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
       
        balance_points = float(data.balancePoints)

        # Determine the response data based on balancePoints
        if balance_points < 5001:
            response_data = []
        elif 5001 <= balance_points < 10001:
            response_data = ["5001"]
        elif 10001 <= balance_points < 15001:
            response_data = ["5001", "10001"]
        else:
            response_data = ["5001.0", "10001.0", "15001.0"]

        response = {
            "status": "0",
            "message": "Success",
            "data": response_data,
        }
        
        create_log("redemption_check_detail",json.dumps(await request.json()),json.dumps(req_header),json.dumps(response),'Info')
        return response

    except psycopg2.Error as e:
        # Handle database errors and return appropriate HTTP response
        print(f"Database error: {e}")
        response_data = { 
            "status": "02", 
            "message": "Something went wrong. Please try after some time.",
        }
        error_message = f"Database error: {e}"
        create_log("redemption_check_detail",json.dumps(await request.json()),json.dumps(req_header),'{"detail":"Internal Server Error"}','Error',error_message)
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
        create_log("redemption_check_detail",json.dumps(await request.json()),json.dumps(req_header),'{"detail":"Internal Server Error"}','Error',error_message)
        return JSONResponse(content=response_data, status_code=200)
    except Exception as e:
        # Handle database errors and return appropriate HTTP response
        print(f"Database error: {e}")
        response_data = { 
            "status": "02", 
            "message": "Something went wrong. Please try after some time.",
        }
        error_message = f"Database error: {e}"
        create_log("redemption_check_detail",json.dumps(await request.json()),json.dumps(req_header),'{"detail":"Internal Server Error"}','Error',error_message)
        return JSONResponse(content=response_data, status_code=200)
