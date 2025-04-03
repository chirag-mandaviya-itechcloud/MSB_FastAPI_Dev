CREATE TABLE IF NOT EXISTS public."MSB_OTP" (
    "BP_NUMBER" VARCHAR(255),
    "MOBILE_NUMBER" VARCHAR(255),
    "IMEI_NUMBER" VARCHAR(255),
    "VALID_UPTO" timestamp(6) without time zone,
    "CONSUMED_STATUS" VARCHAR(255),
    "SMS_STATUS" VARCHAR(255),
    "VERSION_INSTALLED" VARCHAR(255),
    "CREATED_AT" timestamp(6) without time zone,
    "CREATED_BY" VARCHAR(255),
    "MODIFIED_AT" timestamp(6) without time zone,
    "MODIFIED_BY" VARCHAR(255),
    "OTP" VARCHAR(255),
    "COUNT" NUMERIC(38,0)
);