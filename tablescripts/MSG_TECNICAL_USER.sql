CREATE TABLE IF NOT EXISTS public."MSG_TECNICAL_USER" (
    "USER_ID" VARCHAR(20) PRIMARY KEY,
    "NAME" VARCHAR(100),
    "MOBILE_NO" VARCHAR(20),
    "EMAIL" VARCHAR(100),
    "REGION" VARCHAR(400),
    "LINKED_DEALER_COUNT" VARCHAR(100),
    "FILLER1" VARCHAR(30),
    "FILLER2" VARCHAR(30),
    "CREATED_ON" timestamp(6) without time zone,
    "CREATED_BY" character varying(20),
    "UPDATED_ON" timestamp(6) without time zone,
    "UPDATED_BY" character varying(20),
    "ACTIVE" VARCHAR(20)
);
