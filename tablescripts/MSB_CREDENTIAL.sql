CREATE TABLE IF NOT EXISTS public."MSB_CREDENTIAL" (
    "BP_NUMBER" character varying(50) ,
    "ENCP_SALT" character varying(999),
    "ENCP_PASSWORD" character varying(999),
    "VERSION_INSTALLED" character varying(255),
    "BLOCK_STATUS" character varying(20),
    "CREATED_BY" character varying(255),
    "CREATED_AT" timestamp(6) without time zone,
    "MODIFIED_BY" character varying(255),
    "MODIFIED_AT" timestamp(6) without time zone,
    "EXPIRED" character varying(20)
);
