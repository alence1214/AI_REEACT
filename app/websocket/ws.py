from fastapi import APIRouter, WebSocket
from app.cron_job.cron_job import CronJob

router = APIRouter()
connected_clients = set()

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await websocket.accept()
    connected_clients.add((user_id, websocket))
    await CronJob.weather_task([(user_id, websocket)])
    try:
        while True:
            message = await websocket.receive_text()
            await websocket.send_text(f"Server Message: {message}")
    except Exception as e:
        print(e)
    finally:
        connected_clients.remove((user_id, websocket))