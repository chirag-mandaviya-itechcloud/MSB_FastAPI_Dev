from fastapi import FastAPI, HTTPException, Header, status, Request,Depends
from fastapi.responses import JSONResponse
from db_connector import db_connection
import traceback
from urllib.parse import urlparse
import urllib3
from typing import List, Optional
from authenticator import router as authenticator
from authenticator import verify_password
from starlette.requests import Request
from starlette.concurrency import iterate_in_threadpool
import os
from ProfileAPI import router as ProfileAPI
from LoginAPI import router as LoginAPI
from ScanBarcode import router as ScanBarcode
from DPUAPI import router as DPUAPI
from LanguageAPI import router as LanguageAPI
from Get_Notification_List import router as Get_Notification_List



app = FastAPI() 

# Initialize the database connection
app.db_connection = db_connection


bypass_header_passw_check_apis = {
    "/docs",
    "/openapi.json",
    "http://127.0.0.1:8000/openapi.json",
    "http://127.0.0.1:8000/",
    "http://127.0.0.1:8000/docs",
}

bypass_passw_check_apis = {
    "/v1/msb_contractor_app/BPCheck",
    "/v1/msb_contractor_app/ValidateOtpNoUpdate",
    "/v1/msb_contractor_app/ValidateOtp",
    "/v1/msb_contractor/ForgotPassword",
    "/v1/msb_contractor_app/ForgotPassword",
    "/v1/msb_contractor_app/ChangePassword",
    "/v1/msb_contractor_app/SignUpNew",
    "/v1/msb_sms_rp/DealerAPP_BarcodeScan",
    "/v1/msb_contractor_app/SendSMS",
    "/v1/msb_contractor_app/Get_Notification_List"
    
}

@app.middleware("http")
async def protect_api_routes(request: Request, call_next):
    bypasshp = os.environ.get("ByPassHeaderPassw", "N")
    request_body = await request.body()
    print("\n\nRequest Body\n")
    print(request_body)
    print("\n\nRequest Headers\n")
    print(request.headers)
    print("\n\n")
    if bypasshp == "N":
        try:
            if request.url.path in bypass_header_passw_check_apis:
                response = await call_next(request)
                if response.status_code==422:
                    print(response.status_code)
                    return JSONResponse(status_code=400, content={"status": "02", "message": "Exception occured while parsing json request."})
                print("\n\nResponse Body:\n")
                response_body = [section async for section in response.body_iterator]
                response.body_iterator = iterate_in_threadpool(iter(response_body))
                print(f"response_body => {response_body[0].decode()}")
                print("\n\n")
                return response

            if request.url.path in bypass_passw_check_apis:
                response = await call_next(request)
                if response.status_code == 422:
                    print(response.status_code)
                    return JSONResponse(status_code=400, content={"status": "02", "message": "Exception occured while parsing json request."})
                print("\n\nResponse Body:\n")
                response_body = [section async for section in response.body_iterator]
                response.body_iterator = iterate_in_threadpool(iter(response_body))
                print(f"response_body => {response_body[0].decode()}")
                print("\n\n")
                return response
            
            if request.method=='GET':
                if request.url.path in bypass_passw_check_apis:
                    response = await call_next(request)
                    if response.status_code==422:
                        print(response.status_code)
                        return JSONResponse(status_code=400, content={"status": "02", "message": "Exception occured while parsing json request."})
                    print("\n\nResponse Body:\n")
                    response_body = [section async for section in response.body_iterator]
                    response.body_iterator = iterate_in_threadpool(iter(response_body))
                    print(f"response_body => {response_body[0].decode()}")
                    print("\n\n")
                    return response

            data = await request.json()
            password = data.get("Password") or data.get("password") or data.get("d", {}).get("password")
            bpNumber = data.get("bpNumber") or data.get("bpNumber") or data.get("d", {}).get("bpNumber")
            salt = data.get("Salt") or data.get("salt") or data.get("d", {}).get("salt")
            if not password or not salt:
                raise HTTPException(status_code=400, detail="Password and Salt must be provided in the request body.")

            request.state.password = password
            request.state.salt = salt
            request.state.bp_number = request.headers.get("BP_Number", "")
            # request.state.app_ver = required_headers["App_Ver"]
            # request.state.android_ver = required_headers["Android_Ver"]
            # request.state.device_id = required_headers["Device_Id"]
            # request.state.device_mod = required_headers["Device_Mod"]
            # request.state.source = required_headers["Source"]

            if request.state.bp_number is None or request.state.bp_number == '':
                request.state.bp_number = bpNumber
                
                if request.state.bp_number == "" or request.state.bp_number is None:
                    request.state.bp_number = data.get("d", {}).get("bpNumber")

            try:
                result = verify_password(password, salt, request.state.bp_number, request.app.db_connection)
                if result.get("status") == "0":
                                        
                    response = await call_next(request)
                    if response.status_code == 422:
                        print(response.status_code)
                        return JSONResponse(status_code=400, content={"status": "02", "message": "Exception occured while parsing json request."})
                    print("\n\nResponse Body:\n")
                    response_body = [section async for section in response.body_iterator]
                    response.body_iterator = iterate_in_threadpool(iter(response_body))
                    print(f"response_body => {response_body[0].decode()}")
                    print("\n\n")
                    return response
                else:
                    return JSONResponse(status_code=401, content={"status": "01", "message": "Password Match Failed."})
            except Exception as exc:
                return JSONResponse(status_code=401, content={"status": "01", "message": "Error Occured.", "error": str(exc)})
        except Exception as exc:
            return JSONResponse(status_code=200, content={'Reason': str(exc)})
    else:
        try:
            response = await call_next(request)
            if response.status_code == 422:
                print(response.status_code)
                return JSONResponse(status_code=400, content={"status": "02", "message": "Exception occured while parsing json request."})
            print("\n\nResponse Body:\n")
            response_body = [section async for section in response.body_iterator]
            response.body_iterator = iterate_in_threadpool(iter(response_body))
            print(f"response_body => {response_body[0].decode()}")
            print("\n\n")
            return response
        except Exception as exc:
            return JSONResponse(status_code=500, content={'reason': str(exc)})

# Mount the different FastAPI apps as sub-apps
app.include_router(ProfileAPI, prefix="/v1/msb_contractor_app")
app.include_router(ProfileAPI, prefix="/v1/msb_contractor")
app.include_router(LoginAPI, prefix="/v1/msb_contractor_app")
app.include_router(LoginAPI, prefix="/v1/msb_contractor")
app.include_router(ScanBarcode, prefix="/v1/msb_contractor_app")
app.include_router(ScanBarcode, prefix="/v1/msb_sms_rp")

app.include_router(DPUAPI, prefix="/v1/msb_contractor_app")
app.include_router(DPUAPI, prefix="/v1/msb_contractor")
app.include_router(LanguageAPI, prefix="/v1/msb_contractor_app")
app.include_router(Get_Notification_List, prefix="/v1/msb_contractor_app")
