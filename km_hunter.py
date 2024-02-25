import asyncio
import json
from datetime import datetime, timezone
import tkinter as tk
from tkinter import scrolledtext, ttk
import websockets
import webbrowser
import simpleaudio
import sys
import os
import re
import requests
from dotenv import load_dotenv
import tkinter.font as tkFont

# Load environment variables from .env file
load_dotenv()

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
    "belt_hunter_mode": False,
    "officers": True,
    "abyssal_mods": False,
    "blueprints": False,
    "dropped_value_enabled": False,
    "time_threshold_enabled": True,
    "time_threshold": 1200,
    "dropped_value": 100000000,
    "audio_alerts_enabled": True,  # New setting for audio alerts
}

async def subscribe_to_killstream(
    websocket, treeview, counter_var, time_label, dt_label, uri
):
    payload = {"action": "sub", "channel": "killstream"}
    await websocket.send(json.dumps(payload))
    print(f"Subscribed to {payload['channel']} channel")

    # Initialize the counter
    counter = 0
    counter_var.set(counter)

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
                settings,
            )
            counter += 1
            counter_var.set(counter)
    except websockets.ConnectionClosed:
        print("WebSocket connection closed")
        connect_websocket(uri, treeview, counter_var, time_label, dt_label)
    finally:
        ping_task.cancel()

async def send_pings(websocket):
    while True:
        try:
            await websocket.ping()
            print("PING!")
            await asyncio.sleep(30)
        except asyncio.CancelledError:
            break

def open_url(url):
    webbrowser.open(url)

async def process_killmail(
    killmail_data, treeview, counter_var, time_label, dt_label, settings
):
    # Assigns settings.json values
    officers = settings["officers"]
    belt_hunter_mode = settings["belt_hunter_mode"]
    abyssal_mods = settings["abyssal_mods"]
    blueprints = settings["blueprints"]
    max_time_threshold = settings["time_threshold"]
    max_dropped_value = settings["dropped_value"]
    time_threshold_enabled = settings["time_threshold_enabled"]
    dropped_value_enabled = settings["dropped_value_enabled"]
    audio_alerts_enabled = settings["audio_alerts_enabled"]

    label_color = ""  # Initialize label color

    if (
        "zkb" in killmail_data
        and "npc" in killmail_data["zkb"]
        and killmail_data["zkb"]["npc"]
    ):
        dropped_value = killmail_data["zkb"]["droppedValue"]
        url = killmail_data["zkb"]["url"]
        formatted_dropped_value = format_dropped_value(dropped_value)
        killmail_time = datetime.strptime(
            killmail_data["killmail_time"], "%Y-%m-%dT%H:%M:%SZ"
        ).replace(tzinfo=timezone.utc)
        time_difference = calculate_time_difference(killmail_time)

        if (
            calculate_filter_difference(killmail_time) > max_time_threshold
            and time_threshold_enabled == True
        ):
            print(
                f"Filtered out: {killmail_data['killmail_time']} {time_difference} Dropped value: {dropped_value}"
            )
            return

        if officers:
            officers_list = [
                13557, 13654, 13564, 13544, 13573, 13589, 13603, 52475,
                13667, 13584, 13635, 13659, 13615, 13661, 13609, 13538,
                13536, 13580, 13622, 13561, 13541
            ]
            o = False
            for officer in officers_list:
                if str(officer) in killmail_data:
                    await send_discord_webhook(f"Officer {officer} found!")
                    label_color = "purple"
                    if audio_alerts_enabled:
                        play_purple_alert()
                    o = True

        if belt_hunter_mode:
            belter_list = [
                33174, 13602, 13601, 23356, 23355, 13578, 13579, 13588,
                23357, 13583, 23358, 23469, 13660, 13658, 13666, 23471,
                23470, 23472, 13665, 13653, 33164, 13652, 13562, 13560,
                13572, 23300, 13563, 23299, 13559, 23301, 23302, 13556,
                33172, 22873, 13535, 13537, 22871, 13542, 13540, 22874,
                22872, 13539, 33173, 13543, 33163, 13633, 23401, 23402,
                13606, 13620, 23400, 13621, 13634, 13614, 23403, 33163
            ]
            mordus_list = [33866, 33864, 33865]
            for mordu in mordus_list:
                if str(mordu) in killmail_data:
                    label_color = "orange"

            for belter in belter_list:
                if str(belter) in killmail_data:
                    label_color = "orange"
                elif not o:
                    return

        if (
            check_number_combination(killmail_data, blueprints, abyssal_mods)
            and belt_hunter_mode == False
        ):
            label_color = "blue"
            if audio_alerts_enabled:
                play_blue_alert()
        else:
            if dropped_value < max_dropped_value and dropped_value_enabled == True:
                print(
                    f"Filtered out: {killmail_data['killmail_time']} {time_difference} Dropped value: {dropped_value}"
                )
                return
            if audio_alerts_enabled:
                play_audio_alert()

        await asyncio.sleep(0.6)
        kill_details = (
            f"Dropped Value: {formatted_dropped_value} - Occurred: {time_difference}"
        )

        try:
            await send_discord_webhook(f"Kill found! {kill_details} \nurl: {url}")
        except TypeError as e:
            print("Error sending webhook" + str(e))

        treeview.insert("", "end", values=(formatted_dropped_value, time_difference, url), tags=label_color)

def check_number_combination(raw_response, blueprints, abyssal_mods):
    response = str(raw_response)
    if blueprints:
        with open("blueprints.txt", "r") as file:
            number_combinations_to_check = [line.strip() for line in file.readlines()]
        for combination in number_combinations_to_check:
            if re.search('"item_type_id": ' + combination + ",", response):
                return True
    if abyssal_mods:
        with open("abyssals.txt", "r") as file:
            abyssal_ids = [line.strip() for line in file.readlines()]
        for id in abyssal_ids:
            if re.search('"item_type_id": ' + id + ",", response):
                return True
    return False

def play_audio_alert():
    audio_path = "alert.wav"
    try:
        wave_obj = simpleaudio.WaveObject.from_wave_file(audio_path)
        play_obj = wave_obj.play()
        play_obj.wait_done()
    except Exception as e:
        print(f"Error playing audio alert: {e}")

def play_purple_alert():
    purple_audio_path = "purple_alert.wav"
    try:
        wave_obj = simpleaudio.WaveObject.from_wave_file(purple_audio_path)
        play_obj = wave_obj.play()
        play_obj.wait_done()
    except Exception as e:
        print(f"Error playing purple audio alert: {e}")

def play_blue_alert():
    blue_audio_path = "blue_alert.wav"
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

async def connect_websocket(uri, treeview, counter_var, time_label, dt_label):
    while True:
        try:
            async with websockets.connect(uri) as websocket:
                await subscribe_to_killstream(
                    websocket, treeview, counter_var, time_label, dt_label, uri
                )
        except websockets.exceptions.ConnectionClosed as e:
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


async def start_gui():
    root = tk.Tk()
    root.minsize(280, 300)
    root.title("NPC Hunter 1.1")
    root.pack_propagate(False)

    main_frame = tk.Frame(root)
    main_frame.pack(fill="both", expand=True)
    main_frame.pack_propagate(False)

    treeview = ttk.Treeview(main_frame, columns=("Value", "Occurred"), show="headings")
    treeview.heading("Value", text="Dropped Value")
    treeview.heading("Occurred", text="Occurred")

    # Configure the column widths to adjust automatically based on content
    treeview.column("Value", width=tkFont.Font().measure("Dropped Value"))
    treeview.column("Occurred", width=tkFont.Font().measure("Occurred"))

    treeview.pack(side="left", fill="both", expand=True)

    sb = tk.Scrollbar(main_frame, command=treeview.yview)
    sb.pack(side="right", fill="y")
    treeview.configure(yscrollcommand=sb.set)

    clear_button = tk.Button(root, text="Clear kills", command=lambda: clear_treeview(treeview))
    clear_button.pack(pady=5)

    info_frame = tk.Frame(root, relief=tk.RAISED, borderwidth=1)
    info_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

    dt_frame = tk.Frame(root, relief=tk.RAISED, borderwidth=1)
    dt_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

    counter_var = tk.IntVar()
    counter_label = tk.Label(info_frame, text="Kills: ")
    counter_label.pack(side=tk.LEFT, padx=5)
    counter_box = tk.Label(info_frame, textvariable=counter_var)
    counter_box.pack(side=tk.LEFT, padx=5)

    dt_label = tk.Label(dt_frame, text="DT In: ")
    dt_label.pack(side=tk.BOTTOM)

    time_label = tk.Label(info_frame, text="EVE Time: ")
    time_label.pack(side=tk.BOTTOM)

    root.protocol(
        "WM_DELETE_WINDOW", lambda: close_window(root)
    )

    uri = "wss://zkillboard.com/websocket/"

    treeview.bind("<Double-1>", lambda event: open_url_in_browser(treeview))

    try:
        await asyncio.gather(
            connect_websocket(uri, treeview, counter_var, time_label, dt_label),
            run_tkinter_loop(root, treeview, time_label, dt_label),
        )
    except tk.TclError as e:
        if "application has been destroyed" not in str(e):
            raise

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
    await start_gui()

if __name__ == "__main__":
    asyncio.run(main())
