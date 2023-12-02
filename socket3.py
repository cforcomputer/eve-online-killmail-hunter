import asyncio
import json
import tkinter as tk
from tkinter import scrolledtext
import websockets
import webbrowser
from datetime import datetime, timezone, timedelta

async def subscribe_to_killstream(websocket, text_widget, counter_var, time_label):
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
            await process_killmail(response_data, text_widget, counter_var, time_label)
            counter += 1
            counter_var.set(counter)
        except websockets.ConnectionClosed:
            text_widget.insert(tk.END, "WebSocket connection closed\n")
            break

def open_url(url):
    webbrowser.open(url)

async def process_killmail(killmail_data, text_widget, counter_var, time_label):
    # Check if the killmail has a dropped value
    if "zkb" in killmail_data and "npc" in killmail_data["zkb"] and killmail_data["zkb"]["npc"]:
        dropped_value = killmail_data["zkb"]["droppedValue"]

        # Format the dropped item value
        formatted_dropped_value = format_dropped_value(dropped_value)

        # Calculate time difference
        killmail_time = datetime.strptime(killmail_data["killmail_time"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        time_difference = calculate_time_difference(killmail_time)

        # Create a label to display all details including clickable link and time difference
        kill_details = f"Dropped Value: {formatted_dropped_value} - NPC Kill: {killmail_data['zkb']['url']} - Occurred: {time_difference}"
        link_label = tk.Label(text_widget, text=kill_details, fg="blue", cursor="hand2", wraplength=500, justify="left")
        link_label.pack(anchor="w")
        link_label.bind("<Button-1>", lambda event, url=killmail_data["zkb"]["url"]: open_url(url))
        text_widget.insert(tk.END, "\n")

def calculate_time_difference(killmail_time):
    current_time = datetime.now(timezone.utc)
    time_difference = current_time - killmail_time
    seconds = int(time_difference.total_seconds())

    if seconds < 60:
        return f"{seconds} seconds ago"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes} minutes ago"
    elif seconds < 86400:
        hours = seconds // 3600
        return f"{hours} hours ago"
    else:
        days = seconds // 86400
        return f"{days} days ago"

async def connect_websocket(uri, text_widget, counter_var, time_label):
    async with websockets.connect(uri) as websocket:
        await subscribe_to_killstream(websocket, text_widget, counter_var, time_label)

async def run_tkinter_loop(root, text_widget, time_label):
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

    time_label = tk.Label(root, text="UTC Time (London): ")
    time_label.pack(anchor="w")

    uri = "wss://zkillboard.com/websocket/"

    # Use asyncio.gather to run both the WebSocket connection and Tkinter loop concurrently
    await asyncio.gather(connect_websocket(uri, text_widget, counter_var, time_label), run_tkinter_loop(root, text_widget, time_label))

def format_dropped_value(value):
    magnitude = 0
    while abs(value) >= 1000:
        magnitude += 1
        value /= 1000.0
    return '{:.2f}{}'.format(value, ['', 'K', 'M', 'B', 'T'][magnitude])

if __name__ == "__main__":
    asyncio.run(start_gui())
