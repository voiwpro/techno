from fastapi import FastAPI, Request
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.get("/dapr/subscribe")
async def subscribe():
    subscriptions = [
        {'pubsubname': 'pubsub', 'topic': 'messages', 'route': '/messages'}
    ]
    return subscriptions

@app.post("/messages")
async def messages(request: Request):
    data = await request.json()
    logger.info(f"Subscriber received: {data}")
    return {"success": True}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)