import asyncio
import json
from datetime import datetime, timezone, timedelta
import tkinter as tk
from tkinter import scrolledtext
import websockets
import webbrowser
import simpleaudio
import sys
import re

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

        # Get list of dropped items, see if it contains blueprint or abyssal item

        officers_list = [13557, 13654, 13564, 13544, 13573, 13589, 13603, 52475, 13667,
            13584, 13635, 13659, 13615, 13661, 13609, 13538, 13536, 13580, 13622, 13561, 13541]
        
        pass_condition = False
        label_color = "green"

        if calculate_filter_difference(killmail_time) > 1200:
            print(f"Filtered out: {killmail_data['killmail_time']} {time_difference} Dropped value: {dropped_value}")  # debug
            return  # Skip processing and displaying the killmail
        
        for officer in officers_list:
            if str(officer) in killmail_data:
                # Set label color to orange for officer/belt officer
                label_color = "orange"
                # Play a different audio alert
                play_orange_alert()

        if check_number_combination(killmail_data):
            # Item contains a blueprint or special item
            play_blue_alert()
        else:
            # Check if the time difference is greater than 20 minutes and that the value is greater than 100 million
            # Only perform the check if the item does not contain blueprints, abyssals, and is not an officer/commander
            if dropped_value < 200000000:
                print(f"Filtered out: {killmail_data['killmail_time']} {time_difference} Dropped value: {dropped_value}")  # debug
                return
            
            # Play the default audio alert
            play_audio_alert()

        # Create a label to display all details including clickable link and time difference
        kill_details = f"Dropped Value: {formatted_dropped_value} - Occurred: {time_difference}"
        link_label = create_link_label(text_widget, kill_details, killmail_data["zkb"]["url"], color=label_color)
        text_widget.insert(tk.END, "\n")

def check_number_combination(raw_response):
    i = 0
    # Load a list of numbers from a text file
    with open("blueprints.txt", "r") as file:
        number_combinations_to_check = [line.strip() for line in file.readlines()]

    # Check if any combination of numbers is present in the raw response
    for combination in number_combinations_to_check:
        # i+=1
        # print(i) # debug
        if re.search('"item_type_id": ' + combination + ",", str(raw_response)):
            return True

    return False


def play_audio_alert():
    # Replace 'path/to/audio/alert.wav' with the path to your audio file
    audio_path = 'alert.wav'
    try:
        wave_obj = simpleaudio.WaveObject.from_wave_file(audio_path)
        play_obj = wave_obj.play()
        play_obj.wait_done()
    except Exception as e:
        print(f"Error playing audio alert: {e}")

# For officer wrecks
def play_orange_alert():
    # Replace 'path/to/audio/orange_alert.wav' with the path to your orange audio file
    orange_audio_path = 'orange_alert.wav'
    try:
        wave_obj = simpleaudio.WaveObject.from_wave_file(orange_audio_path)
        play_obj = wave_obj.play()
        play_obj.wait_done()
    except Exception as e:
        print(f"Error playing orange audio alert: {e}")

# For blueprints or special items
def play_blue_alert():
    # Replace 'path/to/audio/blue_alert.wav' with the path to your blue audio file
    blue_audio_path = 'blue_alert.wav'
    try:
        wave_obj = simpleaudio.WaveObject.from_wave_file(blue_audio_path)
        play_obj = wave_obj.play()
        play_obj.wait_done()
    except Exception as e:
        print(f"Error playing blue audio alert: {e}")

def calculate_filter_difference(killmail_time):
    current_time = datetime.now(timezone.utc)
    time_difference = current_time - killmail_time
    seconds = int(time_difference.total_seconds())
    return seconds

def calculate_time_difference(killmail_time):
    current_time = datetime.now(timezone.utc)
    time_difference = current_time - killmail_time
    seconds = int(time_difference.total_seconds())

    if seconds < 60:
        return f"{seconds} seconds ago"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes} minutes ago"
    elif seconds < 86_400:
        hours = seconds // 3600
        return f"{hours} hours ago"
    else:
        days = seconds // 86_400
        return f"{days} days ago"

def format_dropped_value(value):
    magnitude = 0
    while abs(value) >= 1_000:
        magnitude += 1
        value /= 1_000.0
    return '{:.2f}{}'.format(value, ['', 'K', 'M', 'B', 'T'][magnitude])

def create_link_label(text_widget, text, url, color):
    link_label = tk.Label(text_widget, text=text, fg=color, cursor="hand2", wraplength=500, justify="left")
    link_label.pack(anchor="w")
    link_label.bind("<Button-1>", lambda event, url=url: open_url(url))
    return link_label

async def connect_websocket(uri, text_widget, counter_var, time_label):
    async with websockets.connect(uri) as websocket:
        await subscribe_to_killstream(websocket, text_widget, counter_var, time_label)

async def run_tkinter_loop(root, text_widget, time_label):
    try:
        while True:
            root.update()
            current_utc_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            time_label.config(text=f"EVE Time: {current_utc_time}")
            await asyncio.sleep(0.1)
    except tk.TclError as e:
        if "application has been destroyed" not in str(e):
            raise

def clear_text_and_labels(text_widget):
    text_widget.delete(1.0, tk.END)
    # Destroy all child widgets (labels) in the text widget
    for widget in text_widget.winfo_children():
        widget.destroy()

async def start_gui():
    root = tk.Tk()
    root.title("NPC Hunter Live XTREME V1")

    text_widget = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=60, height=20)
    text_widget.pack(padx=10, pady=10)

    clear_button = tk.Button(root, text="Clear kills", command=lambda: clear_text_and_labels(text_widget))
    clear_button.pack(pady=5)

    counter_var = tk.IntVar()
    counter_label = tk.Label(root, text="Kills Processed: ")
    counter_label.pack(side=tk.LEFT, padx=5)
    counter_box = tk.Label(root, textvariable=counter_var)
    counter_box.pack(side=tk.LEFT, padx=5)

    time_label = tk.Label(root, text="EVE Time: ")
    time_label.pack(anchor="w")

    root.protocol("WM_DELETE_WINDOW", lambda: close_window(root))  # Handle window close event

    uri = "wss://zkillboard.com/websocket/"

    try:
        await asyncio.gather(connect_websocket(uri, text_widget, counter_var, time_label), run_tkinter_loop(root, text_widget, time_label))
    except tk.TclError as e:
        if "application has been destroyed" not in str(e):
            raise

def close_window(root):
    root.destroy()
    sys.exit(0)  # Ensure the program exits

if __name__ == "__main__":
    asyncio.run(start_gui())
