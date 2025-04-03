CREATE TABLE IF NOT EXISTS public."MSG_BP_MAP" (
    "MANDT" character varying(20) ,
    "DEALER_ID" character varying(20),
    "LOY_PROGRAM" character varying(10),
    "TERRITORY_ID" character varying(20),
    "UNIT_ID" character varying(20),
    "CREATED_BY" character varying(20),
    "CREATED_AT" timestamp(6) without time zone,
    "CHANGED_BY" character varying(20),
    "CHANGED_AT" timestamp(6) without time zone
);
