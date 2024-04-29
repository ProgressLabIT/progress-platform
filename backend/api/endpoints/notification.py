from fastapi import WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi import APIRouter

from utils.websocket_manager import WebsoketManager

router = APIRouter()

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    <body>
        <h1>WebSocket Chat</h1>
        <h2>Your ID: <span id="ws-id"></span></h2>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off"/>
            <button>Send</button>
        </form>
        <ul id='messages'>
        </ul>
        <script>
            var client_id = Date.now()
            document.querySelector("#ws-id").textContent = client_id;
            var ws = new WebSocket(`ws://localhost:8000/api/ws/${client_id}`);
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                ws.send(input.value)
                input.value = ''
                event.preventDefault()
            }
        </script>
    </body>
</html>
"""

#Retrieve websocket example
@router.get("/wsexample")
async def get():
    return HTMLResponse(html)

#Retrieve websocket example
@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    websoketManager = WebsoketManager.getInstance()
    await websoketManager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await websoketManager.broadcast(f"Client #{client_id} says: {data}")
    except WebSocketDisconnect:
        websoketManager.disconnect(websocket)
        await websoketManager.broadcast(f"Client #{client_id} left the chat")
