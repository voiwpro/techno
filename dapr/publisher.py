from fastapi import FastAPI, Request, HTTPException
from dapr.clients import DaprClient
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.post("/publish")
async def publish(request: Request):
    try:
        payload = await request.json()
        logger.info(f"Received payload: {payload}")
        
        with DaprClient() as client:
            result = client.publish_event(
                pubsub_name="pubsub",
                topic_name="messages",
                data=json.dumps(payload),  # Serialize the payload to JSON string
            )
        logger.info(f"Publish result: {result}")
        
        return {"status": "Message published"}
    except ValueError as e:
        logger.error(f"Invalid JSON: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except Exception as e:
        logger.error(f"Error publishing message: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)