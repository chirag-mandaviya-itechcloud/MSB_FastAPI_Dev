CREATE TABLE IF NOT EXISTS public."MSG_PREF_DEALER" (
    "CONTRACTOR_BP" character varying(20) ,
    "DEALER_BP" character varying(20) , 
    "NAME" character varying(50) ,   
    "ROLE" character varying(20) ,   
    "MOBILE_NO" character varying(20) , 
    "CREATED_BY" character varying(20),
    "CREATED_ON" timestamp(6) without time zone,
    "UPDATED_BY" character varying(20),
    "UPDATED_ON" timestamp(6) without time zone
);