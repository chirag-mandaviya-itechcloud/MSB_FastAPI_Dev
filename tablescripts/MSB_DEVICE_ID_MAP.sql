CREATE TABLE IF NOT EXISTS public."MSB_DEVICE_ID_MAP" (
    "BP" VARCHAR(20) ,
    "DEVICE_ID" VARCHAR(200),
    "TYPE" VARCHAR(20),
    "DIVISION" character varying(30),
    "REGION" character varying(40),
    "UNIT" character varying(20),
    "CONTRACTOR_TYPE" character varying(50),
    "CREATED_BY" character varying(20),
    "CREATED_ON" timestamp(6) without time zone,
    "MODIFIED_BY" character varying(20),
    "MODIFIED_ON" timestamp(6) without time zone,
    "APP_VERSION" VARCHAR(50)
);
