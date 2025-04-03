CREATE TABLE IF NOT EXISTS public."MSG_SYSTEM_LOG" (
    "LOG_ID" SERIAL PRIMARY KEY,
    "TYPE" VARCHAR(2000),                       -- Type of log (Error, Info, Warning, etc.)
    "ERROR_MESSAGE" TEXT,                       -- Detailed error message (if applicable)
    "REQUEST_PAYLOAD" TEXT,                    -- Original request data in JSON format (for tracking)
    "REQUEST_HEADER" TEXT,    
    "RESPONSE_PAYLOAD" TEXT,                   -- System response data in JSON format
    "CREATE_DATE" TIMESTAMP(6) DEFAULT CURRENT_TIMESTAMP, -- Timestamp for when the log is created
    "SF_ID" VARCHAR(50),                      -- ID of the user who triggered the log
    "MODULE" VARCHAR(100)                      -- Module or part of the system where the log originated
);
