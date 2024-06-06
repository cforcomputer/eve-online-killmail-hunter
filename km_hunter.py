# @author cforcomputer
# @version 1.2.0
# Tested with python version 3.11.5, 3.12 crashes

import asyncio
import json
from datetime import datetime, timezone
import tkinter as tk
from tkinter import ttk
import websockets
import webbrowser
import sys
import os
import requests
from dotenv import load_dotenv
import argparse
from pygame import mixer, time

# import pdb # debug

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
    "list_check_id": "attacker_ship_type",
}


async def subscribe_to_killstream(
    websocket, treeview, counter_var, time_label, dt_label, uri, filter_lists
):
    global GLOBAL_COUNT
    payload = {"action": "sub", "channel": "killstream"}
    await websocket.send(json.dumps(payload))
    print(
        f"Subscribed to {payload['channel']} channel at: "
        + str(datetime.now(timezone.utc))
    )

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
        await connect_websocket(
            uri, treeview, counter_var, time_label, dt_label, filter_lists
        )
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
    print("playing alert sound")
    if sound_file:
        try:
            mixer.init()
            mixer.music.load(sound_file)
            mixer.music.play()

            # Loop to keep the program running until the sound is done playing
            while mixer.music.get_busy():
                time.Clock().tick(10)
        except Exception as e:
            print(f"Error playing alert sound: {e}")


async def process_killmail(
    killmail_data,
    treeview,
    counter_var,
    time_label,
    dt_label,
    filter_lists,
    settings,
):
    # Assigns settings.json values
    max_time_threshold = settings.get("time_threshold", 1200)  #
    max_dropped_value = settings.get("dropped_value", 100000000)  #
    time_threshold_enabled = settings.get("time_threshold_enabled", True)  #
    dropped_value_enabled = settings.get("dropped_value_enabled", True)  #
    audio_alerts_enabled = settings.get("audio_alerts_enabled", True)  #
    # print("max_time_threshold: " + str(max_time_threshold))
    # print("max_dropped_value: " + str(max_dropped_value))
    # print("time_threshhold_enabled: " + str(time_threshold_enabled))
    # print("dropped_value_enabled: " + str(dropped_value_enabled))
    # print("audio_alerts_enabled: " + str(audio_alerts_enabled))

    label_color = "grey"  # Initialize label color

    if (
        "zkb"
        in killmail_data
        # and "npc" in killmail_data["zkb"] # TODO: Make this an option to filter on npc only
        # and killmail_data["zkb"]["npc"]
    ):
        # killmail_data = r'{"attackers":[{"alliance_id":99011606,"character_id":2119099774,"corporation_id":98682653,"damage_done":8592,"final_blow":true,"security_status":-1.0,"ship_type_id":11999,"weapon_type_id":2897},{"alliance_id":99009927,"character_id":2119074886,"corporation_id":98457503,"damage_done":2523,"final_blow":false,"security_status":-10.0,"ship_type_id":35683,"weapon_type_id":35683}],"killmail_id":118434158,"killmail_time":"2024-06-06T07:23:54Z","solar_system_id":30002539,"victim":{"alliance_id":99003581,"character_id":2122282418,"corporation_id":98598862,"damage_taken":11115,"faction_id":500011,"items":[{"flag":11,"item_type_id":22291,"quantity_destroyed":1,"singleton":0},{"flag":5,"item_type_id":8089,"quantity_dropped":4,"singleton":0},{"flag":5,"item_type_id":27453,"quantity_destroyed":360,"singleton":0},{"flag":5,"item_type_id":27441,"quantity_dropped":335,"singleton":0},{"flag":93,"item_type_id":31360,"quantity_destroyed":1,"singleton":0},{"flag":21,"item_type_id":35659,"quantity_destroyed":1,"singleton":0},{"flag":27,"item_type_id":8105,"quantity_destroyed":1,"singleton":0},{"flag":30,"item_type_id":209,"quantity_dropped":36,"singleton":0},{"flag":5,"item_type_id":27435,"quantity_dropped":425,"singleton":0},{"flag":28,"item_type_id":8105,"quantity_destroyed":1,"singleton":0},{"flag":31,"item_type_id":8105,"quantity_dropped":1,"singleton":0},{"flag":20,"item_type_id":8419,"quantity_dropped":1,"singleton":0},{"flag":29,"item_type_id":209,"quantity_destroyed":36,"singleton":0},{"flag":19,"item_type_id":8419,"quantity_destroyed":1,"singleton":0},{"flag":12,"item_type_id":35774,"quantity_dropped":1,"singleton":0},{"flag":23,"item_type_id":54291,"quantity_dropped":1,"singleton":0},{"flag":30,"item_type_id":8105,"quantity_dropped":1,"singleton":0},{"flag":27,"item_type_id":209,"quantity_destroyed":36,"singleton":0},{"flag":92,"item_type_id":31718,"quantity_destroyed":1,"singleton":0},{"flag":28,"item_type_id":209,"quantity_destroyed":36,"singleton":0},{"flag":5,"item_type_id":209,"quantity_dropped":3715,"singleton":0},{"flag":5,"item_type_id":27447,"quantity_destroyed":180,"singleton":0},{"flag":13,"item_type_id":35774,"quantity_dropped":1,"singleton":0},{"flag":31,"item_type_id":209,"quantity_destroyed":36,"singleton":0},{"flag":22,"item_type_id":54291,"quantity_destroyed":1,"singleton":0},{"flag":29,"item_type_id":8105,"quantity_destroyed":1,"singleton":0},{"flag":14,"item_type_id":8225,"quantity_dropped":1,"singleton":0},{"flag":94,"item_type_id":31790,"quantity_destroyed":1,"singleton":0}],"position":{"x":557047590541.1138,"y":-48686415427.03836,"z":1300842933956.2546},"ship_type_id":621}}'
        dropped_value = killmail_data["zkb"]["droppedValue"]
        url = killmail_data["zkb"]["url"]

        # Gather attacker ids, corp ids
        attacker_ship_type_ids = []
        attacker_character_ids = []
        attacker_corp_ids = []
        attacker_alliance_ids = []

        if killmail_data["attackers"]:
            for attacker in killmail_data["attackers"]:
                # Get ship type ids for attackers:
                ship_type_id = attacker.get("ship_type_id")
                if ship_type_id is not None:
                    attacker_ship_type_ids.append(ship_type_id)

                # Get corporation ids for attackers:
                corp_id = attacker.get("corporation_id")
                if corp_id is not None:
                    attacker_corp_ids.append(corp_id)

                # Get player ids for attackers:
                character_id = attacker.get("character_id")
                if character_id is not None:
                    attacker_character_ids.append(character_id)

                # Get attacker alliance ids
                alliance_id = attacker.get("alliance_id")
                if alliance_id is not None:
                    attacker_alliance_ids.append(alliance_id)
        # Gather dropped item ids, corp id
        # @NOTE: solo ids must be wrapped in list or websocket cannot iterate on int error
        dropped_item_ids = []
        alliance_loss_id = [killmail_data["victim"].get("alliance_id", -1)]
        corp_loss_id = [killmail_data["victim"].get("corporation_id", -1)]
        solar_system_id = [killmail_data.get("solar_system_id", -1)]
        character_loss_id = [killmail_data["victim"].get("character_id", -1)]

        if killmail_data["victim"]["items"]:
            # for victim in killmail_data["victim"]:
            for item in killmail_data["victim"]["items"]:
                try:
                    dropped_item_ids.append(item["item_type_id"])
                except Exception as e:
                    print("dropped item ids not found" + str(e))  # debug
                    pass

        # print("Final dropped item id list: " + str(dropped_item_ids))
        # --------------------------
        formatted_dropped_value = format_dropped_value(dropped_value)
        killmail_time = datetime.strptime(
            killmail_data["killmail_time"], "%Y-%m-%dT%H:%M:%SZ"
        ).replace(tzinfo=timezone.utc)
        time_difference = calculate_time_difference(killmail_time)

        # Check if any filters are enabled, if all disabled no checks need to be made.
        any_filters_enabled = any(
            filter_item["enabled"] for filter_item in filter_lists
        )

        if not any_filters_enabled:  # If filter_lists is empty
            print("No filter lists enabled: Performing base checks")
            # No filters, proceed with checks
            if (
                calculate_filter_difference(killmail_time) > max_time_threshold
                and time_threshold_enabled
            ) or (dropped_value < max_dropped_value and dropped_value_enabled):
                # Filter out if any condition is met
                print(
                    f"Filtered out: {killmail_data['killmail_time']} {time_difference} Dropped value: {dropped_value} {url}"
                )
                return

            # Generate kill details
            kill_details = f"{killmail_data['killmail_time']} {time_difference} Dropped value: {dropped_value}\n{url}"

            # Insert kill to viewer
            print("Checks passed. Adding kill to km-viewer")
            treeview.insert(
                "",
                "end",
                values=(formatted_dropped_value, time_difference, url),
                tags=label_color,
            )
        else:
            # Load filters and check for id matches for each filter

            for filter_item in filter_lists:
                enabled = filter_item.get("enabled")

                if not enabled:
                    # Skip this filter if it's not enabled
                    continue

                ignore_dropped_value = filter_item.get("ignore_dropped_value")

                # Calculating eve time occurred ago, and the dropped value.
                if (
                    calculate_filter_difference(killmail_time) > max_time_threshold
                    and time_threshold_enabled == True
                    and not ignore_dropped_value
                ):
                    print(
                        f"MAX TIME VALUE EXCEEDED: Filtered out: {killmail_data['killmail_time']} {time_difference} Dropped value: {dropped_value} {url}"
                    )
                    return
                elif (
                    dropped_value < max_dropped_value
                    and dropped_value_enabled
                    and not ignore_dropped_value
                ):
                    print(
                        f"DROPPED VALUE TOO LOW: Filtered out: {killmail_data['killmail_time']} {time_difference} Dropped value: {dropped_value} {url}"
                    )

                # Kill details webhook message string
                kill_details = f"{killmail_data['killmail_time']} {time_difference} Dropped value: {dropped_value}\n{url}"

                # print(filter_item)
                file_id_list = load_list_from_file(filter_item.get("file"))

                list_check_id = filter_item.get("list_check_id")

                # Retrieve the filter type from the settings.json
                # print("Retrieving comparison lists")  # debug
                if list_check_id == "attacker_ship_type":
                    id_list_to_check = attacker_ship_type_ids
                elif list_check_id == "dropped_item":
                    id_list_to_check = dropped_item_ids
                elif list_check_id == "system":
                    id_list_to_check = solar_system_id
                elif list_check_id == "attacker_corp":
                    id_list_to_check = attacker_corp_ids
                elif list_check_id == "attacker_alliance":
                    id_list_to_check = attacker_alliance_ids
                elif list_check_id == "attacker_character":
                    id_list_to_check = attacker_character_ids
                elif list_check_id == "character_loss":
                    id_list_to_check = character_loss_id
                elif list_check_id == "corporation_loss":
                    id_list_to_check = corp_loss_id
                elif list_check_id == "alliance_loss":
                    id_list_to_check = alliance_loss_id
                else:
                    print("Filter skipped, invalid")
                    continue  # if invalid, skip the filter

                # print("Gathering ids from id_list_to_check")  # debug
                match_found = False
                for filter_id in file_id_list:
                    if match_found:
                        break

                    for id in id_list_to_check:
                        if filter_id == id:

                            label_color = filter_item.get("color", "")
                            if audio_alerts_enabled and filter_item.get(
                                "sound"
                            ):  # filter sound = true or false
                                play_alert_sound(filter_item.get("sound"))

                            # await asyncio.sleep(0.6)
                            print("Checks passed. Adding kill to km-viewer")
                            print("Applying label color " + str(label_color))
                            treeview.insert(
                                "",
                                "end",
                                values=(
                                    formatted_dropped_value,
                                    time_difference,
                                    url,
                                ),
                                tags=(label_color + ".TLabel",),
                            )

                            try:
                                if filter_item.get("webhook", False):
                                    await send_discord_webhook(
                                        f"Kill found! {kill_details}"
                                    )
                            except TypeError as e:
                                print("Error sending webhook" + str(e))

                            print("Match found, breaking loop")
                            match_found = True
                            break  # Exit loop after first match to avoid duplicate entries
                            # TODO: Could add a counter to the treeview instead, showing the number of matches for that entry

        print(
            f"Filtered out: {killmail_data['killmail_time']} {time_difference} Dropped value: {dropped_value} {url}"
        )
        print(
            f"Killmail time: {killmail_time}, time difference: {time_difference}, dropped value: {dropped_value}"
        )

    else:
        print("zkb not in km data")


def load_list_from_file(filename):
    try:
        with open(filename, "r") as file:
            return [int(line.strip()) for line in file.readlines()]
    except FileNotFoundError:
        print("File not found")
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


async def connect_websocket(
    uri, treeview, counter_var, time_label, dt_label, filter_lists
):
    while True:
        try:
            async with websockets.connect(uri) as websocket:
                await subscribe_to_killstream(
                    websocket,
                    treeview,
                    counter_var,
                    time_label,
                    dt_label,
                    uri,
                    filter_lists,
                )
        except Exception as e:
            print(
                f"WebSocket connection closed (connect_websocket - await subscribe to killstream): {e}"
            )
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
        json.dump(
            settings, file, indent=4
        )  # Use indent parameter for pretty formatting


async def start_gui(settings, with_gui=True):
    if with_gui:
        # Create the root window
        root = tk.Tk()
        root.iconbitmap("logo.ico")
        root.minsize(280, 300)
        root.title("KM Hunter 1.2")
        root.pack_propagate(False)

        # Create the main frame
        main_frame = tk.Frame(root)
        main_frame.pack(fill="both", expand=True)
        main_frame.pack_propagate(False)

        # Create the treeview widget
        treeview = ttk.Treeview(
            main_frame, columns=("Value", "Occurred"), show="headings"
        )
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
        treeview.tag_configure("purple.TLabel", background="purple", foreground="white")
        treeview.tag_configure("orange.TLabel", background="orange", foreground="black")
        treeview.tag_configure(
            "blue.TLabel", background="light blue", foreground="black"
        )  # Light blue background
        treeview.tag_configure("red.TLabel", background="red", foreground="white")
        treeview.tag_configure("grey.TLabel", background="grey", foreground="black")
        treeview.tag_configure(
            "green.TLabel", background="light green", foreground="black"
        )

        # Create a button to clear kills
        clear_button = tk.Button(
            root, text="Clear kills", command=lambda: clear_treeview(treeview)
        )
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

        dropdown_menu = tk.Menubutton(
            filter_frame, text="Filter Lists", relief="raised"
        )
        dropdown_menu.pack(side=tk.LEFT, padx=5)

        dropdown_menu.menu = tk.Menu(dropdown_menu, tearoff=0)
        dropdown_menu["menu"] = dropdown_menu.menu

        enabled_vars = []
        for filter_item in settings["filter_lists"]:
            enabled = tk.BooleanVar()
            enabled.set(filter_item["enabled"])
            enabled_vars.append(enabled)

            dropdown_menu.menu.add_checkbutton(
                label=filter_item["file"], variable=enabled
            )

        def toggle_dropdown(event=None):
            if dropdown_menu.menu.winfo_ismapped():
                dropdown_menu.menu.unpost()
            else:
                dropdown_menu.menu.post(
                    dropdown_menu.winfo_rootx(),
                    dropdown_menu.winfo_rooty() + dropdown_menu.winfo_height(),
                )

        dropdown_menu.bind("<Button-1>", toggle_dropdown)

        # Add a button to update settings
        update_button = tk.Button(
            filter_update_frame,
            text="Update Settings",
            command=lambda: update_settings(settings, enabled_vars),
        )
        update_button.pack(side=tk.LEFT, padx=5)

        # Run the Tkinter event loop
        try:
            await asyncio.gather(
                connect_websocket(
                    uri,
                    treeview,
                    counter_var,
                    time_label,
                    dt_label,
                    settings["filter_lists"],
                ),
                run_tkinter_loop(root, treeview, time_label, dt_label),
            )
        except tk.TclError as e:
            if "application has been destroyed" not in str(e):
                raise
    else:
        uri = "wss://zkillboard.com/websocket/"
        try:
            await asyncio.gather(
                connect_websocket(
                    uri, None, None, None, None, settings["filter_lists"]
                ),
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
                await subscribe_to_killstream(
                    websocket, None, None, None, None, uri, settings["filter_lists"]
                )
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
            settings = {}
            settings_data = json.load(file)

            filter_lists = settings_data.get("filter_lists", [])
            dropped_value_enabled = settings_data.get("dropped_value_enabled", False)
            time_threshold_enabled = settings_data.get("time_threshold_enabled", False)
            time_threshold = int(settings_data.get("time_threshold"))
            dropped_value = float(settings_data.get("dropped_value"))
            audio_alerts_enabled = settings_data.get("audio_alerts_enabled", False)

            if (
                filter_lists
                and dropped_value_enabled
                and time_threshold_enabled
                and time_threshold
                and dropped_value
                and audio_alerts_enabled
            ):
                settings = settings_data
                print("settings refreshed successfully!")
                # print(settings_data)
            else:
                raise Exception("Values not loaded correctly for json settings")
    except FileNotFoundError:
        print("Settings.json file not found or error parsing edited json")
        settings = {"filter_lists": [], "settings": DEFAULT_SETTINGS}
    return settings


def save_settings(settings):
    with open("settings.json", "w") as file:
        json.dump(settings, file, indent=4)


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

# Debug, wrap entire program in try statement
# except Exception as e:
#     pdb.post_mortem()
