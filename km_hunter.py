import asyncio
import json
from datetime import datetime, timezone
import tkinter as tk
from tkinter import ttk
import websockets
import webbrowser
import simpleaudio
import sys
import os
import requests
from dotenv import load_dotenv
import argparse

# Define the command-line arguments
parser = argparse.ArgumentParser(description="NPC Hunter")
parser.add_argument("--no-gui", action="store_true", help="Run the program without GUI")

# Load environment variables from .env file
load_dotenv()

global GLOBAL_COUNT
GLOBAL_COUNT = 0
# Discord WEBHOOK URL --> go to channel settings, integrations, create webhook
# Then copy url and place it in the .env file.
WEBHOOK_URL = os.getenv("FEED_HOOK")

async def send_discord_webhook(message):
    print("Sending webhook")
    data = {"content": message}
    webhook_url = WEBHOOK_URL

    if webhook_url:
        response = requests.post(webhook_url, json=data)
        print(str(response))

# Default settings
DEFAULT_SETTINGS = {
    "dropped_value_enabled": False,
    "time_threshold_enabled": True,
    "time_threshold": 1200,
    "dropped_value": 100000000,
    "audio_alerts_enabled": True,  # New setting for audio alerts
}

async def subscribe_to_killstream(
    websocket, treeview, counter_var, time_label, dt_label, uri, filter_lists
):
    global GLOBAL_COUNT
    payload = {"action": "sub", "channel": "killstream"}
    await websocket.send(json.dumps(payload))
    print(f"Subscribed to {payload['channel']} channel at: " + str(datetime.now(timezone.utc)))

    if counter_var is not None:
        counter_var.set(GLOBAL_COUNT)

    ping_task = asyncio.create_task(send_pings(websocket))

    try:
        while True:
            response = await websocket.recv()
            
            settings = load_settings()
            response_data = json.loads(response)
            await process_killmail(
                response_data,
                treeview,
                counter_var,
                time_label,
                dt_label,
                filter_lists,  # Pass filter_lists here
                settings,
            )
            GLOBAL_COUNT += 1
            if counter_var is not None:
                counter_var.set(GLOBAL_COUNT)
    except websockets.ConnectionClosed:
        print("WebSocket connection closed at: " + str(datetime.now(timezone.utc)))
        await connect_websocket(uri, treeview, counter_var, time_label, dt_label, filter_lists)
  # Pass filter_lists here
    finally:
        ping_task.cancel()



async def send_pings(websocket):
    while True:
        try:
            await websocket.ping()
            # print("PING!") #debug
            await asyncio.sleep(30)
        except asyncio.CancelledError:
            break

def open_url(url):
    webbrowser.open(url)

# Function to play alert sound
def play_alert_sound(sound_file):
    if sound_file:
        try:
            wave_obj = simpleaudio.WaveObject.from_wave_file(sound_file)
            play_obj = wave_obj.play()
            play_obj.wait_done()
        except Exception as e:
            print(f"Error playing alert sound: {e}")

async def process_killmail(killmail_data, treeview, counter_var, time_label, dt_label, filter_lists, settings
):
    # Assigns settings.json values
    max_time_threshold = settings.get("time_threshold", 1200)
    max_dropped_value = settings.get("dropped_value", 100000000)
    time_threshold_enabled = settings.get("time_threshold_enabled", True)
    dropped_value_enabled = settings.get("dropped_value_enabled", False)
    audio_alerts_enabled = settings.get("audio_alerts_enabled", True)
    is_priority = False


    label_color = ""  # Initialize label color

    if (
        "zkb" in killmail_data
        # and "npc" in killmail_data["zkb"] # TODO: Make this an option to filter on npc only
        # and killmail_data["zkb"]["npc"]
    ):
        # killmail_data = r"{'attackers': [{'corporation_id': 1000134, 'damage_done': 14787, 'final_blow': False, 'security_status': 0, 'ship_type_id': 13609}, {'corporation_id': 1000162, 'damage_done': 0, 'final_blow': True, 'security_status': 0, 'ship_type_id': 13539}], 'killmail_id': 115846822, 'killmail_time': '2024-02-26T22:28:19Z', 'solar_system_id': 30002203, 'victim': {'alliance_id': 99012618, 'character_id': 92585977, 'corporation_id': 1670856481, 'damage_taken': 14787, 'items': [{'flag': 5, 'item_type_id': 60279, 'quantity_destroyed': 1, 'singleton': 0}, {'flag': 5, 'item_type_id': 60279, 'quantity_dropped': 5, 'singleton': 0}, {'flag': 27, 'item_type_id': 56306, 'quantity_destroyed': 1, 'singleton': 0}, {'flag': 13, 'item_type_id': 1405, 'quantity_dropped': 1, 'singleton': 0}, {'flag': 93, 'item_type_id': 31718, 'quantity_destroyed': 1, 'singleton': 0}, {'flag': 11, 'item_type_id': 28576, 'quantity_destroyed': 1, 'singleton': 0}, {'flag': 28, 'item_type_id': 60279, 'quantity_dropped': 1, 'singleton': 0}, {'flag': 94, 'item_type_id': 31754, 'quantity_destroyed': 1, 'singleton': 0}, {'flag': 19, 'item_type_id': 380, 'quantity_dropped': 1, 'singleton': 0}, {'flag': 92, 'item_type_id': 31766, 'quantity_destroyed': 1, 'singleton': 0}, {'flag': 87, 'item_type_id': 10246, 'quantity_destroyed': 2, 'singleton': 0}, {'flag': 87, 'item_type_id': 10246, 'quantity_dropped': 2, 'singleton': 0}, {'flag': 12, 'item_type_id': 28576, 'quantity_dropped': 1, 'singleton': 0}, {'flag': 27, 'item_type_id': 17912, 'quantity_dropped': 1, 'singleton': 0}, {'flag': 20, 'item_type_id': 12058, 'quantity_destroyed': 1, 'singleton': 0}, {'flag': 5, 'item_type_id': 2456, 'quantity_destroyed': 1, 'singleton': 0}, {'flag': 28, 'item_type_id': 17912, 'quantity_dropped': 1, 'singleton': 0}], 'position': {'x': -1184906903386.7654, 'y': -77016642186.46077, 'z': -547718785673.0664}, 'ship_type_id': 17478}, 'zkb': {'locationID': 40140327, 'hash': 'd7fe81868aeefcd5ed9738db33607f6575052b40', 'fittedValue': 84214064.17, 'droppedValue': 19790070.52, 'destroyedValue': 65793547.51, 'totalValue': 85583618.03, 'points': 1, 'npc': True, 'solo': False, 'awox': False, 'esi': 'https://esi.evetech.net/latest/killmails/115846822/d7fe81868aeefcd5ed9738db33607f6575052b40/', 'url': 'https://zkillboard.com/kill/115846822/'}}"
        dropped_value = killmail_data["zkb"]["droppedValue"]
        url = killmail_data["zkb"]["url"]
        # Gather attacker ids ------
        attacker_ship_type_ids = []
        if killmail_data["attackers"]:
            for attacker in killmail_data["attackers"]:
                try:
                    attacker_ship_type_ids.append(attacker["ship_type_id"])
                except:
                    pass
        # --------------------------
        formatted_dropped_value = format_dropped_value(dropped_value)
        killmail_time = datetime.strptime(
            killmail_data["killmail_time"], "%Y-%m-%dT%H:%M:%SZ"
        ).replace(tzinfo=timezone.utc)
        time_difference = calculate_time_difference(killmail_time)

        

        
        
        # Load filters and check for id matches for each filter

        for filter_item in filter_lists:
            enabled = filter_item.get("enabled")
            priority = filter_item.get("priority")

                # Calculating eve time occurred ago, and the dropped value.
            if (
                (calculate_filter_difference(killmail_time) > max_time_threshold
                and time_threshold_enabled == True) or (dropped_value < max_dropped_value and dropped_value_enabled and not priority)
            ):
                print(
                    f"Filtered out: {killmail_data['killmail_time']} {time_difference} Dropped value: {dropped_value} {url}"
                )
                return
            
            # Kill details webhook message string
            kill_details = (
                f"{killmail_data['killmail_time']} {time_difference} Dropped value: {dropped_value}\n{url}"
            )

            if enabled:
                # print(filter_item)
                file_id_list = load_list_from_file(filter_item.get("file"))
                

                for filter_id in file_id_list:
                    for id in attacker_ship_type_ids:
                        if filter_id == id:
                            try:
                                if filter_item.get("webhook", False):
                                    await send_discord_webhook(f"Kill found! {kill_details} \nurl: {url}")
                            except TypeError as e:
                                print("Error sending webhook" + str(e))
                            
                            label_color = filter_item.get("color", "")
                            if audio_alerts_enabled and filter_item.get("sound"): # filter sound = true or false
                                play_alert_sound(filter_item.get("sound"))

                            # await asyncio.sleep(0.6)
                            treeview.insert("", "end", values=(formatted_dropped_value, time_difference, url), tags=label_color)        
                
        print(f"Filtered out: {killmail_data['killmail_time']} {time_difference} Dropped value: {dropped_value} {url}")
    else:
        print("zkb not in km data")


def load_list_from_file(filename):
    try:
        with open(filename, "r") as file:
            return [int(line.strip()) for line in file.readlines()]
    except FileNotFoundError:
        return []
    
    
   

def calculate_filter_difference(killmail_time):
    current_time = datetime.now(timezone.utc)
    time_difference = current_time - killmail_time
    seconds = int(time_difference.total_seconds())
    return seconds

def get_time_until_downtime():
    current_utc_time = datetime.now(timezone.utc)
    target_time = current_utc_time.replace(hour=11, minute=0, second=0)
    time_difference = target_time - current_utc_time
    remaining_time_str = str(time_difference)
    return remaining_time_str.replace("-1 day,", "")

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
    return "{:.2f}{}".format(value, ["", "K", "M", "B", "T"][magnitude])

def clear_treeview(treeview):
    treeview.delete(*treeview.get_children())

async def connect_websocket(uri, treeview, counter_var, time_label, dt_label, filter_lists):
    while True:
        try:
            async with websockets.connect(uri) as websocket:
                await subscribe_to_killstream(
                    websocket, treeview, counter_var, time_label, dt_label, uri, filter_lists
                )
        except Exception as e:
            print(f"WebSocket connection closed: {e}")
            await asyncio.sleep(5)

async def run_tkinter_loop(root, treeview, time_label, dt_label):
    try:
        while True:
            root.update()
            current_utc_time = datetime.now(timezone.utc).strftime(
                "%Y-%m-%d %H:%M:%S UTC"
            )
            time_until_downtime = get_time_until_downtime()
            time_label.config(text=f"EVE Time: {current_utc_time}")
            dt_label.config(text=f"DT in: {time_until_downtime}")
            await asyncio.sleep(0.1)
    except tk.TclError as e:
        if "application has been destroyed" not in str(e):
            raise

 # Function to update the settings JSON based on GUI selection
def update_settings(settings, enabled_vars):
    # Update the "enabled" field in the settings dictionary
    for filter_item, enabled_var in zip(settings["filter_lists"], enabled_vars):
        filter_item["enabled"] = enabled_var.get()

    # Write the updated settings back to the JSON file
    with open("settings.json", "w") as file:
        json.dump(settings, file, indent=4)  # Use indent parameter for pretty formatting


async def start_gui(settings, with_gui=True):
    if with_gui:
        # Create the root window
        root = tk.Tk()
        root.minsize(280, 300)
        root.title("NPC Hunter 1.1")
        root.pack_propagate(False)

        # Create the main frame
        main_frame = tk.Frame(root)
        main_frame.pack(fill="both", expand=True)
        main_frame.pack_propagate(False)

        # Create the treeview widget
        treeview = ttk.Treeview(main_frame, columns=("Value", "Occurred"), show="headings")
        treeview.heading("Value", text="Dropped Value")
        treeview.heading("Occurred", text="Occurred")
        treeview.pack(side="left", fill="both", expand=True)

        # Set width for each column
        treeview.column("Value", width=150)  # Adjust the value as needed
        treeview.column("Occurred", width=150)  # Adjust the value as needed

        # Create a scrollbar for the treeview
        sb = tk.Scrollbar(main_frame, command=treeview.yview)
        sb.pack(side="right", fill="y")
        treeview.configure(yscrollcommand=sb.set)

        # Create a button to clear kills
        clear_button = tk.Button(root, text="Clear kills", command=lambda: clear_treeview(treeview))
        clear_button.pack(pady=5)

        # Create frames for additional information
        info_frame = tk.Frame(root, relief=tk.RAISED, borderwidth=1)
        info_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

        dt_frame = tk.Frame(root, relief=tk.RAISED, borderwidth=1)
        dt_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

        # Create labels for EVE time and downtime
        counter_var = tk.IntVar()
        counter_label = tk.Label(info_frame, text="Kills: ")
        counter_label.pack(side=tk.LEFT, padx=5)
        counter_box = tk.Label(info_frame, textvariable=counter_var)
        counter_box.pack(side=tk.LEFT, padx=5)

        dt_label = tk.Label(dt_frame, text="DT In: ")
        dt_label.pack(side=tk.BOTTOM)

        time_label = tk.Label(info_frame, text="EVE Time: ")
        time_label.pack(side=tk.BOTTOM)

        # Define function to close window
        root.protocol("WM_DELETE_WINDOW", lambda: close_window(root))

        # Define URI for websocket
        uri = "wss://zkillboard.com/websocket/"

        # Bind double-click on treeview to open URL in browser
        treeview.bind("<Double-1>", lambda event: open_url_in_browser(treeview))

        # Create a frame for filter lists and update button
        filter_update_frame = tk.Frame(root)
        filter_update_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        # Create dropdown menu for filter lists
        filter_frame = tk.Frame(filter_update_frame)
        filter_frame.pack(side=tk.LEFT)

        dropdown_menu = tk.Menubutton(filter_frame, text="Filter Lists", relief="raised")
        dropdown_menu.pack(side=tk.LEFT, padx=5)

        dropdown_menu.menu = tk.Menu(dropdown_menu, tearoff=0)
        dropdown_menu["menu"] = dropdown_menu.menu

        enabled_vars = []
        for filter_item in settings["filter_lists"]:
            enabled = tk.BooleanVar()
            enabled.set(filter_item["enabled"])
            enabled_vars.append(enabled)

            dropdown_menu.menu.add_checkbutton(label=filter_item["file"], variable=enabled)

        def toggle_dropdown(event=None):
            if dropdown_menu.menu.winfo_ismapped():
                dropdown_menu.menu.unpost()
            else:
                dropdown_menu.menu.post(dropdown_menu.winfo_rootx(), dropdown_menu.winfo_rooty() + dropdown_menu.winfo_height())

        dropdown_menu.bind("<Button-1>", toggle_dropdown)

        # Add a button to update settings
        update_button = tk.Button(filter_update_frame, text="Update Settings", command=lambda: update_settings(settings, enabled_vars))
        update_button.pack(side=tk.LEFT, padx=5)

        # Run the Tkinter event loop
        try:
            await asyncio.gather(
                connect_websocket(uri, treeview, counter_var, time_label, dt_label, settings["filter_lists"]),
                run_tkinter_loop(root, treeview, time_label, dt_label),
            )
        except tk.TclError as e:
            if "application has been destroyed" not in str(e):
                raise
    else:
        uri = "wss://zkillboard.com/websocket/"
        try:
            await asyncio.gather(
                connect_websocket(uri, None, None, None, None, settings["filter_lists"]),
                run_background_tasks(settings),
            )
        except KeyboardInterrupt:
            print("Exiting program due to keyboard interrupt.")
            sys.exit(0)



async def run_background_tasks(settings):
    # Run background tasks here (e.g., WebSocket connection, etc.)
    uri = "wss://zkillboard.com/websocket/"
    while True:
        try:
            async with websockets.connect(uri) as websocket:
                # Run the WebSocket connection task
                await subscribe_to_killstream(websocket, None, None, None, None, uri, settings["filter_lists"])
        except websockets.exceptions.ConnectionClosed as e:
            print(f"WebSocket connection closed: {e} at: {datetime.now(timezone.utc)}")
            await asyncio.sleep(5)

def open_url_in_browser(treeview):
    selected_item = treeview.selection()[0]
    url = treeview.item(selected_item, "values")[2]
    webbrowser.open(url)

def load_settings():
    try:
        with open("settings.json", "r") as file:
            settings = json.load(file)
    except FileNotFoundError:
        settings = DEFAULT_SETTINGS
    return settings

def save_settings(settings):
    with open("settings.json", "w") as file:
        json.dump(settings, file)

def close_window(root):
    root.destroy()
    sys.exit(0)

async def main():
    # Parse the command-line arguments
    args = parser.parse_args()

    # Load settings from JSON file
    settings = load_settings()

    # Check if GUI should be started based on command-line arguments
    with_gui = not args.no_gui

    await start_gui(settings, with_gui)

if __name__ == "__main__":
    asyncio.run(main())
