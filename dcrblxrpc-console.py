import psutil
import time
import os
import re
import requests
import json
import logging
from bs4 import BeautifulSoup
from pypresence import Presence
from pathlib import Path

# Setup logging
LOG_FILENAME = 'dcrblxrpc.log'
logging.basicConfig(filename=LOG_FILENAME, level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Configuration file path
CONFIG_FILE = 'cfg.json'
rpc_open = False
rpc_tryna_connect = False

# Function to create a default config file if it doesn't exist
def create_default_config():
    default_config = {
        "interval": "3",
        "app_id": "INSERT_APP_ID",
        "large_image": "https://cdn.discordapp.com/app-icons/363445589247131668/f2b60e350a2097289b3b0b877495e55f.webp?size=160&keep_aspect_ratio=false",
        "small_image": "https://cdn.discordapp.com/app-icons/363445589247131668/f2b60e350a2097289b3b0b877495e55f.webp?size=160&keep_aspect_ratio=false"
    }
    with open(CONFIG_FILE, 'w') as f:
        json.dump(default_config, f, indent=4)
    print(f"Created {CONFIG_FILE}. Please enter your Discord app_id.")
    logging.info(f"Created {CONFIG_FILE}. Prompting user to fill in the details.")

# Load configuration from cfg.json
if not os.path.exists(CONFIG_FILE):
    create_default_config()
    print(f"Error: {CONFIG_FILE} is missing necessary information.")
    logging.error(f"{CONFIG_FILE} is missing. Created a new one.")
    time.sleep(10)
    exit()

with open(CONFIG_FILE, 'r') as f:
    try:
        config = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Failed to parse {CONFIG_FILE}. Please check the file format.")
        logging.error(f"Failed to parse {CONFIG_FILE}: {e}")
        time.sleep(10)
        exit()

# Get the Discord app_id
DISCORD_CLIENT_ID = config.get('app_id')

if not DISCORD_CLIENT_ID:
    print(f"Please fill in the required fields in {CONFIG_FILE} (app_id).")
    logging.error(f"Missing app_id in {CONFIG_FILE}.")
    time.sleep(10)
    exit()

# Initialize Discord RPC
rpc = Presence(DISCORD_CLIENT_ID)

# Regex pattern for detecting game join messages
LOG_REGEX = r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d{3}Z,\d+\.\d+,\w+,\d+ \[FLog::Output\] ! Joining game '[\w-]+' place (\d+) at [\d.]+"

# Function to determine the log directory based on user/global install
def get_log_directory():
    # User-specific log directory
    user_log_dir = os.path.expandvars(r"C:\Users\%USERNAME%\AppData\Local\Roblox\logs")
    
    if os.path.exists(user_log_dir):
        logging.info(f"Using user log directory: {user_log_dir}")
        return user_log_dir
    else:
        logging.warning("User log directory not found, checking global location.")
        global_log_dir = r"C:\Program Files (x86)\Roblox\logs"
        if os.path.exists(global_log_dir):
            logging.info(f"Using global log directory: {global_log_dir}")
            return global_log_dir
        else:
            logging.error("No valid log directory found!")
            print("Error: Could not find Roblox logs in either user or global directories.")
            return None

# Function to get the latest log file
def get_latest_log():
    log_dir = get_log_directory()
    if not log_dir:
        return None

    log_files = [os.path.join(log_dir, f) for f in os.listdir(log_dir) if f.endswith('.log')]
    if not log_files:
        logging.error("No log files found.")
        print("Error: No log files found in the log directory.")
        return None
    
    latest_log = max(log_files, key=os.path.getmtime)
    logging.info(f"Latest log file: {latest_log}")
    return latest_log

# Function to find place ID in the log file
def find_place_id(log_file):
    if not log_file:
        return None
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                match = re.search(LOG_REGEX, line)
                if match:
                    place_id = match.group(1)
                    logging.info(f"Found place ID: {place_id}")
                    return place_id
    except Exception as e:
        logging.error(f"Error reading log file: {e}")
        print(f"Error: Could not read the log file: {e}")
    logging.warning("No place ID found in log.")
    return None

# Function to get the game name from place ID
def get_game_name(place_id):
    url = f"https://www.roblox.com/games/{place_id}"
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        game_name_tag = soup.find("h1", class_="game-name")
        if game_name_tag:
            game_name = game_name_tag.text.strip()
            logging.info(f"Game name: {game_name}")
            return game_name
    except Exception as e:
        logging.error(f"Failed to fetch game name: {e}")
        print(f"Error: Could not retrieve game name from Roblox: {e}")
    return "Unknown Game"

# Function to update Discord RPC
def update_discord_rpc(game_name, start_time):
    try:
        rpc.update(
            state=f"Playing {game_name}",
            large_image=config.get('large_image'),
            small_image=config.get('small_image'),
            start=start_time
        )
        logging.info(f"Updated Discord RPC for game: {game_name}")
        print(f"Updated Discord RPC for game: {game_name}")
    except Exception as e:
        logging.error(f"Failed to update Discord RPC: {e}")
        print(f"Error: Could not update Discord RPC: {e}")

# Function to monitor Roblox process
def monitor_roblox_process():
    rpc_open = False
    start_time = None
    game_name = None
    place_id = None
    previous_game_name = None  # Store the previous game name

    while True:
        # Check if Roblox process is running
        if "RobloxPlayerBeta.exe" in (p.name() for p in psutil.process_iter()):
            logging.info("RobloxPlayerBeta.exe is running. Checking log...")
            interval_cfg22 = config.get('interval')
            interval_cfg = int(interval_cfg22)
            time.sleep(interval_cfg)
            latest_log = get_latest_log()
            if latest_log:
                place_id = find_place_id(latest_log)

            if place_id:
                game_name = get_game_name(place_id)

                # Only update Discord RPC if the game name has changed
                if game_name and game_name != previous_game_name:
                    start_time = int(time.time())
                    if rpc_open:
                        update_discord_rpc(game_name, start_time)
                    else:
                        try:
                            rpc.connect()
                            rpc_open = True
                            update_discord_rpc(game_name, start_time)
                            logging.info("Discord RPC connected.")
                            print("Discord RPC connected.")
                        except Exception as e:
                            logging.error(f"Failed to connect Discord RPC: {e}")
                            print(f"Error: Could not connect to Discord RPC: {e}")

                previous_game_name = game_name  # Update the previous game name

        else:  # If the Roblox process is not running
            if rpc_open:
                logging.info("Closing Discord RPC.")
                print("Closing Discord RPC.")
                rpc.close()
                rpc_open = False
                start_time = None
                game_name = None
                place_id = None
                previous_game_name = None  # Reset previous game name

        time.sleep(5)

if __name__ == "__main__":
    monitor_roblox_process()