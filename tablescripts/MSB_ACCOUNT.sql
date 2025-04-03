CREATE TABLE IF NOT EXISTS public."MSB_ACCOUNT" (
    "BP_NUMBER" VARCHAR(20) PRIMARY KEY,
    "NAME" VARCHAR(100),
    "USER_TYPE" VARCHAR(20),
    "LINKED_DEALER" VARCHAR(100),
    "EMAIL" VARCHAR(100),
    "MOBILE_NUMBER" VARCHAR(20),
    "CREATED_BY" character varying(20),
    "CREATED_ON" timestamp(6) without time zone,
    "UPDATED_BY" character varying(20),
    "UPDATED_ON" timestamp(6) without time zone,
    "LINKED_DEALER_TERRITORY" VARCHAR(100),
    "LANGUAGE_ID" VARCHAR(10),
    "ROLE" VARCHAR(30),
    "BLOCK" VARCHAR(5),
    "PROFILE_URL" VARCHAR(500)
);
