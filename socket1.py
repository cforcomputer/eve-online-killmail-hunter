import asyncio
import json
import tkinter as tk
from tkinter import scrolledtext
import websockets

async def subscribe_to_killstream(websocket, text_widget):
    payload = {
        "action": "sub",
        "channel": "killstream"
    }
    await websocket.send(json.dumps(payload))
    text_widget.insert(tk.END, f"Subscribed to {payload['channel']} channel\n")

    while True:
        try:
            response = await websocket.recv()
            text_widget.insert(tk.END, f"Received message: {response}\n")
            # Process the received JSON data as needed
        except websockets.ConnectionClosed:
            text_widget.insert(tk.END, "WebSocket connection closed\n")
            break

async def connect_websocket(uri, text_widget):
    async with websockets.connect(uri) as websocket:
        await subscribe_to_killstream(websocket, text_widget)

async def run_tkinter_loop(root, text_widget):
    try:
        while True:
            root.update()
            await asyncio.sleep(0.1)
    except tk.TclError as e:
        if "application has been destroyed" not in str(e):
            raise

async def start_gui():
    root = tk.Tk()
    root.title("WebSocket Live Feed")

    text_widget = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=40, height=15)
    text_widget.pack(padx=10, pady=10)

    uri = "wss://zkillboard.com/websocket/"

    # Use asyncio.gather to run both the WebSocket connection and Tkinter loop concurrently
    await asyncio.gather(connect_websocket(uri, text_widget), run_tkinter_loop(root, text_widget))

if __name__ == "__main__":

    asyncio.run(start_gui())
