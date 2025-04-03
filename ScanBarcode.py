from fastapi import Body, Request, Header, APIRouter
from pydantic import BaseModel
from fastapi.responses import JSONResponse
import requests
from datetime import datetime
from db_connector import connection as db_connection
from salesforce_connector import sf
from typing import Any, Optional
from utility import create_log, get_fiscal_year_dates, get_month_dates, sendSMS
import json
import os

router = APIRouter()


def convert_date(date_str: str) -> str:
    if date_str == "":
        return date_str
    # Define multiple formats to handle both input date formats
    for fmt in ("%d-%b-%Y", "%d-%B-%Y","%Y%m%d", "%Y%m%d%H%M%S","%Y-%m-%dT%H:%M:%SZ","%Y-%m-%dT%H:%M:%S","%Y-%m-%d %H:%M:%S","%Y-%m-%d"):
        try:
            return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    raise ValueError(f"Date format for {date_str} is not recognized")


class DataRequest(BaseModel):
    ImScratchCode: str
    ImCntmobile: str
    ImSource: str
    bpNumber: str
    salt: str
    password: str

class ScanBarcodeDetails(BaseModel):
    d: DataRequest

@router.post("/ScanBarcode", response_model=dict)
async def scan_barcode(request: Request,
                         data: ScanBarcodeDetails, 
    BP_Number: Optional[str] = Header(None, title="BP_Number", convert_underscores=False),
):
    bp_number = data.d.bpNumber
    # convert Header Param to JSON
    req_header={"BP_Number":BP_Number}
    
    # response template
    RESPONSE = {
        "message": "Success",
        "status": "200",
        "data": {
            "ImCntmobile": data.d.ImCntmobile,
            "ImScratchCode": data.d.ImScratchCode,
            "ImSource": data.d.ImSource,
            "EvStatus": "NOT REGISTERED MSB PARTNER",
            "EvTransFrom": "",
            "Type": "E",
            "Id": "",
            "Number": "",
            "Message": "",
            "LogNo": "",
            "LogMsgNo": "",
            "MessageV1": "",
            "MessageV2": "",
            "MessageV3": "",
            "MessageV4": "",
            "Parameter": "",
            "Row": 0.0,
            "Field": "",
            "System": ""
        }
    }
    
    try:
       
        # create database cursor
        cursor = db_connection.cursor()

        # query for get msb_account from bp_number
        query = f"""
                SELECT "BP_NUMBER", "NAME", "USER_TYPE", "EMAIL", "MOBILE_NUMBER", "BLOCK", "LINKED_DEALER", "LINKED_DEALER_TERRITORY"
                FROM public."MSB_ACCOUNT"
                WHERE "BP_NUMBER" = '{bp_number}'
            """

        cursor.execute(query)
        results = cursor.fetchall()
        sequence_number =''

        if results:
            for res in results:
                bp_number = res[0]
                mobile_number = res[4]
                block_status = res[5]
                linkedDealer = res[6]
                linkedDealerTerritory = res[7]

            if block_status == 'Y':
                # response if account is blocked
                RESPONSE["data"]["code"] = 1
                RESPONSE["data"]["Message"] = "Sorry, Your account is blocked in system. Please speak to Asian paints dealer/sales officer to know more on the same."
                return RESPONSE

            if linkedDealer == None or linkedDealer == '' or linkedDealerTerritory == None or linkedDealerTerritory == '':
                # response if  account has ont linked dealer
                RESPONSE["data"]["code"] = 1
                RESPONSE["data"]["Message"] = "Please get in touch with nearest Asian Paints Delaer/Representative to know more."
                return RESPONSE
            
            # query for get link dealer msb_account from bp_number
            query = f"""
                    SELECT "BP_NUMBER", "NAME", "USER_TYPE", "EMAIL", "MOBILE_NUMBER", "BLOCK", "LINKED_DEALER", "LINKED_DEALER_TERRITORY"
                    FROM public."MSB_ACCOUNT"
                    WHERE "BP_NUMBER" = '{linkedDealer}'
                """

            cursor.execute(query)
            results = cursor.fetchall()
            
            if results is None or len(results) == 0:
                # response if there is not link-dealer account
                RESPONSE["data"]["code"] = 1
                RESPONSE["data"]["Message"] = "Please get in touch with nearest Asian Paints Delaer/Representative to know more."
                return RESPONSE
            else:
                for res in results:
                    region = res[7]
                    if region == "" or region is None:
                        # response if link-dealer has no region
                            RESPONSE["data"]["code"] = 1
                            RESPONSE["data"]["Message"] = "Please get in touch with nearest Asian Paints Delaer/Representative to know more."
                            return RESPONSE

            # get sku id from table
            query = f"""
                    SELECT "MATNR", "ZPACK"
                    FROM public."MSB_ZMSB_PBM_CI"
                    WHERE "ZBARCODE" = '{data.d.ImScratchCode}'
                """
                
            cursor.execute(query)
            sku_res = cursor.fetchall()
            sku_number = ''
            volume = 0
            if sku_res:
                for res in sku_res:
                    sku_number = res[0]
                    volume = float(res[1])
            else:
                # response when BP number not found
                RESPONSE["data"]["code"] = 1
                RESPONSE["data"]["Message"] = "Not a Valid Barcode - " + data.d.ImScratchCode
                create_log("bp_check",json.dumps({"BP_Number":BP_Number}),json.dumps(req_header),json.dumps(RESPONSE),'Info')
                return RESPONSE
            
            #sku_number = sku_res[0][0]
            #volume = sku_res[0][1]
            
            # query for get record for sku from master table
            query = f"""
                    SELECT "ZZAPG","ZZALP"
                    FROM public."MSB_ZMSB_BARCOD_MAST"
                    WHERE "ZZSKU" = '{sku_number}' AND "ZZAPR" = '{linkedDealerTerritory}'
                """
        
            cursor.execute(query)
            master_results = cursor.fetchall()
            
            if master_results is None or len(master_results) == 0:
                
                # response if there is not any record for that sku.
                RESPONSE["data"]["code"] = 1
                RESPONSE["data"]["Message"] = "Scan not successful. Please call helpline 18002093000 to raise complaint(CODE 01:BCDMAST)"

                return RESPONSE
            
            # 1. Fetch sequence number
            query = f""" SELECT nextval('public."MSB_ZMSB_BARCOD_SEQ"'); """
            cursor.execute(query)
            sequence_number = str(cursor.fetchone()[0])  # Extract the sequence value

            
            # get product group
            product_group = ""
            product_category = ""
            if master_results:
                for res in master_results:
                    product_group = res[0]
                    product_category = res[1]

            # query for get msb_account from bp_number for pending and successful
            query = f"""
                    SELECT "ZZCNO","ZBARCODE","CNTMOBILE", "ZSTATUS", "ZEND_SCAN","ZZATN"
                    FROM public."MSB_ZMSB_BARCOD_TRAN"
                    WHERE "ZBARCODE" = '{data.d.ImScratchCode}' AND "ZSTATUS" IN ('Pending', 'Successful')
                """

            cursor.execute(query)
            barcodeScanResult = cursor.fetchall()

            if barcodeScanResult:
                for res in barcodeScanResult:
                    barcodeBP = res[0]
                    barcode_code = res[1]
                    cnt_mobile = res[2]
                    barcodeStatus = res[3]
                    scanEndDate = res[4]
                    transactionNo = res[5]
                
                    if barcodeStatus == 'Pending':
                        RESPONSE["data"]["code"] = 1
                        RESPONSE["data"]["Message"] = "Scan is in progress."
                        # create transaction record for pending
                        sql_query="""
                            INSERT INTO public."MSB_ZMSB_BARCOD_TRAN"
                                ("ZZCNO","ZBARCODE","CNTMOBILE","ZSTATUS", "ZSTART_SCAN", "ZEND_SCAN", "ZZATN", "ZMESSAGE","ZZALP","ZZAPG")
                            VALUES
                                (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """

                        # Extract values from estimate_data dictionary
                        values = (
                            bp_number, data.d.ImScratchCode, data.d.ImCntmobile, "Fail", datetime.now(), datetime.now(), sequence_number,RESPONSE["data"]["Message"],product_category,product_group,
                        )
                        # Execute the SQL query
                        cursor.execute(sql_query, values)
                        
                        
                        return RESPONSE

                    if barcodeStatus == 'Successful':

                        RESPONSE["data"]["code"] = 1
                        RESPONSE["data"]["Message"] = f"Sorry. This barcode has already been scaned by {barcodeBP} on {scanEndDate} Transaction Id {transactionNo}."
                        RESPONSE["data"]["EvStatus"] = "USED SCRATCHCODE"
                        # create transaction record for successful
                        sql_query="""
                            INSERT INTO public."MSB_ZMSB_BARCOD_TRAN"
                                ("ZZCNO","ZBARCODE","CNTMOBILE","ZSTATUS","ZSTART_SCAN", "ZEND_SCAN", "ZZATN","ZMESSAGE","ZZALP","ZZAPG")
                            VALUES
                                (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """

                        # Extract values from estimate_data dictionary
                        values = (
                            bp_number, data.d.ImScratchCode, data.d.ImCntmobile, "Fail", datetime.now(), datetime.now(), sequence_number,RESPONSE["data"]["Message"],product_category,product_group,
                        )
                        # Execute the SQL query
                        cursor.execute(sql_query, values)
                        
                        return RESPONSE
                    
            # create transaction record with pending status
            sql_query="""
                INSERT INTO public."MSB_ZMSB_BARCOD_TRAN"
                    ("ZZCNO","ZBARCODE","CNTMOBILE","ZSTATUS", "ZZATN", "ZSTART_SCAN","ZZALP","ZZAPG")
                VALUES
                    (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING "ZZATN";
                """

            # Extract values from estimate_data dictionary
            values = (
                bp_number, data.d.ImScratchCode, data.d.ImCntmobile, "Pending", sequence_number,datetime.now(),product_category,product_group,
            )
            # Execute the SQL query and get the transaction number
            cursor.execute(sql_query, values)
            
            
            
            # Api call to salesforce for transaction journal
            payload = {
                "bpNumber":bp_number,
                "dealerBp":linkedDealer,
                "linkedDealerRegion":linkedDealerTerritory,
                "productGroup":product_group,
                "volume":volume,
                "barcodeScan": "APP",
                "scanCode":data.d.ImScratchCode,
                "skuNumber" : sku_number,
                "transactionNumber" : sequence_number
            }
            
            sf_response = sf.apexecute('/MSB/ScanBarcode', method='POST', data=payload)
                    # for obj in response['data']:
                    #     if 'dates' in obj:
                    #         obj['date'] = obj.pop('dates')
            if sf_response.get("status") == '0':
                # check response from salesforce
                # update status of barcode transaction accordingly salesforce response
                if sf_response.get("points") <= 0:
                    RESPONSE["data"]["Message"] = "No scheme running for this product in your region. Please get in touch with nearest Asian Paints Dealer/Representative to know more."
                    RESPONSE["data"]["code"] = 1
                    
                    query = f"""
                    UPDATE public."MSB_ZMSB_BARCOD_TRAN"
                        SET "ZSTATUS" = 'Fail', "ZMESSAGE" = '{RESPONSE["data"]["Message"]}'
                        WHERE "ZZATN" = '{sequence_number}';
                    """
                    cursor.execute(query)
                else:
                    RESPONSE["data"]["Message"] = "Successfully accrued points"
                    RESPONSE["data"]["code"] = 1
                    RESPONSE["data"]["EvStatus"] = "Success"
                    
                    query = f"""
                        UPDATE public."MSB_ZMSB_BARCOD_TRAN"
                        SET "ZSTATUS" = 'Successful', "ZZPOI" = '{sf_response.get("points")}', "ZEND_SCAN" = '{datetime.now()}'
                        WHERE "ZZATN" = '{sequence_number}';
                    """
                    cursor.execute(query)
                return RESPONSE
            
            RESPONSE["data"]["code"] = 1
            RESPONSE["data"]["Message"] = sf_response.get("message")
            query = f"""
                UPDATE public."MSB_ZMSB_BARCOD_TRAN"
                    SET "ZSTATUS" = 'Fail', "ZMESSAGE" = '{RESPONSE["data"]["Message"]}'
                    WHERE "ZZATN" = '{sequence_number}';
                """
            cursor.execute(query)
            create_log("fetch_scanbarcode",json.dumps(await request.json()),json.dumps(req_header),json.dumps(RESPONSE),'Info')
            return RESPONSE
        else:
            # response when BP number not found
            RESPONSE["data"]["code"] = 1
            RESPONSE["data"]["Message"] = "Invalid Contractor BP"
            RESPONSE["data"]["EvStatus"] = "NOT REGISTERED MSB PARTNER"
            create_log("bp_check",json.dumps({"BP_Number":BP_Number}),json.dumps(req_header),json.dumps(RESPONSE),'Info')
            return RESPONSE
    except Exception as e:

        if sequence_number != '' :
            query = f"""
                UPDATE public."MSB_ZMSB_BARCOD_TRAN"
                SET "ZSTATUS" = 'Fail', "ZMESSAGE" = '{e}'
                WHERE "ZZATN" = '{sequence_number}';
            """
            cursor.execute(query)
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


class UnsuccessfulScansRequest(BaseModel):
    bpNumber: str
    salt: str
    password: str

@router.post("/UnSuccessfulBarcodeScans", response_model=dict)
async def get_unsuccessful_scans(request: Request,
                         data: UnsuccessfulScansRequest, 
    BP_Number: Optional[str] = Header(None, title="BP_Number", convert_underscores=False),
):
    bp_number = data.bpNumber
    start_date = request.query_params.get("start")
    start_date = convert_date(start_date)
    end_date = request.query_params.get("end")
    end_date = convert_date(end_date)
    # convert Header Param to JSON
    req_header={"BP_Number":BP_Number}
    
    try:
        # create database cursor
        cursor = db_connection.cursor()
        
        # query for get barcode transaction details from contractor bp and status
        query = """
            SELECT "ZZCNO", "ZZALP", "ZZAPG", "ZZATN", "ZSTATUS", "ZMESSAGE", "ZZPDT", "ZSTART_SCAN"
            FROM public."MSB_ZMSB_BARCOD_TRAN"
            WHERE "ZZCNO" = %s AND "ZSTATUS" = 'Fail' AND "ZSTART_SCAN" >= %s AND "ZEND_SCAN" <= %s
        """
        
        cursor.execute(query, (bp_number, start_date, end_date))
        results = cursor.fetchall()
        
        if results is None or len(results) == 0:
            # if there is not data.
            response = {
                "Status": "400",
                "Message": "Unable to fetch details",
                "data": None
            }
            return response
        
        data = []
        for res in results:
            record = {
                "Product_Category": res[1],
                "ProductGroup": res[2],
                "Transaction_No":res[3],
                "TransactionStatus": res[4],
                "Reason": res[5],
                "Date": f"/Date({int(res[7].timestamp() * 1000)})/",
                "Time": res[7].strftime("%H%M%S")
            }
            data.append(record)
        
        response = {
            "Status":"200",
            "Message":"Success",
            "data":data
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


class SuccessfulScansRequest(BaseModel):
    bpNumber: str
    salt: str
    password: str

@router.post("/SuccessfulBarcodeScans", response_model=dict)
async def get_successful_scans(request: Request,
                         data: SuccessfulScansRequest, 
    BP_Number: Optional[str] = Header(None, title="BP_Number", convert_underscores=False),
):
    bp_number = data.bpNumber
    start_date = request.query_params.get("start")
    start_date = convert_date(start_date)
    end_date = request.query_params.get("end")
    end_date = convert_date(end_date)
    # convert Header Param to JSON
    req_header={"BP_Number":BP_Number}
    
    try:
        # create database cursor
        cursor = db_connection.cursor()
        
        # query for get barcode transaction details from contractor bp and status
        query = """
            SELECT "ZZCNO", "ZZALP", "ZZAPG", "ZZATN", "ZSTATUS", "ZBARCODE", "ZZPDT", "ZSTART_SCAN", "ZZPOI"
            FROM public."MSB_ZMSB_BARCOD_TRAN"
            WHERE "ZZCNO" = %s AND "ZSTATUS" = 'Successful' AND "ZSTART_SCAN" >= %s AND "ZEND_SCAN" <= %s
        """
        
        cursor.execute(query, (bp_number, start_date, end_date))
        results = cursor.fetchall()
        
        if results is None or len(results) == 0:
            # if there is not data.
            response = {
                "Status": "400",
                "Message": "Unable to fetch details",
                "data": None
            }
            return response
        
        data = []
        for res in results:
            record = {
                "Product_Category": res[1],
                "ProductGroup": res[2],
                "Transaction_No":res[3],
                "TransactionStatus": res[4],
                "Token": res[5],
                "Date": f"/Date({int(res[7].timestamp() * 1000)})/",
                "Time": res[7].strftime("%H%M%S"),
                "Contractor_Points": res[8]
            }
            data.append(record)
        
        response = {
            "Status":"200",
            "Message":"Success",
            "data":data
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


class TTSummaryRequest(BaseModel):
    bpNumber: str
    salt: str
    password: str

@router.post("/TTSummary", response_model=dict)
async def get_tt_summary(request: Request,
                         data: TTSummaryRequest,
    BP_Number: Optional[str] = Header(None, title="BP_Number", convert_underscores=False),
):
    bp_number = data.bpNumber
    
    # convert Header Param to JSON
    req_header={"BP_Number":BP_Number}
    
    try:
        # create database cursor
        cursor = db_connection.cursor()
        
        # Get fiscal year dates
        fy_start_ly, fy_end_ly, fy_start_ty, fy_end_ty = get_fiscal_year_dates()
        
        # Get month dates
        first_day_last_month, last_day_last_month, first_day_this_month, today = get_month_dates()
        
        # query for tokeen scanned last year
        query = f"""
            SELECT
                COUNT(CASE WHEN "ZEND_SCAN" BETWEEN '{fy_start_ly}' AND '{fy_end_ly}' THEN 1 END) AS No_Of_Token_Scanned_Ly,
                COUNT(CASE WHEN "ZEND_SCAN" BETWEEN '{fy_start_ty}' AND '{fy_end_ty}' THEN 1 END) AS No_Of_Token_Scanned_Ty,
                SUM(CASE WHEN "ZEND_SCAN" BETWEEN '{first_day_last_month}' AND '{last_day_last_month}' THEN "ZZPOI" ELSE 0 END) AS Barcode_Contractor_Points_Lm,
                SUM(CASE WHEN "ZEND_SCAN" BETWEEN '{first_day_this_month}' AND '{today}' THEN "ZZPOI" ELSE 0 END) AS Barcode_Contractor_Points_Tm,
                "ZZCNO"
            FROM public."MSB_ZMSB_BARCOD_TRAN"
            WHERE "ZZCNO" = %s AND "ZSTATUS" = 'Successful'
            GROUP BY "ZZCNO";
        """
        
        cursor.execute(query, (bp_number,))
        results = cursor.fetchall()

        acc_query = """
                SELECT "MOBILE_NUMBER" FROM public."MSB_ACCOUNT" WHERE "BP_NUMBER" = %s;
            """
            
        cursor.execute(acc_query, (bp_number,))
        acc = cursor.fetchone()
        
        if results:
            data = []
            for result in results:
                record = {
                    "No_Of_Token_Scanned_Ly": result[0],
                    "No_Of_Token_Scanned_Ty": result[1],
                    "Barcode_Contractor_Points_Lm": result[2],
                    "Barcode_Contractor_Points_Tm": result[3],
                    "Contractor": bp_number,
                    "Mobile":acc[0],
                }
                data.append(record)

            response = {
                "message": "Success",
                "status": "200",
                "data":data
            }
        else:
            response =  {
                "data":[
                    {
                        "No_Of_Token_Scanned_Ly":0,
                        "Barcode_Contractor_Points_Lm":"0.00",
                        "Contractor": bp_number,
                        "No_Of_Token_Scanned_Ty":0,
                        "Barcode_Contractor_Points_Tm":"0.0",
                        "Mobile":acc[0]
                    }
                ],
                "message":"Success",
                "status":"200"
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
    


class SMSDataRequest(BaseModel):
    ImScratchCode: str
    ImCntmobile: str


class SMSScanBarcodeRequest(BaseModel):
    d: SMSDataRequest


@router.post("/DealerAPP_BarcodeScan", response_model=dict)
async def sms_scan_barcode(
    request: Request,
    data: SMSScanBarcodeRequest,
    BP_Number: Optional[str] = Header( None, title="BP_Number", convert_underscores=False),
):
    contractor_mobile = data.d.ImCntmobile

    # convert Header Param to JSON
    req_header = {"BP_Number": BP_Number}

    # response template
    RESPONSE = {
        "message": "Success",
        "status": "200",
        "data": {
            "ImCntmobile": data.d.ImCntmobile,
            "ImScratchCode": data.d.ImScratchCode,
            # "ImSource": data.d.ImSource,
            "EvStatus": "",
            "EvTransFrom": "",
            "Type": "E",
            "Id": "",
            "Number": "",
            "Message": "",
            "LogNo": "",
            "LogMsgNo": "",
            "MessageV1": "",
            "MessageV2": "",
            "MessageV3": "",
            "MessageV4": "",
            "Parameter": "",
            "Row": 0.0,
            "Field": "",
            "System": "",
        },
    }

    try:

        # create database cursor
        cursor = db_connection.cursor()

        # query for get msb_account from mobile number
        query = f"""
                SELECT "BP_NUMBER", "NAME", "USER_TYPE", "EMAIL", "MOBILE_NUMBER", "BLOCK", "LINKED_DEALER", "LINKED_DEALER_TERRITORY"
                FROM public."MSB_ACCOUNT"
                WHERE "MOBILE_NUMBER" = '{contractor_mobile}'
            """

        cursor.execute(query)
        results = cursor.fetchall()
        sequence_number = ""

        if results:
            for res in results:
                bp_number = res[0]
                mobile_number = res[4]
                block_status = res[5]
                linkedDealer = res[6]
                linkedDealerTerritory = res[7]

            if block_status == "Y":
                # response if account is blocked
                RESPONSE["data"]["code"] = 1
                RESPONSE["data"][
                    "Message"
                ] = "Sorry, Your account is blocked in system. Please speak to Asian paints dealer/sales officer to know more on the same."
                return RESPONSE

            if (
                linkedDealer == None
                or linkedDealer == ""
                or linkedDealerTerritory == None
                or linkedDealerTerritory == ""
            ):
                # response if  account has ont linked dealer
                RESPONSE["data"]["code"] = 1
                RESPONSE["data"][
                    "Message"
                ] = "Please get in touch with nearest Asian Paints Delaer/Representative to know more."
                return RESPONSE

            # query for get link dealer msb_account from bp_number
            query = f"""
                    SELECT "BP_NUMBER", "NAME", "USER_TYPE", "EMAIL", "MOBILE_NUMBER", "BLOCK", "LINKED_DEALER", "LINKED_DEALER_TERRITORY"
                    FROM public."MSB_ACCOUNT"
                    WHERE "BP_NUMBER" = '{linkedDealer}'
                """

            cursor.execute(query)
            results = cursor.fetchall()

            if results is None or len(results) == 0:
                # response if there is not link-dealer account
                RESPONSE["data"]["code"] = 1
                RESPONSE["data"][
                    "Message"
                ] = "Please get in touch with nearest Asian Paints Delaer/Representative to know more."
                return RESPONSE
            else:
                for res in results:
                    region = res[7]
                    if region == "" or region is None:
                        # response if link-dealer has no region
                        RESPONSE["data"]["code"] = 1
                        RESPONSE["data"][
                            "Message"
                        ] = "Please get in touch with nearest Asian Paints Delaer/Representative to know more."
                        return RESPONSE

            # get sku id from table
            query = f"""
                    SELECT "MATNR", "ZPACK"
                    FROM public."MSB_ZMSB_PBM_CI"
                    WHERE "ZBARCODE" = '{data.d.ImScratchCode}'
                """

            cursor.execute(query)
            sku_res = cursor.fetchall()
            sku_number = ""
            volume = 0
            if sku_res:
                for res in sku_res:
                    sku_number = res[0]
                    volume = float(res[1])
            else:
                # response when BP number not found
                RESPONSE["data"]["code"] = 1
                RESPONSE["data"]["Message"] = "Not a Valid Barcode - " + data.d.ImScratchCode
                create_log("bp_check",json.dumps({"BP_Number":BP_Number}),json.dumps(req_header),json.dumps(RESPONSE),'Info')
                return RESPONSE

            # sku_number = sku_res[0][0]
            # volume = sku_res[0][1]

            # query for get record for sku from master table
            query = f"""
                    SELECT "ZZAPG","ZZALP"
                    FROM public."MSB_ZMSB_BARCOD_MAST"
                    WHERE "ZZSKU" = '{sku_number}' AND "ZZAPR" = '{linkedDealerTerritory}'
                """

            cursor.execute(query)
            master_results = cursor.fetchall()

            if master_results is None or len(master_results) == 0:

                # response if there is not any record for that sku.
                RESPONSE["data"]["code"] = 1
                RESPONSE["data"][
                    "Message"
                ] = "Scan not successful. Please call helpline 18002093000 to raise complaint(CODE 01:BCDMAST)"

                return RESPONSE

            # 1. Fetch sequence number
            query = f""" SELECT nextval('public."MSB_ZMSB_BARCOD_SEQ"'); """
            cursor.execute(query)
            sequence_number = str(cursor.fetchone()[0])  # Extract the sequence value

            # get product group
            product_group = ""
            product_category = ""
            if master_results:
                for res in master_results:
                    product_group = res[0]
                    product_category = res[1]

            # query for get msb_account from bp_number for pending and successful
            query = f"""
                    SELECT "ZZCNO","ZBARCODE","CNTMOBILE", "ZSTATUS", "ZEND_SCAN","ZZATN"
                    FROM public."MSB_ZMSB_BARCOD_TRAN"
                    WHERE "ZBARCODE" = '{data.d.ImScratchCode}' AND "ZSTATUS" IN ('Pending', 'Successful')
                """

            cursor.execute(query)
            barcodeScanResult = cursor.fetchall()

            if barcodeScanResult:
                for res in barcodeScanResult:
                    barcodeBP = res[0]
                    barcode_code = res[1]
                    cnt_mobile = res[2]
                    barcodeStatus = res[3]
                    scanEndDate = res[4]
                    transactionNo = res[5]

                    if barcodeStatus == "Pending":
                        RESPONSE["data"]["code"] = 1
                        RESPONSE["data"]["Message"] = "Scan is in progress."
                        # create transaction record for pending
                        sql_query = """
                            INSERT INTO public."MSB_ZMSB_BARCOD_TRAN"
                                ("ZZCNO","ZBARCODE","CNTMOBILE","ZSTATUS", "ZSTART_SCAN", "ZEND_SCAN", "ZZATN", "ZMESSAGE","ZZALP","ZZAPG")
                            VALUES
                                (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """

                        # Extract values from estimate_data dictionary
                        values = (
                            bp_number,
                            data.d.ImScratchCode,
                            data.d.ImCntmobile,
                            "Fail",
                            datetime.now(),
                            datetime.now(),
                            sequence_number,
                            RESPONSE["data"]["Message"],
                            product_category,
                            product_group,
                        )
                        # Execute the SQL query
                        cursor.execute(sql_query, values)

                        return RESPONSE

                    if barcodeStatus == "Successful":
                        # create transaction record for successful
                        sql_query = """
                            INSERT INTO public."MSB_ZMSB_BARCOD_TRAN"
                                ("ZZCNO","ZBARCODE","CNTMOBILE","ZSTATUS","ZSTART_SCAN", "ZEND_SCAN", "ZZATN","ZMESSAGE","ZZALP","ZZAPG")
                            VALUES
                                (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """

                        # Extract values from estimate_data dictionary
                        values = (
                            bp_number,
                            data.d.ImScratchCode,
                            data.d.ImCntmobile,
                            "Fail",
                            datetime.now(),
                            datetime.now(),
                            sequence_number,
                            RESPONSE["data"]["Message"],
                            product_category,
                            product_group,
                        )
                        # Execute the SQL query
                        cursor.execute(sql_query, values)

                        sms_message = "এই টোকেনটি আগে ব্যবহৃত হয়ছে। পুনরায় কোডটি প্রবেশ করুন অথবা অন্য টোকেন ব্যবহার করুন।"

                        RESPONSE["data"]["code"] = 1
                        RESPONSE["data"]["Message"] = sms_message
                        RESPONSE["data"]["EvStatus"] = "USED SCRATCHCODE"

                        sendSMS(
                            mobileno=contractor_mobile,
                            message=sms_message,
                            bp_number=bp_number,
                        )
                        return RESPONSE

            # create transaction record with pending status
            sql_query = """
                INSERT INTO public."MSB_ZMSB_BARCOD_TRAN"
                    ("ZZCNO","ZBARCODE","CNTMOBILE","ZSTATUS", "ZZATN", "ZSTART_SCAN","ZZALP","ZZAPG")
                VALUES
                    (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING "ZZATN";
                """

            # Extract values from estimate_data dictionary
            values = (
                bp_number,
                data.d.ImScratchCode,
                data.d.ImCntmobile,
                "Pending",
                sequence_number,
                datetime.now(),
                product_category,
                product_group,
            )
            # Execute the SQL query and get the transaction number
            cursor.execute(sql_query, values)

            # Api call to salesforce for transaction journal
            payload = {
                "bpNumber": bp_number,
                "dealerBp": linkedDealer,
                "linkedDealerRegion": linkedDealerTerritory,
                "productGroup": product_group,
                "volume": volume,
                "barcodeScan": "SMS"
            }

            sf_response = sf.apexecute("/MSB/ScanBarcode", method="POST", data=payload)
            # for obj in response['data']:
            #     if 'dates' in obj:
            #         obj['date'] = obj.pop('dates')
            if sf_response.get("status") == "0":
                # check response from salesforce
                # update status of barcode transaction accordingly salesforce response
                if sf_response.get("points") <= 0:
                    RESPONSE["data"][
                        "Message"
                    ] = "No scheme running for this product in your region. Please get in touch with nearest Asian Paints Dealer/Representative to know more."
                    RESPONSE["data"]["code"] = 1

                    query = f"""
                    UPDATE public."MSB_ZMSB_BARCOD_TRAN"
                        SET "ZSTATUS" = 'Fail', "ZMESSAGE" = '{RESPONSE["data"]["Message"]}'
                        WHERE "ZZATN" = '{sequence_number}';
                    """
                    cursor.execute(query)
                else:
                    # sms_message = f"টোকেনের {sf_response.get("points")} পয়েন্ট আপনার অ্যাকাউন্টে জমা হয়েছে। {sequence_number}।"
                    sms_message = f"আপনার অ্যাকাউন্টে টোকেনের  {sf_response.get('points')} পয়েন্ট  জমা হয়েছে এবং র্সবমোট প্রগতি ক্লাবের পয়েন্ট  {sf_response.get('totalPoints')} ,  টাকা দেওয়া হয়েছে  0.0 , জমা আছে  {sf_response.get('totalPoints')}। {sequence_number}।"
                    RESPONSE["data"]["Message"] = sms_message
                    RESPONSE["data"]["code"] = 1
                    RESPONSE["data"]["EvStatus"] = "Success"

                    query = f"""
                        UPDATE public."MSB_ZMSB_BARCOD_TRAN"
                        SET "ZSTATUS" = 'Successful', "ZZPOI" = '{sf_response.get('points')}', "ZEND_SCAN" = '{datetime.now()}'
                        WHERE "ZZATN" = '{sequence_number}';
                    """
                    cursor.execute(query)

                    sendSMS(
                        mobileno=contractor_mobile,
                        message=sms_message,
                        bp_number=bp_number,
                    )
                return RESPONSE

            RESPONSE["data"]["code"] = 1
            RESPONSE["data"]["Message"] = sf_response.get("message")
            query = f"""
                UPDATE public."MSB_ZMSB_BARCOD_TRAN"
                    SET "ZSTATUS" = 'Fail', "ZMESSAGE" = '{RESPONSE["data"]["Message"]}'
                    WHERE "ZZATN" = '{sequence_number}';
                """
            cursor.execute(query)
            create_log(
                "sms_scanbarcode",
                json.dumps(await request.json()),
                json.dumps(req_header),
                json.dumps(RESPONSE),
                "Info",
            )
            return RESPONSE
        else:
            # response when BP number not found
            RESPONSE["data"]["code"] = 1
            RESPONSE["data"]["Message"] = "Invalid Contractor BP"
            RESPONSE["data"]["EvStatus"] = "NOT REGISTERED MSB PARTNER"
            create_log(
                "sms_scanbarcode",
                json.dumps({"BP_Number": BP_Number}),
                json.dumps(req_header),
                json.dumps(RESPONSE),
                "Info",
            )
            return RESPONSE
    except Exception as e:

        if sequence_number != "":
            query = f"""
                UPDATE public."MSB_ZMSB_BARCOD_TRAN"
                SET "ZSTATUS" = 'Fail', "ZMESSAGE" = '{e}'
                WHERE "ZZATN" = '{sequence_number}';
            """
            cursor.execute(query)
        # Handle exceptions
        print("Exception:", e)
        response = {"status": "01", "message": "Error Occurred", "data": None}
        error_message = f"Database error: {e}"
        create_log(
            "sms_scanbarcode",
            "",
            json.dumps(req_header),
            '{"detail":"Internal Server Error"}',
            "Error",
            error_message,
        )
        return JSONResponse(content=response, status_code=200)
    finally:
        db_connection.commit()
        cursor.close()



class SendSMSRequest(BaseModel):
    mobile_number: str
    message: str


@router.post("/SendSMS", response_model=dict)
async def send_sms(request: Request, data: SendSMSRequest,
                   API_KEY: str = Header(..., title="API_KEY", description="API Key for authentication", convert_underscores=False),):
    apikey = os.getenv("SMS_API_KEY", "rJiUvVv0IHeoXaGYjY")
    response = {}
    try:
        if apikey == API_KEY:
            response = sendSMS(
                mobileno=data.mobile_number, message=data.message, bp_number=""
            )
        else:
            response = {"status": "01", "message": "Invalid ApiKey"}

        create_log(
            "scanbarcode",
            json.dumps(await request.json()),
            "",
            json.dumps(response),
            "Info",
        )
        return response
    except Exception as e:
        # Handle exceptions
        print("Exception:", e)
        response = {"status": "01", "message": "Error Occurred", "data": None}
        error_message = f"Error: {e}"
        create_log(
            "send_sms",
            "",
            "",
            '{"detail":"Internal Server Error"}',
            "Error",
            error_message,
        )
        return JSONResponse(content=response, status_code=200)
