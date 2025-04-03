from fastapi import  HTTPException, Header, status, Request ,APIRouter, UploadFile
from pydantic import BaseModel
import psycopg2
from typing import List, Optional
from db_connector import connection as db_connection
from salesforce_connector import sf
from simple_salesforce.exceptions import SalesforceError
from fastapi.responses import JSONResponse

from utility import create_log
import json

router = APIRouter()

     

class FetchProfile(BaseModel):
    Salt: str = ""
    Password: str = ""
    bpNumber: str = ""

@router.post("/GetProfile", response_model=dict, name="Fetch Profile")
async def fetch_profile(request: Request,data: FetchProfile, 
                                 BP_Number: Optional[str] = Header(None, title="BP_Number", convert_underscores=False)):
     
    bpNumber = data.bpNumber if data.bpNumber else BP_Number 
    try:
        # convert Header Param to JSON
        req_header={"BP_Number":BP_Number}
       
        cursor = db_connection.cursor()
        
        query = f"""
                SELECT a."NAME" , a."LANGUAGE_ID" , a."PROFILE_URL", a."MOBILE_NUMBER", a."USER_TYPE",
                a."ROLE", a."BLOCK"
                FROM public."MSB_ACCOUNT" a
                WHERE a."BP_NUMBER" = %s 
            """

        cursor.execute(query, (bpNumber,))
        
        results = cursor.fetchall()  
        
        if results==None or len(results)==0:  
            response = {
                "status": "01",
                "message": "Failed to Fetch BP Check Info.",
                "data": None
            }
            create_log("fetch_profile",json.dumps({"BP_Number":bpNumber}),json.dumps(req_header),json.dumps(response),'Info')
            return response
        
        for res in results:
            validity = "VALID" if res[6]==None or res[6]=='N' else "INVALID"
            

        if validity == 'INVALID' :
            response = {
                "status": "07",
                "message": "Your account has been blocked, Kindly connect with Asian Paints Causeway.",
                "data": None
            }
            create_log("fetch_profile",json.dumps({"BP_Number":bpNumber}),json.dumps(req_header),json.dumps(response),'Info')
            return response
        
        payload = {
           "bpNumber": bpNumber
        }

        sf_response = sf.apexecute('/MSB/Profile', method='POST', data=payload)
        # for obj in response['data']:
        #     if 'dates' in obj:
        #         obj['date'] = obj.pop('dates')
        response = sf_response
        create_log("fetch_profile",json.dumps(await request.json()),json.dumps(req_header),json.dumps(response),'Info')
        return response

    except psycopg2.Error as e:
        # Handle database errors and return appropriate HTTP response
        print(f"Database error: {e}")
        response_data = { 
            "status": "02", 
            "message": "Something went wrong. Please try after some time.",
        }
        error_message = f"Database error: {e}"
        create_log("fetch_profile",json.dumps(await request.json()),json.dumps(req_header),'{"detail":"Internal Server Error"}','Error',error_message)
        return JSONResponse(content=response_data, status_code=200) 
    except SalesforceError as e:
        # Access the error message from the exception
        error_message = e.content[0]['message']
        print(f"Salesforce error: {error_message}")
        response_data = { 
            "status": "02", 
            "message": "Something went wrong. Please try after some time.",
        }
        error_message = f"Salesforce error: {e}"
        create_log("fetch_profile",json.dumps(await request.json()),json.dumps(req_header),'{"detail":"Internal Server Error"}','Error',error_message)
        return JSONResponse(content=response_data, status_code=200) 
    except Exception as e:
        # Handle database errors and return appropriate HTTP response
        print(f"Database error: {e}")
        response_data = { 
            "status": "02", 
            "message": "Something went wrong. Please try after some time.",
        }
        error_message = f"Database error: {e}"
        create_log("fetch_profile",json.dumps(await request.json()),json.dumps(req_header),'{"detail":"Internal Server Error"}','Error',error_message)
        return JSONResponse(content=response_data, status_code=200) 
    finally:
        db_connection.commit()
        cursor.close()

class LoyalityPoints(BaseModel):
    Salt: str = ""
    Password: str = ""
    bpNumber: str = ""

@router.post("/LoyalityPoints", response_model=dict, name="Loyality Points")
async def loyalty_points(request: Request,data: LoyalityPoints, 
                                 BP_Number: Optional[str] = Header(None, title="BP_Number", convert_underscores=False)):
     
    bpNumber = data.bpNumber if data.bpNumber else BP_Number 
    try:
        # convert Header Param to JSON
        req_header={"BP_Number":BP_Number}
       
        cursor = db_connection.cursor()
        
        payload = {
           "bpNumber": bpNumber
        }

        sf_response = sf.apexecute('/MSB/LoyalityPoints', method='POST', data=payload)
        # for obj in response['data']:
        #     if 'dates' in obj:
        #         obj['date'] = obj.pop('dates')
        response = sf_response
        create_log("loyalty_points",json.dumps(await request.json()),json.dumps(req_header),json.dumps(response),'Info')
        return response

    except psycopg2.Error as e:
        # Handle database errors and return appropriate HTTP response
        print(f"Database error: {e}")
        response_data = { 
            "status": "02", 
            "message": "Something went wrong. Please try after some time.",
        }
        error_message = f"Database error: {e}"
        create_log("loyalty_points",json.dumps(await request.json()),json.dumps(req_header),'{"detail":"Internal Server Error"}','Error',error_message)
        return JSONResponse(content=response_data, status_code=200) 
    except SalesforceError as e:
        # Access the error message from the exception
        error_message = e.content[0]['message']
        print(f"Salesforce error: {error_message}")
        response_data = { 
            "status": "02", 
            "message": "Something went wrong. Please try after some time.",
        }
        error_message = f"Salesforce error: {e}"
        create_log("loyalty_points",json.dumps(await request.json()),json.dumps(req_header),'{"detail":"Internal Server Error"}','Error',error_message)
        return JSONResponse(content=response_data, status_code=200) 
    except Exception as e:
        # Handle database errors and return appropriate HTTP response
        print(f"Database error: {e}")
        response_data = { 
            "status": "02", 
            "message": "Something went wrong. Please try after some time.",
        }
        error_message = f"Database error: {e}"
        create_log("loyalty_points",json.dumps(await request.json()),json.dumps(req_header),'{"detail":"Internal Server Error"}','Error',error_message)
        return JSONResponse(content=response_data, status_code=200) 
    finally:
        db_connection.commit()
        cursor.close()


class ProductDetail(BaseModel):
    salt: str = ""
    password: str = ""
    bpNumber: str = ""

@router.post("/Products", response_model=dict, name="Products")
async def product_details(request: Request,data: ProductDetail, 
                                 BP_Number: Optional[str] = Header(None, title="BP_Number", convert_underscores=False)):
     
    bpNumber = data.bpNumber if data.bpNumber else BP_Number 
    try:
        # convert Header Param to JSON
        req_header={"BP_Number":BP_Number}
       
        cursor = db_connection.cursor()
        
        payload = {
           "bpNumber": bpNumber
        }

        sf_response = sf.apexecute('/MSB/Products', method='POST', data=payload)
        # for obj in response['data']:
        #     if 'dates' in obj:
        #         obj['date'] = obj.pop('dates')
        response = sf_response
        create_log("Products",json.dumps(await request.json()),json.dumps(req_header),json.dumps(response),'Info')
        return response

    except psycopg2.Error as e:
        # Handle database errors and return appropriate HTTP response
        print(f"Database error: {e}")
        response_data = { 
            "status": "02", 
            "message": "Something went wrong. Please try after some time.",
        }
        error_message = f"Database error: {e}"
        create_log("Products",json.dumps(await request.json()),json.dumps(req_header),'{"detail":"Internal Server Error"}','Error',error_message)
        return JSONResponse(content=response_data, status_code=200) 
    except SalesforceError as e:
        # Access the error message from the exception
        error_message = e.content[0]['message']
        print(f"Salesforce error: {error_message}")
        response_data = { 
            "status": "02", 
            "message": "Something went wrong. Please try after some time.",
        }
        error_message = f"Salesforce error: {e}"
        create_log("Products",json.dumps(await request.json()),json.dumps(req_header),'{"detail":"Internal Server Error"}','Error',error_message)
        return JSONResponse(content=response_data, status_code=200) 
    except Exception as e:
        # Handle database errors and return appropriate HTTP response
        print(f"Database error: {e}")
        response_data = { 
            "status": "02", 
            "message": "Something went wrong. Please try after some time.",
        }
        error_message = f"Database error: {e}"
        create_log("Products",json.dumps(await request.json()),json.dumps(req_header),'{"detail":"Internal Server Error"}','Error',error_message)
        return JSONResponse(content=response_data, status_code=200) 
    finally:
        db_connection.commit()
        cursor.close()


class ProductGroups(BaseModel):
    ProductGroup: str = ""

    # Method to convert object to a dictionary
    def to_dict(self):
        return {
            "ProductGroup": self.ProductGroup
        }
     

class ProductGroupDetail(BaseModel):
    salt: str = ""
    password: str = ""
    bpNumber: str = ""
    nav_product_groups: Optional[List[ProductGroups]] = None 
    

@router.post("/Product_group", response_model=dict, name="Product_group")
async def product_details(request: Request,data: ProductGroupDetail, 
                                 BP_Number: Optional[str] = Header(None, title="BP_Number", convert_underscores=False)):
     
    bpNumber = data.bpNumber if data.bpNumber else BP_Number 
    try:
        # convert Header Param to JSON
        req_header={"BP_Number":bpNumber}
       
        cursor = db_connection.cursor()
        
        productGroups = [nav_product_groups.to_dict() for nav_product_groups in (data.nav_product_groups or [])]
        
        payload = {
            "bpNumber": bpNumber,
            "nav_product_groups" : productGroups
        }

        sf_response = sf.apexecute('/MSB/ProductGroup', method='POST', data=payload)
       
        response = sf_response
        create_log("Product_group",json.dumps(await request.json()),json.dumps(req_header),json.dumps(response),'Info')
        return response

    except psycopg2.Error as e:
        # Handle database errors and return appropriate HTTP response
        print(f"Database error: {e}")
        response_data = { 
            "status": "02", 
            "message": "Something went wrong. Please try after some time.",
        }
        error_message = f"Database error: {e}"
        create_log("Product_group",json.dumps(await request.json()),json.dumps(req_header),'{"detail":"Internal Server Error"}','Error',error_message)
        return JSONResponse(content=response_data, status_code=200) 
    except SalesforceError as e:
        # Access the error message from the exception
        error_message = e.content[0]['message']
        print(f"Salesforce error: {error_message}")
        response_data = { 
            "status": "02", 
            "message": "Something went wrong. Please try after some time.",
        }
        error_message = f"Salesforce error: {e}"
        create_log("Product_group",json.dumps(await request.json()),json.dumps(req_header),'{"detail":"Internal Server Error"}','Error',error_message)
        return JSONResponse(content=response_data, status_code=200) 
    except Exception as e:
        # Handle database errors and return appropriate HTTP response
        print(f"Database error: {e}")
        response_data = { 
            "status": "02", 
            "message": "Something went wrong. Please try after some time.",
        }
        error_message = f"Database error: {e}"
        create_log("Product_group",json.dumps(await request.json()),json.dumps(req_header),'{"detail":"Internal Server Error"}','Error',error_message)
        return JSONResponse(content=response_data, status_code=200) 
    finally:
        db_connection.commit()
        cursor.close()


class ProductVolDetail(BaseModel):
    salt: str = ""
    password: str = ""
    bpNumber: str = ""

@router.post("/ProductVolumeByDealer", response_model=dict, name="Products")
async def product_details(request: Request,data: ProductVolDetail, 
                                 BP_Number: Optional[str] = Header(None, title="BP_Number", convert_underscores=False)):
     
    bpNumber = data.bpNumber if data.bpNumber else BP_Number 
    dealer_bp_number = request.query_params.get("DealerBp")
    try:
        # convert Header Param to JSON
        req_header={"BP_Number":BP_Number}
       
        cursor = db_connection.cursor()
        
        payload = {
           "bpNumber": bpNumber,
           "dealerBp" : dealer_bp_number
        }

        sf_response = sf.apexecute('/MSB/ProductsByVolumeDealer', method='POST', data=payload)
        # for obj in response['data']:
        #     if 'dates' in obj:
        #         obj['date'] = obj.pop('dates')
        response = sf_response
        create_log("Products",json.dumps(await request.json()),json.dumps(req_header),json.dumps(response),'Info')
        return response

    except psycopg2.Error as e:
        # Handle database errors and return appropriate HTTP response
        print(f"Database error: {e}")
        response_data = { 
            "status": "02", 
            "message": "Something went wrong. Please try after some time.",
        }
        error_message = f"Database error: {e}"
        create_log("Products",json.dumps(await request.json()),json.dumps(req_header),'{"detail":"Internal Server Error"}','Error',error_message)
        return JSONResponse(content=response_data, status_code=200) 
    except SalesforceError as e:
        # Access the error message from the exception
        error_message = e.content[0]['message']
        print(f"Salesforce error: {error_message}")
        response_data = { 
            "status": "02", 
            "message": "Something went wrong. Please try after some time.",
        }
        error_message = f"Salesforce error: {e}"
        create_log("Products",json.dumps(await request.json()),json.dumps(req_header),'{"detail":"Internal Server Error"}','Error',error_message)
        return JSONResponse(content=response_data, status_code=200) 
    except Exception as e:
        # Handle database errors and return appropriate HTTP response
        print(f"Database error: {e}")
        response_data = { 
            "status": "02", 
            "message": "Something went wrong. Please try after some time.",
        }
        error_message = f"Database error: {e}"
        create_log("Products",json.dumps(await request.json()),json.dumps(req_header),'{"detail":"Internal Server Error"}','Error',error_message)
        return JSONResponse(content=response_data, status_code=200) 
    finally:
        db_connection.commit()
        cursor.close()


