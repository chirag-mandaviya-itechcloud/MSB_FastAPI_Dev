CREATE TABLE IF NOT EXISTS public."MSG_SMS_LOG" (
    "MOBILE_NUMBER" character varying(20) , 
    "CREATE_DATE" timestamp(6) without time zone, 
    "BP_NUMBER" character varying(20) ,   
    "MESSAGE" character varying(200) ,   
    "STATUS" character varying(20) , 
    "RESPONSE_CODE" character varying(20) , 
    "RESPONSE" character varying(200) , 
    "MESSAGE_ID" character varying(20),
    "CREDIT_AVAIL" character varying(20)
);
