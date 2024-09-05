import os
from fastapi import FastAPI, WebSocket
from fastapi.websockets import WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI()

# Mount the static files directory
app.mount("/static", StaticFiles(directory="."), name="static")

@app.get("/")
async def get():
    current_dir = os.path.dirname(os.path.realpath(__file__))
    html_file_path = os.path.join(current_dir, "index.html")
    if os.path.exists(html_file_path):
        return FileResponse(html_file_path)
    else:
        return {"error": f"File not found: {html_file_path}"}

@app.websocket("/ps")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Message received: {data}")
    except WebSocketDisconnect:
        print("Client disconnected")