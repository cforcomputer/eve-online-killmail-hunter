import asyncio
import json
import tkinter as tk
from tkinter import scrolledtext
import websockets
import webbrowser

async def subscribe_to_killstream(websocket, text_widget, counter_var):
    payload = {
        "action": "sub",
        "channel": "killstream"
    }
    await websocket.send(json.dumps(payload))
    text_widget.insert(tk.END, f"Subscribed to {payload['channel']} channel\n")

    # Initialize the counter
    counter = 0
    counter_var.set(counter)

    while True:
        try:
            response = await websocket.recv()
            response_data = json.loads(response)
            await process_killmail(response_data, text_widget, counter_var)
            counter += 1
            counter_var.set(counter)
        except websockets.ConnectionClosed:
            text_widget.insert(tk.END, "WebSocket connection closed\n")
            break

def open_url(url):
    webbrowser.open(url)

async def process_killmail(killmail_data, text_widget, counter_var):
    # Check if the killmail has a dropped value
    if "zkb" in killmail_data and "npc" in killmail_data["zkb"] and killmail_data["zkb"]["npc"]:
        dropped_value = killmail_data["zkb"]["droppedValue"]

        # Format the dropped item value
        formatted_dropped_value = format_dropped_value(dropped_value)

        # Display the killmail in the text widget
        text_widget.insert(tk.END, f"Dropped Value: {formatted_dropped_value} - NPC Kill: ")

        # Create a clickable link using Label widget
        kill_link = killmail_data["zkb"]["url"]
        link_label = tk.Label(text_widget, text=kill_link, fg="blue", cursor="hand2")
        link_label.pack()
        link_label.bind("<Button-1>", lambda event, url=kill_link: open_url(url))
        text_widget.insert(tk.END, "\n")

async def connect_websocket(uri, text_widget, counter_var):
    async with websockets.connect(uri) as websocket:
        await subscribe_to_killstream(websocket, text_widget, counter_var)

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

    text_widget = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=60, height=20)
    text_widget.pack(padx=10, pady=10)

    clear_button = tk.Button(root, text="Clear Text", command=lambda: text_widget.delete(1.0, tk.END))
    clear_button.pack(pady=5)

    counter_var = tk.IntVar()
    counter_label = tk.Label(root, text="Kills Processed: ")
    counter_label.pack(side=tk.LEFT, padx=5)
    counter_box = tk.Label(root, textvariable=counter_var)
    counter_box.pack(side=tk.LEFT, padx=5)

    uri = "wss://zkillboard.com/websocket/"

    # Use asyncio.gather to run both the WebSocket connection and Tkinter loop concurrently
    await asyncio.gather(connect_websocket(uri, text_widget, counter_var), run_tkinter_loop(root, text_widget))

def format_dropped_value(value):
    magnitude = 0
    while abs(value) >= 1000:
        magnitude += 1
        value /= 1000.0
    return '{:.2f}{}'.format(value, ['', 'K', 'M', 'B', 'T'][magnitude])

if __name__ == "__main__":
    asyncio.run(start_gui())
