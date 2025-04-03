from fastapi import Body,  HTTPException, Request, Header, APIRouter, UploadFile
from pydantic import BaseModel
import psycopg2
import psycopg2.extras 
from typing import List
from authenticator import verify_password
from typing import List, Optional
from fastapi.responses import JSONResponse
import json
from datetime import datetime
from db_connector import connection as db_connection
from salesforce_connector import sf
from utility import create_log
from simple_salesforce.exceptions import SalesforceError

router = APIRouter()

def convert_date(date_str: str) -> str:
    if date_str == "":
        return date_str
    # Define multiple formats to handle both input date formats
    for fmt in ("%d-%b-%Y", "%d-%B-%Y","%Y%m%d", "%Y%m%d%H%M%S"):
        try:
            return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    raise ValueError(f"Date format for {date_str} is not recognized")

class DData(BaseModel):
    Zaction: str
    Zzcno: str
    Zdealerid: str
    Zresult: str
    bpNumber: str
    salt: str
    password: str

class RequestBody(BaseModel):
    d: DData

@router.post("/PreferredDealer", response_model=dict, name="Insert Delete Pref Dealer")
async def insert_delete_pref_dealer(request: Request,
                       data: RequestBody
):
    try:
        req_header = {}
        con_bp_number = data.d.bpNumber
        cursor = db_connection.cursor()
        current_datetime = datetime.now()
        dealerBP = data.d.Zdealerid
        operationType = data.d.Zaction
        if operationType != 'ADD' and operationType != 'DELETE' :
            response = {
                "status" : "200",
                "message" : "Invalid type, Type should be ADD or DELETE"
            }
            create_log("insert_delete_pref_dealer",json.dumps(await request.json()),json.dumps(req_header),json.dumps(response),'Info')
            return response
        
        # query for get msb_account from bp_number
        query = f"""
                SELECT "BP_NUMBER", "NAME", "USER_TYPE", "EMAIL", "MOBILE_NUMBER", "BLOCK"
                FROM public."MSB_ACCOUNT"
                WHERE "BP_NUMBER" = '{dealerBP}'
            """

        cursor.execute(query)
        results = cursor.fetchall()

        if results is None or len(results)==0:
            response =  {
                "status" : "200",
                "message" : "Invalid Dealer ",
                "data":None
            }
            return response
        
        cursor.execute('''
            SELECT "DEALER_BP", "CONTRACTOR_BP"
            FROM public."MSB_PREF_DEALER" 
            WHERE "CONTRACTOR_BP" = %s AND "DEALER_BP" = %s 
        ''', (con_bp_number, dealerBP))
        
        result = cursor.fetchall()

        if result is None or len(result)==0:

            if operationType == 'DELETE':
                response =  {
                    "status" : "200",
                    "message" : "Dealer removal failed",
                    "data":None
                }
            
                create_log("insert_delete_pref_dealer",json.dumps(await request.json()),json.dumps(req_header),json.dumps(response),'Info')
                return response
            
            # create dealer
            add_dealer="""
                    INSERT INTO public."MSB_PREF_DEALER"
                        ("DEALER_BP","CONTRACTOR_BP",
                        "CREATED_BY", "CREATED_ON", "UPDATED_BY","UPDATED_ON")
                    VALUES
                        (%s,%s, %s, %s, %s, %s)
                    """

            # Extract values from estimate_data dictionary
            values = (
                dealerBP, con_bp_number, 
                con_bp_number,current_datetime, con_bp_number, current_datetime
            )

            # Execute the SQL query
            cursor.execute(add_dealer, values)
            response = {
                "status" : "200",
                "message" : "Success",
                "data":{
                    "Zaction":"ADD",
                    "Zzcno":data.d.Zzcno,
                    "Zresult":"ADD-SUCCESS",
                    "__metadata":"",
                    "Zdealerid":dealerBP
                }
            }
            create_log("insert_delete_pref_dealer",json.dumps(await request.json()),json.dumps(req_header),json.dumps(response),'Info')
            return response
        
        # For contractor and painter, update the cred table with passw
        else:
            if operationType == 'ADD':
                response = {
                    "status" : "200",
                    "message" : f"{dealerBP} is already Added",
                    "data":None
                }
                create_log("insert_delete_pref_dealer",json.dumps(await request.json()),json.dumps(req_header),json.dumps(response),'Info')
                return response
            
            delete_delaer = """
                DELETE FROM public."MSB_PREF_DEALER"
                WHERE "DEALER_BP" = %s AND "CONTRACTOR_BP" = %s
            """

            cursor.execute(delete_delaer, (dealerBP, con_bp_number,))
            response = {
                "status" : "200",
                "message" : "Success",
                "data":{
                    "Zaction":"DELETE",
                    "Zzcno":data.d.Zzcno,
                    "Zresult":"DELETE-SUCCESS",
                    "Zdealerid":dealerBP
                }
            }
            create_log("insert_delete_pref_dealer",json.dumps(await request.json()),json.dumps(req_header),json.dumps(response),'Info')
            return response
        
    except Exception as e:
        # Handle exceptions
        print("Exception:", e) 
        response = {
            "status": "200",
            "message": "Error Occurred",
            "data":None
        }
        error_message = f"Database error: {e}"
        create_log("insert_delete_pref_dealer",json.dumps(await request.json()),json.dumps(req_header),'{"detail":"Internal Server Error"}','Error',error_message)
        return JSONResponse(content=response, status_code=200) 
        
    finally:
        db_connection.commit()
        cursor.close()

class GetPrefDealer(BaseModel):
    salt : str
    password: str
    bpNumber: str

@router.post("/PreferredDealerList", response_model=dict, name="Get Pref Dealer")
async def get_pref_dealer(request: Request,
                       data: GetPrefDealer):
    
    try:
        con_bp_number = data.bpNumber if data.bpNumber else request.query_params.get("IP_CONTRACTOR")
        # convert Header Param to JSON
        req_header={}
       
        cursor = db_connection.cursor()
        
        cursor.execute('''
            SELECT a."DEALER_BP", a."CONTRACTOR_BP", b."NAME" ,b."ROLE", b."MOBILE_NUMBER"
            FROM public."MSB_PREF_DEALER" a
            INNER JOIN public."MSB_ACCOUNT" b
            ON a."DEALER_BP" = b."BP_NUMBER"  
            WHERE "CONTRACTOR_BP" = %s 
        ''', (con_bp_number,))
        
        result = cursor.fetchall()
        
        dealerRecords = [{
                "Dealer": row[0],
                "Contractor":row[1],
                "Dealer_Name": row[2],
                "mobileNo": row[4],
                "Role": row[3],
                "City":""
                } for row in result]
        
        response = {
            "status" : "200",
            "message" : "Success",
            "data": dealerRecords
        }
        create_log("get_pref_dealer",json.dumps(await request.json()),json.dumps(req_header),json.dumps(response),'Info')
        return response
        
    except Exception as e:
        # Handle exceptions
        print("Exception:", e)
        response_data = {
            "status": "400",
            "message": "Error Occurred",
            "data":None
        }
        error_message = f"Database error: {e}"
        create_log("get_pref_dealer",json.dumps(await request.json()),json.dumps(req_header),'{"detail":"Internal Server Error"}','Error',error_message)
        return JSONResponse(content=response_data, status_code=200) 
        
    finally:
        db_connection.commit()
        cursor.close()

class PrefBPSearch(BaseModel):
    bpNumber : str
    salt : str
    password: str

@router.post("/SearchDealer", response_model=dict, name="Pref BP Search")
async def searchDealer(request: Request,
                       data: PrefBPSearch,
                       BP_Number: Optional[str] = Header(None, title="BP_Number", convert_underscores=False),):
    try:
        
        dealer_bp_number = request.query_params.get("PARTNER")
        # convert Header Param to JSON
        req_header={"BP_Number":BP_Number}
       
        cursor = db_connection.cursor()
        
        cursor.execute('''
            SELECT "NAME", "EMAIL", "MOBILE_NUMBER", "ROLE" , "BLOCK"
            FROM public."MSB_ACCOUNT" 
            WHERE "BP_NUMBER" = %s AND "USER_TYPE" = %s
        ''', (dealer_bp_number,'DEALER',))
        
        result = cursor.fetchall()
        
        if result==None or len(result)==0:
            response = {
                "status" : "400",
                "message" : "Invalid Search"
            }
            create_log("searchDealer",json.dumps(await request.json()),json.dumps(req_header),json.dumps(response),'Info')
            return response
        
        dealerRecords = [{
                "Mandt": "122",
                "Mc_Name1": row[0],
                "Partner": dealer_bp_number,
                "Rltyp": row[3]
                } for row in result]
        
        response = {
            "status" : "200",
            "message" : "Success",
            "data": dealerRecords
        }
        create_log("searchDealer",json.dumps(await request.json()),json.dumps(req_header),json.dumps(response),'Info')
        return response
        
    except Exception as e:
        # Handle exceptions
        print("Exception:", e) 
        response_data = {
            "status": "400",
            "message": "Error Occurred"
        }
        error_message = f"Database error: {e}"
        create_log("searchDealer",json.dumps(await request.json()),json.dumps(req_header),'{"detail":"Internal Server Error"}','Error',error_message)
        return JSONResponse(content=response_data, status_code=200) 
        
    finally:
        db_connection.commit()
        cursor.close()


class RETURNSetItem(BaseModel):
    pass  # Empty object as per the given JSON

class ProdVolSetItem(BaseModel):
    Source: str
    Dealer: str
    Volume: str
    Contractor: str
    Prod: str

    # Method to convert object to a dictionary
    def to_dict(self):
        return {
            "Source": self.Source,
            "Dealer": self.Dealer,
            "Volume": self.Volume,
            "Contractor": self.Contractor,
            "Prod": self.Prod
        }

class DPUTransactionDetail(BaseModel):
    Id: str
    bpNumber: str
    salt: str
    password: str
    RETURNSet: List[RETURNSetItem]
    ProdVolSet: List[ProdVolSetItem]

class DPUTransactionRequest(BaseModel):
    d: DPUTransactionDetail
    

@router.post("/DpuTransaction", response_model=dict, name="Fetch Profile")
async def dpu_transaction(request: Request,data: DPUTransactionRequest, 
                                 BP_Number: Optional[str] = Header(None, title="BP_Number", convert_underscores=False)):
     
    bpNumber = data.d.bpNumber if data.d.bpNumber else BP_Number 
    try:
        # convert Header Param to JSON
        req_header={"BP_Number":BP_Number}
       
        cursor = db_connection.cursor()
        ProdVolSet = [ProdVolSet.to_dict() for ProdVolSet in data.d.ProdVolSet]
        payload = {
            "Id" : data.d.Id,
           "bpNumber": bpNumber,
           "ProdVolSet" : ProdVolSet
        }

        sf_response = sf.apexecute('/MSB/DPUTransaction', method='POST', data=payload)
        # for obj in response['data']:
        #     if 'dates' in obj:
        #         obj['date'] = obj.pop('dates')
        response = sf_response
        create_log("dpu_transaction",json.dumps(await request.json()),json.dumps(req_header),json.dumps(response),'Info')
        return response

    except psycopg2.Error as e:
        # Handle database errors and return appropriate HTTP response
        print(f"Database error: {e}")
        response_data = { 
            "status": "400", 
            "message": "Something went wrong. Please try after some time.",
        }
        error_message = f"Database error: {e}"
        create_log("dpu_transaction",json.dumps(await request.json()),json.dumps(req_header),'{"detail":"Internal Server Error"}','Error',error_message)
        return JSONResponse(content=response_data, status_code=200) 
    except SalesforceError as e:
        # Access the error message from the exception
        error_message = e.content[0]['message']
        print(f"Salesforce error: {error_message}")
        response_data = { 
            "status": "400", 
            "message": "Something went wrong. Please try after some time.",
        }
        error_message = f"Salesforce error: {e}"
        create_log("dpu_transaction",json.dumps(await request.json()),json.dumps(req_header),'{"detail":"Internal Server Error"}','Error',error_message)
        return JSONResponse(content=response_data, status_code=200) 
    except Exception as e:
        # Handle database errors and return appropriate HTTP response
        print(f"Database error: {e}")
        response_data = { 
            "status": "400", 
            "message": "Something went wrong. Please try after some time.",
        }
        error_message = f"Database error: {e}"
        create_log("dpu_transaction",json.dumps(await request.json()),json.dumps(req_header),'{"detail":"Internal Server Error"}','Error',error_message)
        return JSONResponse(content=response_data, status_code=200) 
    finally:
        db_connection.commit()
        cursor.close()


class ProductGroup(BaseModel):
    ProductGroup : str

    # Method to convert object to a dictionary
    def to_dict(self):
        return {
            "ProductGroup": self.ProductGroup
        }

class VolumeSummaryDetail(BaseModel):
    bpNumber: str
    salt: str
    password: str
    StartDate: str
    EndDate: str
    PageNumber: int
    nav_product_groups: Optional[List[ProductGroup]] = None


@router.post("/VolumeSummary", response_model=dict, name="Fetch Profile")
async def volumeSummary(request: Request,data: VolumeSummaryDetail, 
                                 BP_Number: Optional[str] = Header(None, title="BP_Number", convert_underscores=False)):
     
    bpNumber = data.bpNumber if data.bpNumber else BP_Number 
    try:
        # convert Header Param to JSON
        req_header={"BP_Number":BP_Number}
       
        cursor = db_connection.cursor()
        nav_product_groups = []
        if data.nav_product_groups != None:
            nav_product_groups = [nav_product_group.to_dict() for nav_product_group in data.nav_product_groups]

        payload = {
            "PageNumber" : data.PageNumber,
            "bpNumber": bpNumber,
            "StartDate": convert_date(data.StartDate),
            "EndDate" : convert_date(data.EndDate),
            "nav_product_groups" : nav_product_groups
        }

        sf_response = sf.apexecute('/MSB/VolumeSummary', method='POST', data=payload)
        # for obj in response['data']:
        #     if 'dates' in obj:
        #         obj['date'] = obj.pop('dates')
        response = sf_response
        create_log("volumeSummary",json.dumps(await request.json()),json.dumps(req_header),json.dumps(response),'Info')
        return response

    except psycopg2.Error as e:
        # Handle database errors and return appropriate HTTP response
        print(f"Database error: {e}")
        response_data = { 
            "status": "400", 
            "message": "Something went wrong. Please try after some time.",
        }
        error_message = f"Database error: {e}"
        create_log("volumeSummary",json.dumps(await request.json()),json.dumps(req_header),'{"detail":"Internal Server Error"}','Error',error_message)
        return JSONResponse(content=response_data, status_code=200) 
    except SalesforceError as e:
        # Access the error message from the exception
        error_message = e.content[0]['message']
        print(f"Salesforce error: {error_message}")
        response_data = { 
            "status": "400", 
            "message": "Something went wrong. Please try after some time.",
        }
        error_message = f"Salesforce error: {e}"
        create_log("volumeSummary",json.dumps(await request.json()),json.dumps(req_header),'{"detail":"Internal Server Error"}','Error',error_message)
        return JSONResponse(content=response_data, status_code=200) 
    except Exception as e:
        # Handle database errors and return appropriate HTTP response
        print(f"Database error: {e}")
        response_data = { 
            "status": "400", 
            "message": "Something went wrong. Please try after some time.",
        }
        error_message = f"Database error: {e}"
        create_log("volumeSummary",json.dumps(await request.json()),json.dumps(req_header),'{"detail":"Internal Server Error"}','Error',error_message)
        return JSONResponse(content=response_data, status_code=200) 
    finally:
        db_connection.commit()
        cursor.close()




class SearchTransactionDetail(BaseModel):
    bpNumber: str
    salt: str
    password: str


@router.post("/SearchTransactions", response_model=dict, name="Fetch Profile")
async def searchTransactions(request: Request,data: SearchTransactionDetail, 
                                 BP_Number: Optional[str] = Header(None, title="BP_Number", convert_underscores=False)):
     
    try:
        BP_Number = data.bpNumber if data.bpNumber else request.query_params.get("IP_CONTRACTOR")
        StartDate = request.query_params.get("start")
        EndDate = request.query_params.get("end")
        # convert Header Param to JSON
        req_header={"BP_Number":BP_Number}
       
        cursor = db_connection.cursor()
        payload = {
            "bpNumber": BP_Number,
            "StartDate": convert_date(StartDate),
            "EndDate" : convert_date(EndDate),
            "isSelfClaim" : 'false'
        }

        sf_response = sf.apexecute('/MSB/SearchTransaction', method='POST', data=payload)
        # for obj in response['data']:
        #     if 'dates' in obj:
        #         obj['date'] = obj.pop('dates')
        response = sf_response
        create_log("searchTransactions",json.dumps(await request.json()),json.dumps(req_header),json.dumps(response),'Info')
        return response

    except psycopg2.Error as e:
        # Handle database errors and return appropriate HTTP response
        print(f"Database error: {e}")
        response_data = { 
            "status": "400", 
            "message": "Something went wrong. Please try after some time.",
        }
        error_message = f"Database error: {e}"
        create_log("searchTransactions",json.dumps(await request.json()),json.dumps(req_header),'{"detail":"Internal Server Error"}','Error',error_message)
        return JSONResponse(content=response_data, status_code=200) 
    except SalesforceError as e:
        # Access the error message from the exception
        error_message = e.content[0]['message']
        print(f"Salesforce error: {error_message}")
        response_data = { 
            "status": "400", 
            "message": "Something went wrong. Please try after some time.",
        }
        error_message = f"Salesforce error: {e}"
        create_log("searchTransactions",json.dumps(await request.json()),json.dumps(req_header),'{"detail":"Internal Server Error"}','Error',error_message)
        return JSONResponse(content=response_data, status_code=200) 
    except Exception as e:
        # Handle database errors and return appropriate HTTP response
        print(f"Database error: {e}")
        response_data = { 
            "status": "400", 
            "message": "Something went wrong. Please try after some time.",
        }
        error_message = f"Database error: {e}"
        create_log("searchTransactions",json.dumps(await request.json()),json.dumps(req_header),'{"detail":"Internal Server Error"}','Error',error_message)
        return JSONResponse(content=response_data, status_code=200) 
    finally:
        db_connection.commit()
        cursor.close()



class SelfClaimDetail(BaseModel):
    bpNumber: str
    salt: str
    password: str


@router.post("/SelfClaim", response_model=dict, name="Self Claim")
async def selfClaim(request: Request,data: SelfClaimDetail, 
                                 BP_Number: Optional[str] = Header(None, title="BP_Number", convert_underscores=False)):
     
    try:
        BP_Number = data.bpNumber if data.bpNumber else request.query_params.get("IP_CONTRACTOR")
        StartDate = request.query_params.get("start")
        EndDate = request.query_params.get("end")
        # convert Header Param to JSON
        req_header={"BP_Number":BP_Number}
       
        cursor = db_connection.cursor()
        payload = {
            "bpNumber": BP_Number,
            "StartDate": convert_date(StartDate),
            "EndDate" : convert_date(EndDate),
            "isSelfClaim" : 'true'
        }

        sf_response = sf.apexecute('/MSB/SearchTransaction', method='POST', data=payload)
        # for obj in response['data']:
        #     if 'dates' in obj:
        #         obj['date'] = obj.pop('dates')
        response = sf_response
        create_log("selfClaim",json.dumps(await request.json()),json.dumps(req_header),json.dumps(response),'Info')
        return response

    except psycopg2.Error as e:
        # Handle database errors and return appropriate HTTP response
        print(f"Database error: {e}")
        response_data = { 
            "status": "400", 
            "message": "Something went wrong. Please try after some time.",
        }
        error_message = f"Database error: {e}"
        create_log("selfClaim",json.dumps(await request.json()),json.dumps(req_header),'{"detail":"Internal Server Error"}','Error',error_message)
        return JSONResponse(content=response_data, status_code=200) 
    except SalesforceError as e:
        # Access the error message from the exception
        error_message = e.content[0]['message']
        print(f"Salesforce error: {error_message}")
        response_data = { 
            "status": "400", 
            "message": "Something went wrong. Please try after some time.",
        }
        error_message = f"Salesforce error: {e}"
        create_log("selfClaim",json.dumps(await request.json()),json.dumps(req_header),'{"detail":"Internal Server Error"}','Error',error_message)
        return JSONResponse(content=response_data, status_code=200) 
    except Exception as e:
        # Handle database errors and return appropriate HTTP response
        print(f"Database error: {e}")
        response_data = { 
            "status": "400", 
            "message": "Something went wrong. Please try after some time.",
        }
        error_message = f"Database error: {e}"
        create_log("selfClaim",json.dumps(await request.json()),json.dumps(req_header),'{"detail":"Internal Server Error"}','Error',error_message)
        return JSONResponse(content=response_data, status_code=200) 
    finally:
        db_connection.commit()
        cursor.close()