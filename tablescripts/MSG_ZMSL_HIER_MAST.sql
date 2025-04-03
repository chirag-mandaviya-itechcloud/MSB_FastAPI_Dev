CREATE TABLE IF NOT EXISTS public."MSG_ZMSL_HIER_MAST" (
    "ZZTERRITORY" character varying(40) PRIMARY KEY, 
    "ZZUNIT" character varying(40) , 
    "ZZLOY_PROGRAM" character varying(40) , 
    "ZZREGION" character varying(40) , 
    "ZZDIVISIONID" character varying(40) , 
    "ZZTERR_DESCP" character varying(600) , 
    "ZZUNIT_DESCP" character varying(600) , 
    "ZZREG_DESCP" character varying(600) , 
    "ZZDIV_DESCP" character varying(600) , 
    "ZZCREATEDDATE" timestamp(6) without time zone,
    "ZZCREATEDBY" character varying(40) , 
    "ZZCHANGEDDATE" timestamp(6) without time zone,
    "ZZCHANGEDBY" character varying(40) 
);
