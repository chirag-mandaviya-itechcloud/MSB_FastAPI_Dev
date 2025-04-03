CREATE TABLE IF NOT EXISTS public."MSG_SPLASH_MESSAGES" (
    "MessageId" SERIAL PRIMARY KEY,
    "LANGUAGE_ID" VARCHAR(20),                      
    "MESSAGE" TEXT,                       
    "TYPE" VARCHAR(20)                  
);
