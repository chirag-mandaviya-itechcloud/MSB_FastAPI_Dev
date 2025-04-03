import os
from fastapi.responses import JSONResponse
from starlette.requests import Request



async def app_version_check(request: Request):
    required_headers = {
        "BP_Number": request.headers.get("BP_Number"),
        "App_Ver": request.headers.get("App_Ver"),
        "Android_Ver": request.headers.get("Android_Ver"),
        "Device_Id": request.headers.get("Device_Id"),
        "Device_Mod": request.headers.get("Device_Mod"),
        "Source": request.headers.get("Source")
    }

    app_ver_config_var = float(os.environ.get("App_Ver", "2.0"))
    try:
        app_ver = float(required_headers["App_Ver"])
    except ValueError:
        return JSONResponse(
            status_code=200,
            content={
                "status": "03",
                "message": "Older App version. Application needs to be updated.",
                "data": None
            }
        )

    if app_ver < app_ver_config_var:
        version_check_response = check_app_version(app_ver, app_ver_config_var, request.url.path)
        if version_check_response:
            return version_check_response

    return None
