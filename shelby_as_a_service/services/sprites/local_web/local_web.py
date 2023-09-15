from fastapi import FastAPI, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse

import os

def create_api():
    local_web = FastAPI()

    # Serve static files from the current directory
    local_web.mount("/static", StaticFiles(directory="."), name="static")

    @local_web.get("/")
    def read_root():
        return FileResponse(os.path.join(os.getcwd(), 'app/sprites/local_web/index.html'))

    @local_web.post("/run-function/")
    def run_function(data: str = Form(...)):
        # Placeholder logic
        if not data:
            raise HTTPException(status_code=400, detail="No data provided")
        return {"result": data[::-1]}
    
    return local_web  # Important: Return the FastAPI instance

local_web = create_api()  # Create and assign the FastAPI instance to the variable

