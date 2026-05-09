
###############################################################################
#                    V.G.A.R  Front End (PC Python Code)                      #
#                          Beta 0.1 09.05.26    (build 112)                   #
###############################################################################
#  For Adrino AKI USB Atari Control:                                          #
#     Requires VGAR Beta0.1 HID passthrough code on UNO R3                    #
#     Adrino needs to then be flashed with Adrino-keyboard-0.3.hex            #                                                                         
#     VGAR passes HID codes via PC serial interface connected to Adrino RX/TX #
###############################################################################
#                     Known Bugs / missing features                           #
###############################################################################
#  Arrow keys in Control or capture keys not working                          #
#  Shift functionality issues in key capture (also clear / insert as shifted) #
#  No inverse key (HID code not located - may need Adrino code update)        #
#  No break key (HID code not located - may need Adrino code update)          #   
###############################################################################

#First Importing  Required code libraries
import tkinter as tk         # GUI
from tkinter import Tk, ttk, messagebox, Label, Button, Radiobutton, IntVar, font ,filedialog
from PIL import Image, ImageTk
import subprocess
import time                  
import random
from random import choice
import threading
import pyperclip             # Copy/Paste access
#Requests import for flash API call
import requests
import pygame.mixer
from textwrap import shorten
import os  # For file operations
import psutil #for process kill
import tinydb
from tinydb import TinyDB, Query   # For lightweight database using ASCII File for Good/Bad Games recording
import keyboard                   #For Keyboard capture functionality
import json
import queue  #Queuing functions for managing keypresses
import serial # For serial input
###Some quick serial debug here
print ("serial loaded:")
print(serial.__file__)
print(serial.Serial)
import inspect
print(serial)
print(dir(serial))
print(inspect.getsourcefile(serial))
import shutil # For file copy of xex file
import configparser  # For Parsing INI file used currently for Base games path setting and persistance.


#Global Variables
##############################################
APP_PATH = os.path.dirname(os.path.abspath(__file__))
window = tk.Tk() # Define this early as other tk elements defined after

#Global to help build key maps by reading X Y on debugs
click_buffer = []
#######################
#Preset system Variables
#######################
PRESET_COUNT = 6

preset_buttons = []
preset_data = []
preset_images = []   # IMPORTANT: keep PhotoImage refs alive

#More Globals

final_file = "final.txt"  # File to store final output

text_box = None
serial_box = None
canvas = None

# ==============================
# DASHBOARD LAYOUT SYSTEM
# ==============================

UI = {
    "header": {"x": 55, "y": 10},

    "main_buttons": {"x": 10, "y": 230},       #Generate, Browse, Copy, Mount, Auto Launch
    "secondary_buttons": {"x": 10, "y":300},    #Good , bad, database
    "utility_buttons": {"x": 430, "y": 300},     #Control

    "result_area": {"x": 30, "y": 260},           #Filename Text
    
    "image_panel": {"x": 100, "y": 300},

    "bottom_controls": {"x": 10, "y": 600},
     #"footer": {"x": 10, "y": 880}
}

CTRL_UI = {
    "status_area": {"x": 190, "y": 605},          #TEXTBOX    , Key cap, string send, control
}

#Function helper for placing objects
def place(widget, key, dx=0, dy=0, width=None):
    cfg = UI[key]
    widget.place(
        x=cfg["x"] + dx,
        y=cfg["y"] + dy,
        width=width
    )

files = []  # List to hold all matching files

key_queue = queue.Queue()       # Queue for managing keypresses

#State of modifiers
ctrl_down = False
shift_down = False
alt_down = False
is_hold_mode = False
#key hold state for control map
held_keys = {}

# Last key press time dictionary to debounce key presses
last_key_time = {}

########################
#Load variables from INI
########################

#File to use for config
config_file = "Vgar-config.ini"

# Load configuration
config = configparser.ConfigParser()
config.read(config_file)

# Read the file path
Atari_Files = config.get("Settings", "Atari_Files", fallback="D:\\test\\AtariGames\\")
print(f"Loaded file path: {Atari_Files}")

#read the other stuff

db_location = config.get("Settings", "db_location", fallback="D:\\test\\dbold.json\\")
db = TinyDB(db_location) #Database file path
print(f"Loaded db location: {db_location}")
DEBOUNCE_INTERVAL = config.getfloat("Settings", "debounce_interval", fallback=0.05)
print(f"Loaded debounce: {DEBOUNCE_INTERVAL}")
RespeQT_path= config.get("Settings", "respecqt_path", fallback = "D:\\TEST\\RespeQt5.4rc4\\respeqt.exe")
print(f"Loaded RespecQT Path: {RespeQT_path}")
session_path = config.get("Settings", "session_path", fallback = "D:\\TEST\\Random_Atari_Game.respeqt")
print(f"Loaded RespecQT Session Path: {session_path}")
game_placeholder_image=config.get("Settings", "placeholder_image", fallback = os.path.join(APP_PATH, "placeholder.png"))
vgar_start_sound=config.get("Settings", "vgar_start_sound", fallback = os.path.join(APP_PATH, "vgar-start.wav"))
vgar_load_sound=config.get("Settings", "vgar_load_sound", fallback = os.path.join(APP_PATH, "cload.wav"))

com_port = config.get("Settings", "com_port", fallback = "COM1")
baud = config.getint("Settings", "baud", fallback = 9600)

xexload_delay = config.getint("Settings", "xload_delay", fallback = 15)


session_path = config.get("Settings", "session_path", fallback = "D:\\TEST\\Random_Atari_Game.respeqt")
session_path = config.get("Settings", "session_path", fallback = "D:\\TEST\\Random_Atari_Game.respeqt")

###########################################################################################


#generation animation stuff
animation_count = 0
animation_cycles = 0

#Initialise some values here
ser = None # Reset serial variable
session = requests.Session()
pre_loaded_filenames = []
final_filename = ""
runonce=0
testname =""
xexload=0

result_frame = tk.Frame(window, bd=2, relief=tk.SOLID, bg="black", width=500)  # Proper initialization

# Label for result text
lbl_result = tk.Label(
    result_frame,
    text="File?",   #Not sure we want text here now
    font=("Helvetica", 18),
    fg="blue",
    bg="white",
    anchor="center",
    borderwidth=1,
    relief=tk.SOLID
)

# Initialize Pygame mixer for sound effects
pygame.mixer.init()


#########################################


# Create the main GUI window
window.title("VGAR - pre beta")
window.configure(background='black')

pygame.mixer.music.load("vgar-start.wav")  # Startup sound



#Preset read
if not config.has_section("Presets"):
    config.add_section("Presets")

    for i in range(PRESET_COUNT):
        config.set("Presets", f"slot_{i}", "")
        config.set("Presets", f"label_{i}", "")

    with open(config_file, "w") as configfile:
        config.write(configfile)

#Preset loader
def load_presets():
    global preset_data

    preset_data = []

    for i in range(PRESET_COUNT):

        game_path = config.get("Presets", f"slot_{i}", fallback="")
        label = config.get("Presets", f"label_{i}", fallback="")

        preset_data.append({
            "path": game_path,
            "label": label
        })
        
def save_preset(slot, game_path, label=""):

    config.set("Presets", f"slot_{slot}", game_path)
    config.set("Presets", f"label_{slot}", label)

    with open(config_file, "w") as configfile:
        config.write(configfile)

    load_presets()
    refresh_preset_buttons()

def get_game_image_path(filename):

    global game_placeholder_image

    if not filename:
        return game_placeholder_image

    # NORMALISE PATH
    filename = os.path.normpath(filename)

    directory = os.path.dirname(filename)

    base_name = os.path.splitext(
        os.path.basename(filename)
    )[0]

    print("LOOKING FOR IMAGE:")
    print("DIR:", directory)
    print("BASE:", base_name)

    extensions = [".png", ".jpg", ".bmp"]

    for ext in extensions:

        candidate = os.path.join(
            directory,
            base_name + ext
        )

        print("TRY:", candidate)

        if os.path.exists(candidate):

            print("FOUND IMAGE:", candidate)

            return candidate

    print("USING PLACEHOLDER")
    print("FOUND IMAGE:", candidate)
    return game_placeholder_image

def preset_clicked(slot):

    global final_filename

    # CTRL held = PROGRAM SLOT
    if ctrl_is_down():

        if not final_filename:
            messagebox.showerror("Error", "No game currently loaded")
            return

        save_preset(slot, final_filename)

        pygame.mixer.music.load("good.mp3")
        pygame.mixer.music.play()

        print(f"Preset {slot} programmed")

        return

    # NORMAL CLICK = LOAD SLOT
    preset = preset_data[slot]

    if not preset["path"]:
        return

    final_filename = preset["path"]

    lbl_result.config(
        text=os.path.basename(final_filename),
        font=("Helvetica", 14),
        fg="blue",
        bg="white"
    )

    show_game_image(game_image_label, final_filename)

    pygame.mixer.music.load("cload.wav")
    pygame.mixer.music.play()

    print(f"Loaded preset {slot}")


def refresh_preset_buttons():

    global preset_images

    preset_images.clear()

    for i, btn in enumerate(preset_buttons):

        preset = preset_data[i]

        image_path = get_game_image_path(preset["path"])

        try:
            img = Image.open(image_path)
        except Exception as e:
              print("IMAGE LOAD FAILED:", e)
              img = Image.open(game_placeholder_image)

        img = img.resize((80, 60), Image.Resampling.LANCZOS)

        photo = ImageTk.PhotoImage(img)

        preset_images.append(photo)

        # TEXT OVERRIDE?
        if preset["label"]:

            btn.config(
                image=photo,
                text=preset["label"],
                compound="center",
                font=("Helvetica", 8, "bold"),
                fg="white",
                bg="black"
            )

        else:

            btn.config(
                image=photo,
                text=""
            )
            btn.image = photo

# Replace your ENTIRE get_game_image_path() function with this version.

def get_game_image_path(filename):

    global game_placeholder_image

    if not filename:
        return game_placeholder_image

    filename = os.path.normpath(filename)

    directory = os.path.dirname(filename)
    base_name = os.path.splitext(os.path.basename(filename))[0]

    if not os.path.exists(directory):
        return game_placeholder_image

    for file in os.listdir(directory):
        name, ext = os.path.splitext(file)

        if ext.lower() in [".png", ".jpg", ".jpeg", ".bmp"]:
            if name.lower() == base_name.lower():
                return os.path.join(directory, file)

    return game_placeholder_image

def delete_selected_game(listbox, refresh_callback):
    selection = listbox.curselection()

    if not selection:
        messagebox.showerror("Error", "No game selected")
        return

    game_path = listbox.get(selection[0])

    # confirm delete
    confirm = messagebox.askyesno(
        "Delete Entry",
        f"Delete this entry?\n\n{game_path}"
    )

    if not confirm:
        return

    # remove from TinyDB
    QueryObj = Query()
    db.remove(QueryObj.Game == game_path)

    print("Deleted from DB:", game_path)

    # refresh UI
    refresh_callback()

#pygame.mixer.music.play()
pygame.mixer.music.play()

# Define logo size
LOGO_WIDTH = 400
LOGO_HEIGHT = 150

# Add a logo and heading
header_frame = tk.Frame(window)  # Frame for the logo and heading
place(header_frame, "header")

original_logo_image = Image.open("vgar.png")
resized_logo_image = original_logo_image.resize((LOGO_WIDTH, LOGO_HEIGHT))
logo_image = ImageTk.PhotoImage(resized_logo_image)  # Convert to PhotoImage for Tkinter
logo_label = tk.Label(header_frame, image=logo_image)  # Display the resized logo
logo_label.pack()

# Heading text under the logo
heading_label = tk.Label(
    header_frame,
    text="(Very Good Atari Remote)",
    font=("Helvetica", 24, "bold"),
    #fg="dimgray",
    fg="black",
)
heading_label.pack()



#MAIN FUNCTIONS
###########################################################

def open_serial():
    global ser
    global baud
    global com_port
    global timeout

    try:
        
        print("Using Serial Method")

        if 'ser' in globals() and ser and ser.is_open:
            print("Serial already open")
            return
        
        ser = serial.Serial(com_port, baud, timeout=1)
        time.sleep(2)
       
    except Exception as e:
        print(f"Serial error: {e}")
        messagebox.showerror("Error", "Could not open COM port for AKI USB HID Comms")

def Change_Atari_Path():
# Update the file path and save
    global Atari_Files
    new_path = filedialog.askdirectory(title="Select a folder")
    #new_path = "C:/New/Path/game.xex"
    config.set("Settings", "atari_files", new_path)

    with open(config_file, "w") as configfile:
        config.write(configfile)
    Atari_Files = new_path
    print(f"Updated file path to: {new_path}")


def start_atari():
    response = requests.get("http://192.168.168.181:5000/start_game")


def stop_atari():
    response = requests.get("http://192.168.168.181:5000/stop_game")


#These are functions for Atari special keys, mapped from AKI function key presses.
#Code includes key release at python level currently (allows control hold duration in python)
#Atari Function keys - F1 = Help, F2= Start, F3= Select, F4 = Option, F5= Reset
#           "F1": 0x3a, "F2": 0x3b, "F3": 0x3c, "F4": 0x3d,"F5": 0x3e


#Press Atari special keys

def send_reset():
    print("Using Serial Method - reset")
    ser.write(bytes([0x00,0x3e]))
    time.sleep(0.1)
    ser.write(bytes([0x00,0x00]))
         
def send_option():
    print("Using Serial Method - option")
    ser.write(bytes([0x00,0x3d]))
    time.sleep(0.1)
    ser.write(bytes([0x00,0x00]))

def send_select():
    print("Using Serial Method - select")
    ser.write(bytes([0x00,0x3c]))
    time.sleep(0.1)
    ser.write(bytes([0x00,0x00]))    

def send_start():
    print("Using Serial Method - start")
    ser.write(bytes([0x00,0x3b]))
    time.sleep(0.1)
    ser.write(bytes([0x00,0x00]))

def send_help():
    print("Using Serial Method - help")
    ser.write(bytes([0x00,0x3a]))
    time.sleep(0.1)
    ser.write(bytes([0x00,0x00]))

#Hold Atari special keys

def send_reset_hold():

    ser.write(bytes([0x00,0x3e]))
    time.sleep(0.2)
    
def send_reset_release():
    ser.write(bytes([0x00,0x00]))

def send_help_hold():
    ser.write(bytes([0x00,0x3a]))
    time.sleep(0.2)
      
def send_help_release():
    ser.write(bytes([0x00,0x00]))

def send_start_hold():
    ser.write(bytes([0x00,0x3b]))
    time.sleep(0.2)
    
def send_start_release():
    ser.write(bytes([0x00,0x3b]))
    time.sleep(0.2)
        
def send_option_hold():
    ser.write(bytes([0x00,0x3d]))
    time.sleep(0.2)
    
def send_option_release():
    ser.write(bytes([0x00,0x00]))

def send_select_hold():
    ser.write(bytes([0x00,0x3c]))
    time.sleep(0.2)
    
def send_select_release():
    ser.write(bytes([0x00,0x00]))



def send_esc():
    print("Using Serial Method - Esc")
    ser.write(bytes([0x00,0x29]))
    time.sleep(0.1)
    ser.write(bytes([0x00,0x00]))

def send_tab():
    print("Using Serial Method - Tab")
    ser.write(bytes([0x00, 0x2B]))
    time.sleep(0.2)
    ser.write(bytes([0x00, 0x00]))

def send_control():
    print("Using Serial Method - CTRL")
    ser.write(bytes([0x01,0x00]))   #0x01 or 0x10 for rctrl
    time.sleep(0.1)
    ser.write(bytes([0x00,0x00]))

def send_shift():
    print("Using Serial Method - Shift")
    ser.write(bytes([0x00,0x3a]))
    time.sleep(0.1)
    ser.write(bytes([0x00,0x00]))

def send_backspace():
    print("Using Serial Method - backspace")
    ser.write(bytes([0x00,0x2a]))
    time.sleep(0.1)
    ser.write(bytes([0x00,0x00]))

def send_enter():
    print("Using Serial Method - enter")
    ser.write(bytes([0x00,0x28]))
    time.sleep(0.1)
    ser.write(bytes([0x00,0x00]))

def send_caps():
    print("Using Serial Method - caps")
    ser.write(bytes([0x00,0x39]))
    time.sleep(0.2)
    ser.write(bytes([0x00,0x00]))

def send_break():
    print("Using Serial Method - break")
    ser.write(bytes([0x00,0x3a]))
    time.sleep(0.1)
    ser.write(bytes([0x00,0x00]))

def send_space():
    print("Using Serial Method - caps")
    ser.write(bytes([0x00,0x2C]))
    time.sleep(0.1)
    ser.write(bytes([0x00,0x00]))

    
def atari_string_send():

    global text_box

    # widget destroyed?
    if not text_box.winfo_exists():
        print("Text box no longer exists")
        return

    Atari_string = text_box.get("1.0", tk.END).strip()

    print("Using Serial Method - string send")

    for char in Atari_string:
        send_key_to_atari(char)
        
def send_key_to_atari(key, modifier=0x00):
    try:
        if not ser:
            print("Serial not initialised")
            messagebox.showerror("Error", "Serial not initialised")
            return

        print("Using Protocol Send")

        
        SHIFT = 0x02

        SHIFT_REQUIRED = {
            '!', '"', '#', '$', '%', '&', "'",
            '(', ')', '*', '+',
            '<', '>', '?', ':',
            '{', '}', '|', '~','@'
}

        # =========================
        # F-KEYS
        # =========================
        F_KEY_HID_MAP = {
            "F1": 0x3a, "F2": 0x3b, "F3": 0x3c, "F4": 0x3d,
            "F5": 0x3e, "F6": 0x3f, "F7": 0x40, "F8": 0x41,
            "F9": 0x42, "F10": 0x43, "F11": 0x44, "F12": 0x45,
            "f1": 0x3a, "f2": 0x3b, "f3": 0x3c, "f4": 0x3d,
            "f5": 0x3e, "f6": 0x3f, "f7": 0x40, "f8": 0x41,
            "f9": 0x42, "f10": 0x43, "f11": 0x44, "f12": 0x45,
        }

        # =========================
        # SPECIAL KEYS
        # =========================
        SPECIAL_KEYS = {
            "enter": 0x28,
            "escape": 0x29,
            "backspace": 0x2A,
            "tab": 0x2B,
            "space": 0x2C,
            "caps lock": 0x39,
            "down": 0x51,
            "left": 0x50,
            "right": 0x4f,
            "up": 0x52,
            "ctrl": 0x01
            
        }

        key_lower = str(key).lower()

        if key_lower in SPECIAL_KEYS:
            code = SPECIAL_KEYS[key_lower]
            print(f"SPECIAL: {key} -> {hex(code)}")
            ser.write(bytes([modifier, code]))
            time.sleep(0.05)
            ser.write(bytes([0x00, 0x00]))
        
            return

        # =========================
        # F-KEYS
        # =========================
        if key in F_KEY_HID_MAP:
            code = F_KEY_HID_MAP[key]
            print(f"FKEY: {key} -> {hex(code)}")

            ser.write(bytes([modifier, code]))
            time.sleep(0.05)
            ser.write(bytes([0x00, 0x00]))
            return

        # =========================
        # ASCII MAP
        # =========================
        ASCII_KEY_HID_MAP = {
            ' ': 0x2C,

            '!': 0x1E, '"': 0x1f, '#': 0x20, '$': 0x21,
            '%': 0x22, '&': 0x24, "'": 0x34,

            '(': 0x26, ')': 0x27, '*': 0x4f, '+': 0x50,
            ',': 0x36, '-': 0x2D, '.': 0x37, '/': 0x38,

            '0': 0x27, '1': 0x1E, '2': 0x1F, '3': 0x20,
            '4': 0x21, '5': 0x22, '6': 0x23, '7': 0x24,
            '8': 0x25, '9': 0x26,

            ':': 0x33, ';': 0x33,
            '<': 0x36, '=': 0x2E, '>': 0x37, '?': 0x38,

            '@': 0x1F,

            'A': 0x04, 'B': 0x05, 'C': 0x06, 'D': 0x07,
            'E': 0x08, 'F': 0x09, 'G': 0x0A,
            'H': 0x0B, 'I': 0x0C, 'J': 0x0D, 'K': 0x0E,
            'L': 0x0F, 'M': 0x10, 'N': 0x11, 'O': 0x12,
            'P': 0x13, 'Q': 0x14, 'R': 0x15, 'S': 0x16,
            'T': 0x17, 'U': 0x18, 'V': 0x19, 'W': 0x1A,
            'X': 0x1B, 'Y': 0x1C, 'Z': 0x1D,

            '[': 0x2F, '\\': 0x31, ']': 0x30,
            '^': 0x23, '_': 0x2D,

            '`': 0x35,

            'a': 0x04, 'b': 0x05, 'c': 0x06, 'd': 0x07,
            'e': 0x08, 'f': 0x09, 'g': 0x0A,
            'h': 0x0B, 'i': 0x0C, 'j': 0x0D, 'k': 0x0E,
            'l': 0x0F, 'm': 0x10, 'n': 0x11, 'o': 0x12,
            'p': 0x13, 'q': 0x14, 'r': 0x15, 's': 0x16,
            't': 0x17, 'u': 0x18, 'v': 0x19, 'w': 0x1A,
            'x': 0x1B, 'y': 0x1C, 'z': 0x1D,

            '{': 0x2F, '|': 0x31, '}': 0x30, '~': 0x35,
        }

        if key in ASCII_KEY_HID_MAP:
            code = ASCII_KEY_HID_MAP[key]

            print(f"ASCII: {key} -> {hex(code)} mod={hex(modifier)}")

            ser.write(bytes([modifier, code]))
            time.sleep(0.05)
            ser.write(bytes([0x00, 0x00]))
        return

        print(f"Unmapped key ignored: {key}")

    except Exception as e:
        print(f"Error sending key '{key}': {e}")

def send_serial():
    global ser
    global serial_box

    print(ser)

    # widget destroyed?
    if serial_box is None or not serial_box.winfo_exists():
        print("Serial box no longer exists")
        return

    serial_code = serial_box.get("1.0", tk.END).strip()

    print("INPUT:", serial_code)

    if not ser:
        print("Serial not initialised")
        messagebox.showerror("Error", "Serial not initialised")
        return

    try:
        # =========================
        # PARSE INPUT (DEC or HEX)
        # =========================
        if serial_code.lower().startswith("0x"):
            value = int(serial_code, 16)
        else:
            value = int(serial_code)

        if value < 0 or value > 255:
            print("Value must be 0–255")
            return

        # =========================
        # BUILD PACKET
        # =========================
        modifier = 0x00  # keep for future CTRL/SHIFT expansion
        packet = bytes([modifier, value])

        ser.write(packet)

        print(f"Sent: mod={hex(modifier)} key={hex(value)}")

        # release (important for HID-style devices)
        time.sleep(0.05)
        ser.write(bytes([0x00, 0x00]))

    except ValueError:
        print("Enter a valid number (e.g. 57 or 0x39)")
    except Exception as e:
        print(f"Serial error: {e}")
            

# Worker function to process the key presses from the queue
def key_worker():
    """
    Worker thread to process key presses in the queue.
    """
    while True:
        key = key_queue.get()

        if key is None:
            break

        modifier = 0x00

        if ctrl_down:
            modifier |= 0x01
        if shift_down:
            modifier |= 0x02
        if alt_down:
            modifier |= 0x04

        send_key_to_atari(key, modifier)

        time.sleep(0.05)

# Function to capture keyboard events and add them to the queue
def realtime_keyboard_capture():
    """
    Captures real-time keyboard input and sends each keypress to the Atari.
    """
    global ctrl_down, shift_down, alt_down

    print("Realtime keyboard capture started. Press ESC to exit.")

    try:
        while True:
            event = keyboard.read_event()

            # =========================
            # KEY DOWN
            # =========================
            if event.event_type == keyboard.KEY_DOWN:

                # -------------------------
                # MODIFIER TRACKING
                # -------------------------
                if event.name in ('ctrl', 'ctrl_l', 'ctrl_r'):
                    ctrl_down = True
                    continue

                if event.name in ('shift', 'shift_l', 'shift_r'):
                    shift_down = True
                    continue

                if event.name in ('alt', 'alt_l', 'alt_r'):
                    alt_down = True
                    continue

                # ESC exit
                if event.name == 'esc':
                    print("Exiting realtime keyboard capture.")
                    break

                # -------------------------
                # DEBOUNCE
                # -------------------------
                current_time = time.time()

                if (event.name not in last_key_time or
                    (current_time - last_key_time[event.name]) > DEBOUNCE_INTERVAL):

                    key_queue.put(event.name)
                    last_key_time[event.name] = current_time

            # =========================
            # KEY UP
            # =========================
            elif event.event_type == keyboard.KEY_UP:

                if event.name in ('ctrl', 'ctrl_l', 'ctrl_r'):
                    ctrl_down = False

                elif event.name in ('shift', 'shift_l', 'shift_r'):
                    shift_down = False

                elif event.name in ('alt', 'alt_l', 'alt_r'):
                    alt_down = False

    except KeyboardInterrupt:
        print("Realtime keyboard capture interrupted by user.")

        
# Function to start the capture and worker threads
def start_realtime_capture():
    """
    Start the keyboard capture and worker in separate threads.
    """
    # Start the worker thread to process the key presses
    worker_thread = threading.Thread(target=key_worker, daemon=True)
    worker_thread.start()

    # Start the keyboard capture in a separate thread
    capture_thread = threading.Thread(target=realtime_keyboard_capture, daemon=True)
    capture_thread.start()

   
######################               

def update_respeqt_file():
    # Path to the file to update
   # respeqt_file_path = "Random_Atari_Game.respeqt"
    global final_filename
    global session_path
    global xexload
    if final_filename.endswith(".xex"):
        session_path = os.path.join(APP_PATH, "DOS_XEX.respeqt")
        shutil.copy(final_filename,os.path.join(APP_PATH, "xex\\VGAR.xex"))
        subprocess.Popen([RespeQT_path, session_path])
        time.sleep(0.2)
        xexload = 1        
    else:
        session_path = os.path.join(APP_PATH, "Random_Atari_Game.respeqt")
    
        # Read the content of the file
        with open(session_path, "r") as file:
            lines = file.readlines()  # Read all lines

        # Find the block that needs to be updated
        section_start = None
        section_end = None

        # Iterate through the lines to find the block boundaries
        for index, line in enumerate(lines):
            # Identify the start of the block
            if line.strip() == "[MountedImageSettings]":
                section_start = index
            # Identify the end of the block
            if section_start is not None and line.startswith("1\\FileName"):
                section_end = index
                break

        if section_start is None or section_end is None:
            raise ValueError("Could not find the [MountedImageSettings] block.")

        # Update the first disk image (1\FileName)
        corrected_path = final_filename.replace("\\", "/")  # Replace \ with /
        lines[section_start + 1] = f"1\\FileName={corrected_path}\n"  # Write with corrected slashes

        # Write the updated content back to the file
        with open(session_path, "w") as file:
            file.writelines(lines)  # Write the modified content
        subprocess.Popen([RespeQT_path, session_path])
        

def auto_launch():
    PROCNAME = "RespeQt.exe"

    for proc in psutil.process_iter():
    # check whether the process name matches
        if proc.name() == PROCNAME:
            proc.kill()
    update_respeqt_file()
    send_reset_hold()
    time.sleep(0.3)
    send_help_hold()
    time.sleep(0.3)
    send_reset_release()
    time.sleep(0.3)
    send_help_release()
   # time.sleep(0.5)    
##needs serial code
    print("Using Serial Method - c")
    ser.write(bytes([0x00,0x6]))
    time.sleep(0.8)
    ser.write(bytes([0x00,0x00]))
    global xexload_delay
    
    if xexload == 1:
        #time to wait before hitting enter to load from dos
        #Add this to INI as Respeqt serial load can be variable on setup / usb cable, handshaking etc.
        time.sleep(xexload_delay)
        print("Using Serial Method - enter")
             
        ser.write(bytes([0x00,0x28]))
        time.sleep(0.2)
        ser.write(bytes([0x00,0x00]))
       
def rate_good():
    pygame.mixer.music.load("good.mp3")  
    pygame.mixer.music.play()

    rating="good"

    db.insert({ 'Game': final_filename,
             'Rating': rating
                         })  

def rate_bad():
    pygame.mixer.music.load("bad.mp3")  # Final sound effect
    pygame.mixer.music.play()

    rating="bad"
  
    db.insert({ 'Game': final_filename,
             'Rating': rating
                         })  
###################################

#Function to load game image
def show_game_image(game_image_label, filename):

    global game_placeholder_image

    # CLEAR PREVIOUS IMAGE FIRST
    game_image_label.config(image="")
    game_image_label.image = None

    image_path = get_game_image_path(filename)

    print("SHOW IMAGE:", image_path)

    try:

        img = Image.open(image_path)

    except Exception as e:

        print("IMAGE LOAD FAILED:", e)

        img = Image.open(game_placeholder_image)

    img = img.resize((300,225), Image.Resampling.LANCZOS)

    photo = ImageTk.PhotoImage(img)

    game_image_label.config(image=photo, relief="raised")
    game_image_label.image = photo
   

# Function to start the animation and display the final filename
def generate_random_filename():
    global animation_count, animation_cycles

    pygame.mixer.music.load("beep.mp3")

    animation_cycles = random.randint(10, 50)
    animation_count = 0

    animate_filename()

def animate_filename():
    global animation_count, animation_cycles, final_filename

    if animation_count < animation_cycles:
        pygame.mixer.music.play()
        
        filename = random.choice(pre_loaded_filenames)
        show_game_image(game_image_label, filename)
        lbl_result.config(text=os.path.basename(filename))

        animation_count += 1
        #Control the speed of the filename cycling with this number - 50 was too fast, so went to 150
        #however went back to 50 and changed for sound every 3 files may be better
        #  window.after(100, animate_filename)
        #now removed that linier animation with delay at end
        delay = 40 + (animation_count * 3)
        window.after(delay, animate_filename)

    else:
   
        unused_filenames = [f for f in pre_loaded_filenames if not db.search(Query().Game == f)]

        if not unused_filenames:
            lbl_result.config(text="No unused filenames left!", font=("Helvetica", 14), fg="red", bg="white")
            return

        final_filename = choice(unused_filenames)
        show_game_image(game_image_label, final_filename)
        lbl_result.config(text=os.path.basename(final_filename), font=("Helvetica", 14), fg="blue", bg="white")

        with open(final_file, "w") as file:
            file.write(final_filename + "\n")

        pygame.mixer.music.load("tada.mp3")
        if animation_count % 3 ==0:
            pygame.mixer.music.play()

        print(final_filename)

        pygame.mixer.music.load("cload.wav")  # CLOAD SOUND
        pygame.mixer.music.play()   


def browse_filename():
    global lbl_result
    global final_filename
    final_filename = filedialog.askopenfilename(title="Select a file")
    show_game_image(game_image_label, final_filename)

    #lbl_result.config(text="", bg="white" )
    #lbl_result.config(text=os.path.basename(final_filename), font=("Helvetica", 14), fg="blue", bg="white")
    lbl_result.config(
        text=os.path.basename(final_filename),
        font=("Helvetica", 14),
        fg="blue",
        bg="white",
        anchor="center",
        justify="center"
    )
    pygame.mixer.music.load("cload.wav")  # CLOAD SOUND
    pygame.mixer.music.play()   

# Function to copy to clipboard
def copy_to_clipboard():
    global final_filename
    pyperclip.copy(final_filename)  # Copy the final filename to the clipboard
        
def ctrl_is_down():
    return keyboard.is_pressed('ctrl')

def release_all_keys():
    global held_keys

    print("RELEASING ALL HELD KEYS")

    for name, data in list(held_keys.items()):
        if "release" in data["key"]:
            data["key"]["release"]()

        try:
            if canvas is not None and canvas.winfo_exists():
                canvas.delete(data["rect"])
        except Exception as e:
            print("DELETE FAILED:", e)

    held_keys.clear()


#######release keys helper
def clear_held_key(name):
    if name in held_keys:
        data = held_keys[name]

        if "release" in data["key"]:
            data["key"]["release"]()

        try:
            if canvas is not None and canvas.winfo_exists():
                canvas.delete(data["rect"])
        except:
            pass

        del held_keys[name]

#######
def release_key(name):
    if name in held_keys:
        try:
            if canvas is not None and canvas.winfo_exists():
                canvas.delete(data["rect"])
                canvas.delete(held_keys[name]["rect"])
        except:
            pass

        held_keys[name]["key"]["release"]()

        del held_keys[name]
        
#Function to launch Atari control
def on_atari_click(event, canvas):
    global click_buffer
    global is_hold_mode
    x, y = event.x, event.y
    #old line to print coordinates to console
    #print(f"Clicked at: {x}, {y}")

    #keymap builder code
    
    click_buffer.append((x, y))

    if len(click_buffer) == 1:
        print(f"Top-left: {click_buffer[0]}")

    elif len(click_buffer) == 2:
        (x1, y1), (x2, y2) = click_buffer

        # Normalise in case clicks aren't perfectly ordered
        x1, x2 = sorted([x1, x2])
        y1, y2 = sorted([y1, y2])

        print(
            f'{{"name": "X", "x1": {x1}, "y1": {y1}, "x2": {x2}, "y2": {y2}, '
            f'"action": lambda: send_key_to_atari("x")}},'
        )
        click_buffer.clear()
    
#Atari Control Key Zones
    key_zones = [

        {"name": "RESET", "x1": 714, "y1": 267, "x2": 751, "y2": 312,
         "press": send_reset, "hold": send_reset_hold, "release": send_reset_release},

        {"name": "OPTION", "x1": 716, "y1": 321, "x2": 750, "y2": 370,
         "press": send_option, "hold": send_option_hold, "release": send_option_release},

        {"name": "SELECT", "x1": 715, "y1": 373, "x2": 751, "y2": 422,
         "press": send_select, "hold": send_select_hold, "release": send_select_release},

        {"name": "START", "x1": 714, "y1": 429, "x2": 749, "y2": 475,
         "press": send_start, "hold": send_start_hold, "release": send_start_release},

        {"name": "HELP", "x1": 716, "y1": 480, "x2": 750, "y2": 532,
         "press": send_help, "hold": send_help, "release": send_help_release},

        {"name": "A", "x1": 133, "y1": 385, "x2": 154, "y2": 417,
         "press": lambda: send_key_to_atari("a"),
         "hold": lambda: send_key_to_atari("a"),
         "release": lambda: None},

        {"name": "B", "x1": 320, "y1": 435, "x2": 341, "y2": 468,
         "press": lambda: send_key_to_atari("b"),
         "hold": lambda: send_key_to_atari("b"),
         "release": lambda: None},

        {"name": "C", "x1": 237, "y1": 438, "x2": 259, "y2": 468,
         "press": lambda: send_key_to_atari("C"),
         "hold": lambda: send_key_to_atari("C"),
         "release": lambda: None},

        {"name": "D", "x1": 215, "y1": 382, "x2": 239, "y2": 416,
         "press": lambda: send_key_to_atari("D"),
         "hold": lambda: send_key_to_atari("D"),
         "release": lambda: None},

        {"name": "E", "x1": 207, "y1": 329, "x2": 228, "y2": 363,
         "press": lambda: send_key_to_atari("E"),
         "hold": lambda: send_key_to_atari("E"),
         "release": lambda: None},

        {"name": "F", "x1": 257, "y1": 381, "x2": 279, "y2": 414,
         "press": lambda: send_key_to_atari("F"),
         "hold": lambda: send_key_to_atari("F"),
         "release": lambda: None},

        {"name": "G", "x1": 296, "y1": 379, "x2": 321, "y2": 414,
         "press": lambda: send_key_to_atari("G"),
         "hold": lambda: send_key_to_atari("G"),
         "release": lambda: None},

        {"name": "H", "x1": 340, "y1": 379, "x2": 362, "y2": 416,
         "press": lambda: send_key_to_atari("H"),
         "hold": lambda: send_key_to_atari("H"),
         "release": lambda: None},

        {"name": "I", "x1": 412, "y1": 326, "x2": 435, "y2": 361,
         "press": lambda: send_key_to_atari("I"),
         "hold": lambda: send_key_to_atari("I"),
         "release": lambda: None},

        {"name": "J", "x1": 382, "y1": 382, "x2": 403, "y2": 417,
         "press": lambda: send_key_to_atari("J"),
         "hold": lambda: send_key_to_atari("J"),
         "release": lambda: None},

        {"name": "K", "x1": 423, "y1": 378, "x2": 446, "y2": 415,
         "press": lambda: send_key_to_atari("K"),
         "hold": lambda: send_key_to_atari("K"),
         "release": lambda: None},

        {"name": "L", "x1": 464, "y1": 377, "x2": 487, "y2": 414,
         "press": lambda: send_key_to_atari("L"),
         "hold": lambda: send_key_to_atari("L"),
         "release": lambda: None},

        {"name": "M", "x1": 404, "y1": 434, "x2": 427, "y2": 470,
         "press": lambda: send_key_to_atari("M"),
         "hold": lambda: send_key_to_atari("M"),
         "release": lambda: None},

        {"name": "N", "x1": 360, "y1": 434, "x2": 384, "y2": 468,
         "press": lambda: send_key_to_atari("N"),
         "hold": lambda: send_key_to_atari("N"),
         "release": lambda: None},

        {"name": "O", "x1": 453, "y1": 327, "x2": 477, "y2": 363,
         "press": lambda: send_key_to_atari("O"),
         "hold": lambda: send_key_to_atari("O"),
         "release": lambda: None},

        {"name": "P", "x1": 494, "y1": 324, "x2": 518, "y2": 360,
         "press": lambda: send_key_to_atari("P"),
         "hold": lambda: send_key_to_atari("P"),
         "release": lambda: None},

        {"name": "Q", "x1": 121, "y1": 330, "x2": 144, "y2": 366,
         "press": lambda: send_key_to_atari("Q"),
         "hold": lambda: send_key_to_atari("Q"),
         "release": lambda: None},

        {"name": "R", "x1": 247, "y1": 328, "x2": 270, "y2": 363,
         "press": lambda: send_key_to_atari("R"),
         "hold": lambda: send_key_to_atari("R"),
         "release": lambda: None},

        {"name": "S", "x1": 174, "y1": 382, "x2": 197, "y2": 416,
         "press": lambda: send_key_to_atari("S"),
         "hold": lambda: send_key_to_atari("S"),
         "release": lambda: None},

        {"name": "T", "x1": 288, "y1": 327, "x2": 311, "y2": 363,
         "press": lambda: send_key_to_atari("T"),
         "hold": lambda: send_key_to_atari("T"),
         "release": lambda: None},

        {"name": "U", "x1": 370, "y1": 326, "x2": 393, "y2": 360,
         "press": lambda: send_key_to_atari("U"),
         "hold": lambda: send_key_to_atari("U"),
         "release": lambda: None},

        {"name": "V", "x1": 278, "y1": 434, "x2": 302, "y2": 466,
         "press": lambda: send_key_to_atari("V"),
         "hold": lambda: send_key_to_atari("V"),
         "release": lambda: None},

        {"name": "W", "x1": 163, "y1": 329, "x2": 186, "y2": 360,
         "press": lambda: send_key_to_atari("W"),
         "hold": lambda: send_key_to_atari("W"),
         "release": lambda: None},

        {"name": "X", "x1": 198, "y1": 435, "x2": 221, "y2": 468,
         "press": lambda: send_key_to_atari("X"),
         "hold": lambda: send_key_to_atari("X"),
         "release": lambda: None},

        {"name": "Y", "x1": 329, "y1": 326, "x2": 352, "y2": 364,
         "press": lambda: send_key_to_atari("Y"),
         "hold": lambda: send_key_to_atari("Y"),
         "release": lambda: None},

        {"name": "Z", "x1": 154, "y1": 437, "x2": 176, "y2": 470,
         "press": lambda: send_key_to_atari("Z"),
         "hold": lambda: send_key_to_atari("Z"),
         "release": lambda: None},

        {"name": "1", "x1": 98, "y1": 279, "x2": 123, "y2": 310,
         "press": lambda: send_key_to_atari("1"),
         "hold": lambda: send_key_to_atari("1"),
         "release": lambda: None},

        {"name": "2", "x1": 142, "y1": 277, "x2": 166, "y2": 309,
         "press": lambda: send_key_to_atari("2"),
         "hold": lambda: send_key_to_atari("2"),
         "release": lambda: None},

        {"name": "3", "x1": 183, "y1": 274, "x2": 207, "y2": 308,
         "press": lambda: send_key_to_atari("3"),
         "hold": lambda: send_key_to_atari("3"),
         "release": lambda: None},

        {"name": "4", "x1": 225, "y1": 271, "x2": 250, "y2": 307,
         "press": lambda: send_key_to_atari("4"),
         "hold": lambda: send_key_to_atari("4"),
         "release": lambda: None},

        {"name": "5", "x1": 265, "y1": 272, "x2": 288, "y2": 305,
         "press": lambda: send_key_to_atari("5"),
         "hold": lambda: send_key_to_atari("5"),
         "release": lambda: None},

        {"name": "6", "x1": 311, "y1": 272, "x2": 332, "y2": 307,
         "press": lambda: send_key_to_atari("6"),
         "hold": lambda: send_key_to_atari("6"),
         "release": lambda: None},

        {"name": "7", "x1": 353, "y1": 269, "x2": 373, "y2": 307,
         "press": lambda: send_key_to_atari("7"),
         "hold": lambda: send_key_to_atari("7"),
         "release": lambda: None},

        {"name": "8", "x1": 390, "y1": 272, "x2": 412, "y2": 306,
         "press": lambda: send_key_to_atari("8"),
         "hold": lambda: send_key_to_atari("8"),
         "release": lambda: None},

        {"name": "9", "x1": 431, "y1": 270, "x2": 454, "y2": 305,
         "press": lambda: send_key_to_atari("9"),
         "hold": lambda: send_key_to_atari("9"),
         "release": lambda: None},

        {"name": "0", "x1": 475, "y1": 269, "x2": 496, "y2": 305,
         "press": lambda: send_key_to_atari("0"),
         "hold": lambda: send_key_to_atari("0"),
         "release": lambda: None},

        {"name": "Esc", "x1": 50, "y1": 276, "x2": 82, "y2": 309,
         "press": send_esc, "hold": send_esc, "release": lambda: None},

        {"name": "Tab", "x1": 47, "y1": 329, "x2": 111, "y2": 364,
         "press": send_tab, "hold": send_tab, "release": lambda: None},

        {"name": "CTRL", "x1": 48, "y1": 382, "x2": 112, "y2": 415,
         "press": send_control, "hold": send_control, "release": lambda: None},

        {"name": "L-Shift", "x1": 47, "y1": 442, "x2": 130, "y2": 473,
         "press": send_shift, "hold": send_shift, "release": lambda: None},

        {"name": "DeleteBS", "x1": 597, "y1": 270, "x2": 619, "y2": 303,
         "press": send_backspace, "hold": send_backspace, "release": lambda: None},

        {"name": "Enter", "x1": 619, "y1": 328, "x2": 658, "y2": 355,
         "press": send_enter, "hold": send_enter, "release": lambda: None},

        {"name": "CAPS", "x1": 629, "y1": 380, "x2": 663, "y2": 418,
         "press": lambda: send_key_to_atari("caps lock"),
         "hold": lambda: send_key_to_atari("caps lock"),
         "release": lambda: None},

        {"name": "Break", "x1": 640, "y1": 271, "x2": 664, "y2": 303,
         "press": send_break, "hold": send_break, "release": lambda: None},

        {"name": "R-Shift", "x1": 568, "y1": 432, "x2": 620, "y2": 471,
         "press": send_shift, "hold": send_shift, "release": lambda: None},

        {"name": "Space", "x1": 174, "y1": 492, "x2": 527, "y2": 523,
         "press": send_space, "hold": send_space, "release": lambda: None},

        {"name": "Clear", "x1": 514, "y1": 270, "x2": 538, "y2": 302,
         "press": lambda: send_key_to_atari("<"), "hold": lambda: send_key_to_atari("<"), "release": lambda: None},

        {"name": "Insert", "x1": 555, "y1": 271, "x2": 579, "y2": 305,
         "press": lambda: send_key_to_atari(">"), "hold": lambda: send_key_to_atari(">"), "release": lambda: None},

        {"name": "-", "x1": 536, "y1": 326, "x2": 561, "y2": 359,
         "press": lambda: send_key_to_atari("-"), "hold": lambda: send_key_to_atari("-"), "release": lambda: None},

        {"name": "=", "x1": 579, "y1": 322, "x2": 601, "y2": 359,
         "press": lambda: send_key_to_atari("="), "hold": lambda: send_key_to_atari("="), "release": lambda: None},

        {"name": "+", "x1": 547, "y1": 380, "x2": 567, "y2": 409,
         "press": lambda: send_key_to_atari("+"), "hold": lambda: send_key_to_atari("+"), "release": lambda: None},

        {"name": "*", "x1": 590, "y1": 378, "x2": 613, "y2": 412,
         "press": lambda: send_key_to_atari("*"), "hold": lambda: send_key_to_atari("*"), "release": lambda: None},

        {"name": "Inverse", "x1": 640, "y1": 434, "x2": 666, "y2": 471,
         "press": lambda: None, "hold": lambda: None, "release": lambda: None},

        {"name": ",", "x1": 446, "y1": 436, "x2": 470, "y2": 467,
         "press": lambda: send_key_to_atari(","), "hold": lambda: send_key_to_atari(","), "release": lambda: None},

        {"name": ".", "x1": 485, "y1": 433, "x2": 509, "y2": 468,
         "press": lambda: send_key_to_atari("."), "hold": lambda: send_key_to_atari("."), "release": lambda: None},

        {"name": ";", "x1": 505, "y1": 379, "x2": 528, "y2": 416,
         "press": lambda: send_key_to_atari(";"), "hold": lambda: send_key_to_atari(";"), "release": lambda: None},

        {"name": "/", "x1": 526, "y1": 435, "x2": 551, "y2": 466,
         "press": lambda: send_key_to_atari("/"), "hold": lambda: send_key_to_atari("/"), "release": lambda: None},


    ]

    for key in key_zones:
        if key["x1"] <= x <= key["x2"] and key["y1"] <= y <= key["y2"]:

            print(f"{key['name']} pressed")

            is_hold_mode = ctrl_is_down()

            def run_action(current_key, is_hold_mode):
                name = current_key["name"]

                print("HOLD MODE =", is_hold_mode)

                if is_hold_mode:
                    print(f"HOLD: {name}")

                    if name in held_keys:
                        return

                    rect = canvas.create_rectangle(
                        current_key["x1"], current_key["y1"],
                        current_key["x2"], current_key["y2"],
                        fill="red",
                        stipple="gray25",
                        outline=""
                    )

                    held_keys[name] = {
                        "rect": rect,
                        "key": current_key
                    }

                    current_key["hold"]()

                else:
                    print(f"PRESS: {name}")

                    release_all_keys()

                    rect = canvas.create_rectangle(
                        current_key["x1"], current_key["y1"],
                        current_key["x2"], current_key["y2"],
                        fill="red",
                        stipple="gray50",
                        outline=""
                    )

                    canvas.update()   # 👈 FORCE DRAW BEFORE IT DISAPPEARS

                    current_key["press"]()
                    current_key["release"]()

                    def safe_delete():
                        try:
                            if canvas.winfo_exists():
                                canvas.delete(rect)
                        except:
                            pass

                    canvas.after(80, safe_delete)

            run_action(key, is_hold_mode)

            break   # MUST STOP AFTER FIRST MATCH

  #  run_action(key, is_hold_mode)

def atari_control():

    def place_ctrl(widget, key, dx=0, dy=0, width=None):
        cfg = CTRL_UI[key]
        widget.place(
            x=cfg["x"] + dx,
            y=cfg["y"] + dy,
            width=width
    )

    #this global being removed caused the red on hold keys to incorrectly persist.
    #To fix, I beleive it's a trade off between having potential loss of focus if multiple control windows or complete restructure of canvas....
    # seems ok to keep global now, and button hold colors work - just be aware there may be focus bugs
    # if we open lots of control windows and close again (who would)

    global canvas  #- May have caused loss of focus bug
    ctl_window = tk.Toplevel(window)
    ctl_window.title("Atari-Control")
    ctl_window.geometry("800x690+600+50")
    
    image_path = os.path.join(APP_PATH, "800xl.png")
    image1 = Image.open(image_path)
    image1 = image1.resize((800, 600), Image.Resampling.LANCZOS)
    photo1 = ImageTk.PhotoImage(image1)

    canvas = tk.Canvas(ctl_window, width=800, height=600)
    canvas.pack()

    canvas.create_image(0, 0, anchor="nw", image=photo1)
    canvas.image = photo1  # prevent garbage collection
    canvas.bind("<Button-1>", lambda event: on_atari_click(event, canvas))

    #String box
   
    #Buttons etc.
   
     # NEW LOCAL WIDGETS

    global text_box
    global serial_box
    text_box = tk.Text(ctl_window, height=3, width=40)

    serial_box = tk.Text(ctl_window, height=1, width=6)

    atari_string_send_button_ctl = tk.Button(
        ctl_window,
        text="String Send",
        command=atari_string_send
    )

    serial_send_button_ctl = tk.Button(
        ctl_window,
        text="HID Send",
        command=send_serial
    )

    keyboard_capture_button_ctl = tk.Button(
        ctl_window,
        text="Key Capture",
        command=start_realtime_capture
    )

    # PLACE THEM

    place_ctrl(text_box, "status_area",dx=20,dy=0)
    place_ctrl(atari_string_send_button_ctl, "status_area",dx=350,dy=-3)
    place_ctrl(keyboard_capture_button_ctl, "status_area",dx=350,dy=25)
    place_ctrl(serial_box, "status_area",dx=290,dy=55)
    place_ctrl(serial_send_button_ctl, "status_area",dx=350,dy=55)
    
#In addition to button, bind Atari Control to the Logo image and container clicks

def on_header_click(event):
    atari_control()

logo_label.bind("<Button-1>", on_header_click)
heading_label.bind("<Button-1>", on_header_click)

#function to view database

def launch_procedure(game_path):
    global final_filename
    global lbl_result
    """Function to launch a procedure with the selected game path as a parameter."""
    print("Launching procedure for:", game_path)
    final_filename=game_path
    lbl_result.config(text=os.path.basename(final_filename))
###db image load?
    show_game_image(game_image_label, final_filename)
    pygame.mixer.music.load("cload.wav")  # CLOAD SOUND
    pygame.mixer.music.play()   
    

def create_listbox(parent_frame, games):

    scrollbar = tk.Scrollbar(parent_frame, orient=tk.VERTICAL)

    listbox = tk.Listbox(
        parent_frame,
        yscrollcommand=scrollbar.set,
        font=font.Font(family="Courier", size=10)
    )

    scrollbar.config(command=listbox.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    full_paths = list(games)

    for game in full_paths:
        listbox.insert(tk.END, game)

    def on_double_click(event):
        sel = listbox.curselection()
        if not sel:
            return
        launch_procedure(listbox.get(sel[0]))

    listbox.bind('<Double-Button-1>', on_double_click)

    return listbox

def database_open():
    """Open a Tkinter window to display the formatted database results."""
    dbwindow = tk.Toplevel(window)
    dbwindow.title("Database of ratings")
    dbwindow.geometry("800x580+50+700")

    good_frame = tk.Frame(dbwindow)
    good_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    good_label = tk.Label(good_frame, text="Good Games", font=("Arial", 12, "bold"))
    good_label.pack(pady=5)

    bad_frame = tk.Frame(dbwindow)
    bad_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    bad_label = tk.Label(bad_frame, text="Bad Games", font=("Arial", 12, "bold"))
    bad_label.pack(pady=5)

    todo = Query()
    good_results = db.search(todo.Rating == 'good')
    bad_results = db.search(todo.Rating == 'bad')

  #  create_listbox(good_frame, [entry['Game'] for entry in good_results])
  #  create_listbox(bad_frame, [entry['Game'] for entry in bad_results])
    good_listbox = None
    bad_listbox = None
    good_listbox = create_listbox(good_frame, [e['Game'] for e in good_results])
    bad_listbox = create_listbox(bad_frame, [e['Game'] for e in bad_results])

    def refresh_db():
        dbwindow.destroy()
        database_open()

    delete_good_btn = tk.Button(
        good_frame,
        text="Delete Selected",
        command=lambda: delete_selected_game(good_listbox, refresh_db)
    )

    delete_bad_btn = tk.Button(
        bad_frame,
        text="Delete Selected",
        command=lambda: delete_selected_game(bad_listbox, refresh_db)
    )

    delete_good_btn.pack(pady=5)
    delete_bad_btn.pack(pady=5)


# Function to load the filenames
def load_filenames(num_filenames):
    filenames = []
    try:
        map_directories()
    except:
        print("Path doesn't have Atari files")
        messagebox.showerror("Error", "Path doesn't have Atari Files")
        return # bail out, rest will fail
    
    print(f"Scanning directory: {Atari_Files}")
    print(f"Total files found: {len(files)}")
    for i in range(num_filenames):
        output = get_random_filename()  # Get the output from the script
        filenames.append(output)
  
        window.after(0, lambda: progress.step(100 / num_filenames))

        #time.sleep(0.1)  # Simulate processing time

    global pre_loaded_filenames
    pre_loaded_filenames = filenames

   
#Function to map directories

def map_directories():
    global files
    files = []   # Reset Files
    # Base folder to search for files
    
    atarifolder = Atari_Files
    #We want only random games, and filtering out utilities etc.  We can still load any of this stuff manually if wanted
    badtext = ["demo", "disk", "Disk", "Demos", "demos", "editor", "Editor", "File Creator"]
    # Define the list of extensions to search for
    extensions = [".atr",".xex"]  # Predefined extensions
    #global files 
    
    # Recursively search for files with the given extensions
    for root, dirs, file_names in os.walk(atarifolder):
        # Add full paths of files with the desired extensions to the list
        for file_name in file_names:
            full_path = os.path.join(root, file_name)  # Get full path
            # Check if the full path contains any bad text
            if not any(badt in full_path for badt in badtext):
                # Check if the file has one of the desired extensions
                if any(file_name.lower().endswith(ext) for ext in extensions):
                    files.append(full_path)

    if not files:
        raise ValueError(f"No files with extensions {extensions} found in '{atarifolder}'.")


# Function to run the command script and get a filename
def get_random_filename():

    # Select a random file from the list
    random_file = random.choice(files)  # Randomly choose one file
    return random_file  # Return the full path of the random file


# Function to Load Batch of random games
def Load_Batch():
    
    # Get the selected value from the slider for the number of filenames to load
    if filename_count_slider.get() > 1:
         num_to_generate = filename_count_slider.get()
    else:
         num_to_generate = 100

    # Start loading filenames in a separate thread to keep the GUI responsive
    threading.Thread(target=load_filenames, args=(num_to_generate,)).start()

#####################MAIN Button Setup######################

####################
#Button definitions#
####################

#Start Atari
Atari_button = tk.Button(window, text="Start Atari", command=start_atari)
#Stop Atari
Atari_off_button = tk.Button(window, text="Stop Atari", command=stop_atari)
#Atari Reset
reset_atari_button = tk.Button(window, text="Atari Reset", command=send_reset)
#Atari Reset hold  - STILL DEFINING, BUT COMMENTED OUT AS NOW WORKS IN CONTROL
reset_atari_hold_button = tk.Button(window, text="Atari Reset Hold", command=send_reset_hold)
#Atari Reset release 
reset_atari_release_button = tk.Button(window, text="Atari Reset release", command=send_reset_release)
#Atari string send

#Realtime keyboard
keyboard_capture_button = tk.Button(window, text="Keyboard_Capture", command=start_realtime_capture)
#database
database_button = tk.Button(window, text="Rating DB", command=database_open)
# Button for control
btn_ctrl = tk.Button(window, text="Control", command=atari_control)
#btn_ctrl.place(x=190,y=330)
place(btn_ctrl, "utility_buttons",dx=0)
btn_generate = tk.Button(window, text="Random Filename", command=generate_random_filename)
btn_browse = tk.Button(window, text="Browse Filenames", command=browse_filename)
copy_button = tk.Button(window, text="Copy", command=copy_to_clipboard)
rqt_button = tk.Button(window, text="Mount in RespecQT", command=update_respeqt_file)
auto_button = tk.Button(window, text="Auto Launch", command=auto_launch)
rate_button = tk.Button(window, text="Good", command=rate_good)
rate_button2 = tk.Button(window, text="Bad", command=rate_bad)
btn_Change_Filepath = tk.Button(window, text="Change Path", command=Change_Atari_Path)

# Adjust the window size for the final view
window.geometry("525x700+50+50")

#Main Buttons

place(btn_browse, "main_buttons")
place(btn_generate, "main_buttons", dx=115)
place(copy_button, "main_buttons", dx=230)
place(rqt_button, "main_buttons", dx=275)
place(auto_button, "main_buttons", dx=400)


# Create a frame to draw a box around the results text
place(result_frame, "result_area", width=450)
lbl_result.pack(fill="x")

#Image box
game_image_label = tk.Label(window)
game_image_label.config(relief="raised")# was trying to get a border before it has content, but didnt work - instead load a dummy image.
place(game_image_label, "image_panel")

#Initial image placeholder
img = Image.open(game_placeholder_image)
img = img.resize((300,225), Image.Resampling.LANCZOS)
photo = ImageTk.PhotoImage(img)
game_image_label.config(image=photo, relief="raised")

#Secondary Buttons

place(rate_button,  "secondary_buttons", dx=0,   dy=30)
place(rate_button2, "secondary_buttons", dx=45,  dy=30)
place(database_button, "secondary_buttons", dx=0, dy=0)

# =========================
# PRESET BUTTONS
# =========================

preset_positions = [

    # LEFT SIDE
    (0, 70),
    (0, 125),
    (0, 180),
    
    # RIGHT SIDE
    
    (410, 70),
    (410, 125),
    (410, 180)
]

for i in range(PRESET_COUNT):

    btn = tk.Button(
        window,
        width=60,
        height=40,
        relief=tk.RAISED,
        command=lambda s=i: preset_clicked(s)
    )

    dx, dy = preset_positions[i]

    place(btn, "secondary_buttons", dx=dx, dy=dy)

    preset_buttons.append(btn)


# LEGACY VERSION COMMENT: Add Atari Start button (if using KASA) (Had a smart plug turing atari on also at one point.....
#
#Atari_button.place(x=100,y=290)
#Add Atari Stop button
#Atari_off_button.place(x=170,y=290)
#
#Add Atari Reset button (if using KASA)

#Utility Buttons  - Now commented out as all possible under Atari Control

#place(reset_atari_button, "utility_buttons")
#place(reset_atari_hold_button, "utility_buttons", dx=160)
#place(reset_atari_release_button, "utility_buttons", dx=320)

place(btn_Change_Filepath, "bottom_controls",dx=300,dy=-35)

#Database
#database_button.place(x=100,y=420)

# Button to Load File batches
btn_loadBatch = tk.Button(window, text="Load Batch", command=Load_Batch)

place(btn_loadBatch, "bottom_controls", dx=435,dy=-35)

# Slider to choose the number of filenames to load
filename_count_slider = tk.Scale(
    window,
    from_=1,
    to=100,
    orient=tk.HORIZONTAL,
    length=500,
    tickinterval=10,
    label="Number of Filenames"
)
filename_count_slider.set(100)
#filename_count_slider.place(x=100,y=650)
place(filename_count_slider, "bottom_controls")
slider_instructions =tk.Label(window, text="Number of files in batch:", font=("Arial", 12, "bold"))
place(slider_instructions, "bottom_controls", dy=-40)


# Progressbar for showing progress during filename loading
progress = ttk.Progressbar(window, orient=tk.HORIZONTAL, length=200, mode='determinate')  # Proper initialization
progress.config(maximum=100)
#progress.place(x=100,y=633)
place(progress, "bottom_controls", dy=15,dx=300)

# Call this function to start capturing and processing keyboard events (we don't want it starting automatically, so hashed out normally)  ETC to cancel it
#start_realtime_capture()
        
open_serial()
num_to_generate = 100

# Start the GUI loop
load_presets()
refresh_preset_buttons()
window.after(100, Load_Batch)

window.mainloop()

