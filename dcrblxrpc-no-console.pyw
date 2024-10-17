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
import tkinter as tk
from tkinter import messagebox
import subprocess
import ctypes
import sys
import tempfile

# Setup logging
LOG_FILENAME = 'dcrblxrpc.log'
logging.basicConfig(filename=LOG_FILENAME, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuration file path
CONFIG_FILE = 'cfg.json'
rpc_open = False

# Helper function to log and log_and_print messages
def log_and_print(message):
    logging.info(message)
    print(message)

# Function to create a default config file if it doesn't exist
def create_default_config():
    default_config = {
        "interval": "3",
        "app_id": "INSERT_APP_ID",
        "large_image": "AUTO",
        "RTSSPatch": "True"
    }
    with open(CONFIG_FILE, 'w') as f:
        json.dump(default_config, f, indent=4)
    log_and_print(f"Created {CONFIG_FILE}. Please enter your Discord app_id.")
    logging.info(f"Created {CONFIG_FILE}. Prompting user to fill in the details.")

# Load configuration from cfg.json
if not os.path.exists(CONFIG_FILE):
    create_default_config()
    log_and_print(f"Error: {CONFIG_FILE} is missing necessary information.")
    logging.error(f"{CONFIG_FILE} is missing. Created a new one.")
    time.sleep(10)
    exit()

with open(CONFIG_FILE, 'r') as f:
    try:
        config = json.load(f)
    except json.JSONDecodeError as e:
        log_and_print(f"Error: Failed to parse {CONFIG_FILE}. Please check the file format.")
        logging.error(f"Failed to parse {CONFIG_FILE}: {e}")
        time.sleep(10)
        exit()

# Get the Discord app_id
DISCORD_CLIENT_ID = config.get('app_id')
if not DISCORD_CLIENT_ID:
    log_and_print(f"Please fill in the required fields in {CONFIG_FILE} (app_id).")
    logging.error(f"Missing app_id in {CONFIG_FILE}.")
    time.sleep(10)
    exit()

RTSS_PATCH = config.get('RTSSPatch', "True").lower() == "true"

# Initialize Discord RPC
rpc = Presence(DISCORD_CLIENT_ID)

# Regex pattern for detecting game join messages
LOG_REGEX = r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d{3}Z,\d+\.\d+,\w+,\d+ \[FLog::Output\] ! Joining game '[\w-]+' place (\d+) at [\d.]+"

# Function to determine the log directory based on user/global install
def get_log_directory():
    # User-specific log directory
    user_log_dir = os.path.expandvars(r"C:\Users\%USERNAME%\AppData\Local\Roblox\logs")
    if os.path.exists(user_log_dir):
        log_and_print(f"Using user log directory: {user_log_dir}")
        return user_log_dir
    else:
        logging.warning("User log directory not found, checking global location.")
        global_log_dir = r"C:\Program Files (x86)\Roblox\logs"
        if os.path.exists(global_log_dir):
            log_and_print(f"Using global log directory: {global_log_dir}")
            return global_log_dir
        else:
            log_and_print("Error: Could not find Roblox logs in either user or global directories.")
            return None

# Function to get the latest log file
def get_latest_log():
    log_dir = get_log_directory()
    if not log_dir:
        return None

    log_files = [os.path.join(log_dir, f) for f in os.listdir(log_dir) if f.endswith('.log')]
    if not log_files:
        log_and_print("Error: No log files found in the log directory.")
        return None

    latest_log = max(log_files, key=os.path.getmtime)
    log_and_print(f"Latest log file: {latest_log}")

    # Check if the log file is older than 5 minutes
    log_age = time.time() - os.path.getmtime(latest_log)
    if log_age > 300:  # 300 seconds = 5 minutes
        log_and_print("Logs are too old, retrying...")

        # Retry getting the latest log from the global directory if needed
        global_log_dir = r"C:\Program Files (x86)\Roblox\logs"
        if os.path.exists(global_log_dir):
            log_files = [os.path.join(global_log_dir, f) for f in os.listdir(global_log_dir) if f.endswith('.log')]
            if not log_files:
                log_and_print("Error: No log files found in the global directory.")
                return None

            latest_log = max(log_files, key=os.path.getmtime)
            log_age = time.time() - os.path.getmtime(latest_log)
            if log_age > 300:  # Check again
                log_and_print("Roblox is not installed or running properly!")
                return None

    return latest_log

# Fetch large image URL based on the universe ID
def fetch_large_image_url(universe_id):
    url = "https://thumbnails.roblox.com/v1/batch"
    data = [{
        "requestId": f"{universe_id}::GameIcon:256x256:webp:regular",
        "type": "GameIcon",
        "targetId": universe_id,
        "token": "",
        "format": "webp",
        "size": "256x256"
    }]
    try:
        log_and_print(f"Fetching large image for universe ID: {universe_id}")
        response = requests.post(url, headers={"Content-Type": "application/json"}, json=data)
        if response.status_code == 200:
            json_data = response.json()
            if json_data['data']:
                image_url = json_data['data'][0]['imageUrl']
                log_and_print(f"Successfully fetched large image URL: {image_url}")
                return image_url
            else:
                log_and_print(f"No image data returned for universe ID: {universe_id}")
        else:
            log_and_print(f"Failed to fetch image. Status Code: {response.status_code}")
    except Exception as e:
        log_and_print(f"Error: Could not fetch large image: {e}")
    return None

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
                    log_and_print(f"Found place ID: {place_id}")
                    return place_id
    except Exception as e:
        log_and_print(f"Error: Could not read the log file: {e}")
    log_and_print("Warning: No place ID found in log.")
    return None

# Function to get the game name from place ID
def get_game_details(place_id):
    url = f"https://www.roblox.com/games/{place_id}"
    try:
        log_and_print(f"Fetching game details for place ID: {place_id}")
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract the universe ID and game name from the HTML
        game_meta_data = soup.find("div", id="game-detail-meta-data")
        if game_meta_data:
            universe_id = game_meta_data.get('data-universe-id')
            game_name = game_meta_data.get('data-place-name')
            log_and_print(f"Found universe ID: {universe_id} and game name: {game_name}")
            return game_name, universe_id
        else:
            log_and_print(f"Game meta data not found for place ID: {place_id}")
    except Exception as e:
        log_and_print(f"Error: Could not retrieve game details from Roblox: {e}")

    return "Unknown Game", None

# Function to update Discord RPC
def update_discord_rpc(game_name, start_time, universe_id=None):
    try:
        large_image_url = config.get('large_image')

        # If the large image is set to AUTO, fetch the actual image URL using universe ID
        if large_image_url == "AUTO" and universe_id:
            large_image_url = fetch_large_image_url(universe_id)

        # Default to configured large image if AUTO fetching fails
        if not large_image_url:
            large_image_url = config.get('large_image')

        rpc.update(
            state=f"Playing {game_name}",
            large_image=large_image_url,
            start=start_time
        )
        log_and_print(f"Updated Discord RPC for game: {game_name}")
    except Exception as e:
        log_and_print(f"Error: Could not update Discord RPC: {e}")
        
        
        
        
        
def restart_msi_afterburner(path):
    # Use PowerShell to restart MSI Afterburner with elevated privileges
    ps_command = f"Start-Process '{path}' -Verb RunAs"
    command = ['powershell.exe', '-command', ps_command]
    runCmd(command)

def runCmd(command):
    try:
        # Execute the command and capture output
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        log_and_print(f"Command output: {result.stdout}")
    except subprocess.CalledProcessError as e:
        log_and_print(f"Command output: {result.stdout}")


 
    
def apply_rtss_patch():
    rtss_executable_path = None
    msi_afterburner_path = None

    # Check if MSI Afterburner and RTSS are running and get their paths
    for proc in psutil.process_iter(attrs=['name', 'exe']):
        if proc.info['name'] == 'MSIAfterburner.exe':
            msi_afterburner_path = proc.info['exe']
            log_and_print(f"Found MSI Afterburner: {msi_afterburner_path}")
        elif proc.info['name'] == 'RTSS.exe':
            rtss_executable_path = proc.info['exe']
            log_and_print(f"Found RTSS: {rtss_executable_path}")

    if rtss_executable_path and msi_afterburner_path:
        profile_folder = os.path.join(os.path.dirname(rtss_executable_path), "Profiles")
        roblox_config_path = os.path.join(profile_folder, "RobloxPlayerBeta.exe.cfg")
        

        # Check if the patch has already been applied
        if os.path.exists(roblox_config_path):
            return  # Exit the function early

        # Create the Tkinter window for the message box
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', 1)
        user_response = messagebox.askokcancel("RTSSPatch needed", 
            "Apply? This will only be needed once. You may need to approve a UAC prompt afterwards.")
        
        if user_response:
            
            # Kill processes before applying the patch
            for proc_name in ['MSIAfterburner.exe', 'RTSSHooksLoader64.exe', 'RTSS.exe', 'RobloxPlayerBeta.exe']:
                for proc in psutil.process_iter(attrs=['name']):
                    if proc.info['name'] == proc_name:
                        log_and_print(f"Killing process: {proc_name}")
                        proc.kill()

            # Create the configuration file for RobloxPlayerBeta.exe
            try:
                create_config_file()

                # Restart MSI Afterburner using elevated privileges
                restart_msi_afterburner(msi_afterburner_path)

                # Inform the user that the RTSS patch has been applied
                messagebox.showinfo("RTSSPatch applied", "RTSSPatch applied, you may need to run the game again.")
            except Exception as e:
                log_and_print(f"An error occurred while applying the patch: {e}")
                messagebox.showerror("Error", f"Failed to apply patch: {e}")
            finally:
                root.destroy()  # Ensure root is destroyed at the end
        else:
            log_and_print("User canceled the RTSS patch application.")
            root.destroy()  # Ensure root is destroyed if user cancels
    else:
        return None
            
            

        
        

def create_config_file():
    # Prepare the configuration content as a list of lines
    config_content_lines = [
        "[OSD]",
        "EnableOSD=1",
        "EnableBgnd=1",
        "EnableFill=0",
        "EnableStat=0",
        "BaseColor=00FF8000",
        "BgndColor=00000000",
        "FillColor=80000000",
        "PositionX=1",
        "PositionY=1",
        "ZoomRatio=2",
        "CoordinateSpace=0",
        "EnableFrameColorBar=0",
        "FrameColorBarMode=0",
        "RefreshPeriod=500",
        "IntegerFramerate=1",
        "MaximumFrametime=0",
        "EnableFrametimeHistory=0",
        "FrametimeHistoryWidth=-32",
        "FrametimeHistoryHeight=-4",
        "FrametimeHistoryStyle=0",
        "ScaleToFit=0",
        "[Statistics]",
        "FramerateAveragingInterval=1000",
        "PeakFramerateCalc=0",
        "PercentileCalc=0",
        "FrametimeCalc=0",
        "PercentileBuffer=0",
        "[Framerate]",
        "Limit=0",
        "LimitDenominator=1",
        "LimitTime=0",
        "LimitTimeDenominator=1",
        "SyncScanline0=0",
        "SyncScanline1=0",
        "SyncPeriods=0",
        "SyncLimiter=0",
        "PassiveWait=1",
        "[Hooking]",
        "EnableHooking=0",
        "EnableFloatingInjectionAddress=0",
        "EnableDynamicOffsetDetection=0",
        "HookLoadLibrary=0",
        "HookDirectDraw=0",
        "HookDirect3D8=0",
        "HookDirect3D9=0",
        "HookDirect3DSwapChain9Present=1",
        "HookDXGI=0",
        "HookDirect3D12=0",
        "HookOpenGL=0",
        "HookVulkan=0",
        "InjectionDelay=15000",
        "UseDetours=0",
        "[Font]",
        "Height=-9",
        "Weight=400",
        "Face=Unispace",
        "[RendererDirect3D8]",
        "Implementation=2",
        "[RendererDirect3D9]",
        "Implementation=2",
        "[RendererDirect3D10]",
        "Implementation=2",
        "[RendererDirect3D11]",
        "Implementation=2",
        "[RendererDirect3D12]",
        "Implementation=2",
        "[RendererOpenGL]",
        "Implementation=2",
        "[RendererVulkan]",
        "Implementation=2",
        "[Info]",
        "Timestamp=16-10-2024, 17:41:31"
    ]

    # Create a temporary batch file to execute the commands
    with tempfile.NamedTemporaryFile(delete=False, suffix=".bat") as temp_batch_file:
        temp_batch_file.write(b'@echo off\n')

        # Loop through each line of the config and write it with echo
        for line in config_content_lines:
            temp_batch_file.write(f'echo {line} >> "C:\\Program Files (x86)\\RivaTuner Statistics Server\\Profiles\\RobloxPlayerBeta.exe.cfg"\n'.encode('utf-8'))
        
        temp_batch_file_path = temp_batch_file.name

    # Execute the batch file with elevated privileges
    command = ['powershell.exe', '-Command', f'Start-Process cmd.exe -ArgumentList "/c {temp_batch_file_path}" -Verb RunAs']
    runCmd(command)



def monitor_roblox_process():
    global rpc_open
    start_time = None
    game_name = None
    place_id = None
    previous_game_name = None
    universe_id = None

    while True:
        if "RobloxPlayerBeta.exe" in (p.name() for p in psutil.process_iter()):
            log_and_print("RobloxPlayerBeta.exe is running. Checking log...")
            if RTSS_PATCH:
                apply_rtss_patch()

            interval_cfg = int(config.get('interval', 3))
            time.sleep(interval_cfg)

            latest_log = get_latest_log()
            if latest_log:
                place_id = find_place_id(latest_log)
                if place_id:
                    game_name, universe_id = get_game_details(place_id)
                    if game_name and game_name != previous_game_name:
                        start_time = int(time.time())
                        if rpc_open:
                            update_discord_rpc(game_name, start_time, universe_id)
                        else:
                            try:
                                rpc.connect()
                                rpc_open = True
                                update_discord_rpc(game_name, start_time, universe_id)
                                log_and_print("Discord RPC connected.")
                            except Exception as e:
                                log_and_print(f"Error: Could not connect to Discord RPC: {e}")
                        previous_game_name = game_name
        else:
            if rpc_open:
                log_and_print("Closing Discord RPC.")
                rpc.close()
                rpc_open = False
            time.sleep(5)

if __name__ == "__main__":
    monitor_roblox_process()