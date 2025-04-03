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
import xmltodict
import random 
import json
import os

router = APIRouter()




class Productdetail4(BaseModel):
    Salt: str
    Password: str
   



class productcategory(BaseModel):
    image : str
    language : str
    notificationId : str
    readStatus : str
    notificationType : str
    title : str
    message : str
    startDate : str
    endDate : str


class productdetails(BaseModel):
    status: str
    message: str
    data : List[productcategory]

    
    

@router.post("/Get_Notification_List")
async def profile_update(request: Request, data: Productdetail4,BP_Number: str = Header(..., convert_underscores=False)
                       ):
     return productdetails(
            status= "0",
            message= "Success",
            data=[]
            
        )
    