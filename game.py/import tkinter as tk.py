import tkinter as tk
import time
import random
import math
from tkinter import messagebox
from PIL import Image, ImageTk
import pygame
from PIL import ImageSequence

# Initialize Pygame mixer for sound effects
pygame.mixer.init()
# Load sound effects
countdown_beep = pygame.mixer.Sound("countdown_beep.wav")
engine_loop = pygame.mixer.Sound("engine_loop.wav")
engine_loop.set_volume(0.2)
win_sound = pygame.mixer.Sound("win_sound.wav")

# Add a sound for coin collection
try:
    coin_collect_sound = pygame.mixer.Sound("coin_collect.wav") # Make sure you have this sound file
    coin_collect_sound.set_volume(0.2)
except pygame.error:
    print("Warning: 'coin_collect.wav' not found. Please ensure the file is in the correct directory.")
    coin_collect_sound = None

# Add cheer sound for end screen
try:
    cheer_sound = pygame.mixer.Sound("cheer.wav")
    cheer_sound.set_volume(1.0)  # Full volume!
except pygame.error:
    print("Warning: 'cheer.wav' not found.")
    cheer_sound = None


# Add the new sound for the "Let's Go!" button
try:
    lets_go_sound = pygame.mixer.Sound("lets_go.wav")
except pygame.error:
    print("Warning: 'lets_go.wav' not found. Please ensure the file is in the correct directory.")
    lets_go_sound = None # Set to None if sound file is not found


# Load voice effects for power zones
try:
    boost_voice = pygame.mixer.Sound("boost_voice.wav")
    boost_voice.set_volume(1.0)
except pygame.error:
    print("Warning: 'boost_voice.wav' not found.")
    boost_voice = None

try:
    slow_voice = pygame.mixer.Sound("slow_voice.wav")
    slow_voice.set_volume(1.0)
except pygame.error:
    print("Warning: 'slow_voice.wav' not found.")
    slow_voice = None


# --- UPDATED: Sounds for impressive messages ---
try:
    good_sound = pygame.mixer.Sound("good_sound.wav") # Create this sound file
    superb_sound = pygame.mixer.Sound("superb_sound.wav") # Create this sound file
    awesome_sound = pygame.mixer.Sound("awesome_sound.wav") # Create this sound file
    IMPRESSIVE_SOUNDS = {
        "good": good_sound,
        "superb": superb_sound,
        "awesome": awesome_sound
    }
except pygame.error as e:
    print(f"Warning: Missing impressive message sound file(s). Error: {e}")
    IMPRESSIVE_SOUNDS = {} # Fallback to empty if sounds are missing


# Constants for game settings
BOOST_DURATION = 3000
SLOW_DURATION = 3000
BOOST_AMOUNT = 3.0
SLOW_AMOUNT = -1.5
GOOD_DURATION = 3000
SUPERB_DURATION = 3000
AWESOME_DURATION = 3000

zone_effect_active = False
zone_effect_end_time = 0
zone_speed_change = 0.0

MAX_SPEED = 15.0
MIN_SPEED = 5.0
MIN_ACTIVE_SPEED = 3.0
CRUISE_SPEED = 0.05
BIKE_WIDTH = 105
BIKE_HEIGHT = 75
UPDATE_INTERVAL = 50
PIXELS_PER_METER = 5

leaderboard = {}
user_name = None
current_level = 1
MAX_LEVEL = 3

# Score variable
score = 0
coins_collected_user = 0
coins_collected_ai = 0

# Impressive messages for coin collection - Now categorized for better control
# These will be explicitly triggered based on coin count, not randomly per coin
IMPRESSIVE_MESSAGES = {
    "good": "Good!",
    "superb": "Superb!",
    "awesome": "Awesome!"
}

# --- UPDATED: Cooldown and last played milestones ---
last_impressive_message_time = 0
IMPRESSIVE_MESSAGE_COOLDOWN = 1.0 # seconds (Reduced for more frequent appearance)
last_good_msg_coin_count = 0
last_superb_msg_coin_count = 0
last_awesome_msg_coin_count = 0


root = tk.Tk()
root.title("🏍 Bike Race: User vs Computer")
root.state('zoomed')
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight() # Corrected here

TRACK_LENGTH = int(screen_width * 2)
TOTAL_DISTANCE = TRACK_LENGTH // PIXELS_PER_METER
canvas_height = int(screen_height * 0.7)

canvas = tk.Canvas(root, width=screen_width, height=canvas_height, bg='white')
canvas.pack()

# Load bike images
bike_user_img = Image.open("bike_blue.png").resize((BIKE_WIDTH, BIKE_HEIGHT), Image.LANCZOS)
bike_user_tk = ImageTk.PhotoImage(bike_user_img)

bike_computer_img = Image.open("bike_red.png").resize((BIKE_WIDTH, BIKE_HEIGHT), Image.LANCZOS)
bike_computer_tk = ImageTk.PhotoImage(bike_computer_img)

# Coin image
coin_img = Image.open("coin.png").resize((30, 30), Image.LANCZOS)  # Ensure you have a coin image
coin_tk = ImageTk.PhotoImage(coin_img)

# Load background images for levels
bg_img1 = ImageTk.PhotoImage(Image.open("bg_level1.jpg").resize((screen_width, canvas_height), Image.LANCZOS))
bg_img2 = ImageTk.PhotoImage(Image.open("bg_level2.jpg").resize((screen_width, canvas_height), Image.LANCZOS))
bg_img3 = ImageTk.PhotoImage(Image.open("bg_level3.jpg").resize((screen_width, canvas_height), Image.LANCZOS))

# Load the new intro background image
intro_bg_img = ImageTk.PhotoImage(Image.open("bike_bg.jpg").resize((screen_width, canvas_height), Image.LANCZOS))
countdown_bg = ImageTk.PhotoImage(Image.open("bike_bg.jpg").resize((screen_width, canvas_height), Image.LANCZOS))
end_bg_img = ImageTk.PhotoImage(Image.open("end_bg.jpg").resize((screen_width, canvas_height), Image.LANCZOS))
popup_bg_img = ImageTk.PhotoImage(Image.open("pop_up.jpg").resize((500, 300), Image.LANCZOS))
popup_bg1_img = ImageTk.PhotoImage(Image.open("pop_up_1.jpg").resize((500, 300), Image.LANCZOS))
popup_bg2_img = ImageTk.PhotoImage(Image.open("pop_up_2.jpg").resize((500, 300), Image.LANCZOS))
popup_name_bg = ImageTk.PhotoImage(Image.open("pop_enter_name.png").resize((500, 300), Image.LANCZOS))


road_width = 250
bike_user_position = 0.0
bike_computer_position = 0.0
bike_user_speed = 0.0
bike_computer_speed = 0.0
start_time = None
game_running = False
paused = False
user_ready = False
computer_ready = False
speed_data = {'User   ': [], 'Computer': []}
time_data = []
frame_count = 0

last_keypress_time = 0
KEYPRESS_TIMEOUT = 500

user_fixed_x = int(screen_width * 0.3)

# List to hold coin positions
coins = []

# Keep track of the maximum x position coins have been generated up to
max_coin_generated_x = 0

def center_y_func(x):
    amplitude = canvas_height // 6
    center = canvas_height // 2
    return center + amplitude * math.sin(2 * math.pi * x / TRACK_LENGTH * 4)

def draw_leaderboard():
    canvas.delete("hud")

    # Panel background
    canvas.create_rectangle(0, canvas_height - 80, screen_width, canvas_height,
                            fill="#222222", outline="", tags="hud")

    # Titles
    canvas.create_text(screen_width // 2, canvas_height - 75,
                        text="📊 Live Stats", font=("Arial", 14, "bold"),
                        fill="white", tags="hud")

    # User stats
    user_speed_text = f"👤 You: {bike_user_speed:.2f} m/s | {bike_user_position * PIXELS_PER_METER:.0f} px"
    canvas.create_text(150, canvas_height - 40,
                        text=user_speed_text, font=("Arial", 12), fill="cyan", tags="hud")

    # Computer stats
    comp_speed_text = f"🤖 AI: {bike_computer_speed:.2f} m/s | {bike_computer_position * PIXELS_PER_METER:.0f} px"
    canvas.create_text(screen_width - 150, canvas_height - 40,
                        text=comp_speed_text, font=("Arial", 12), fill="orange", tags="hud")
        # Coin collection stats
    canvas.create_text(screen_width // 2, canvas_height - 40,
                        text=f"🪙 Coins - You: {coins_collected_user} | AI: {coins_collected_ai}",
                        font=("Arial", 12), fill="gold", tags="hud")



def start_countdown(count=3):

    canvas.create_image(0, 0, anchor="nw", image=countdown_bg)

    if count > 0:
        countdown_beep.play()
        countdown_id = canvas.create_text(screen_width // 2, canvas_height // 2, text=str(count),
                                            font=("Arial", 72, "bold"), fill="cyan", tags="countdown")
        root.after(1000, lambda: (canvas.delete(countdown_id), start_countdown(count - 1)))
    else:
        go_id = canvas.create_text(screen_width // 2, canvas_height // 2, text="GO!",
                                            font=("Arial", 72, "bold"), fill="green", tags="countdown")
        root.after(800, lambda: (canvas.delete(go_id), reset_race()))

def draw_stars():
    canvas.delete("stars")
    for _ in range(50):
        x = random.randint(0, screen_width)
        y = random.randint(0, int(canvas_height * 0.5))
        r = random.choice([1, 2])
        canvas.create_oval(x - r, y - r, x + r, y + r, fill="white", outline="", tags="track")

def generate_coins(from_x=0, to_x=None):
    global coins, max_coin_generated_x
    if to_x is None:
        to_x = TRACK_LENGTH
    new_coins = []
    # Generate 10 coins per segment for a reasonable density
    for _ in range(10):
        x = random.randint(from_x, to_x)
        y = center_y_func(x) + random.randint(-20, 20)  # Randomize y position slightly
        # Ensure coins are within reasonable road bounds (e.g., 50px from top/bottom of road)
        road_center_y = center_y_func(x)
        min_y = road_center_y - road_width // 2 + 25 # 25 for coin radius + small margin
        max_y = road_center_y + road_width // 2 - 25 # 25 for coin radius + small margin
        y = max(min_y, min(max_y, y))

        if 0 <= y <= canvas_height:  # Ensure coins are within the canvas height
            # Avoid generating coins too close to existing ones (50 px gap min)
            too_close = False
            for c_x, c_y in coins:
                if abs(c_x - x) < 50:
                    too_close = True
                    break
            if not too_close:
                new_coins.append((x, y))
    coins.extend(new_coins)
    if to_x > max_coin_generated_x:
        max_coin_generated_x = to_x

def draw_coins(camera_offset):
    canvas.delete("coin")
    for coin in coins:
        x, y = coin
        screen_x = x - camera_offset
        if -50 < screen_x < screen_width + 50:
            canvas.create_image(screen_x, y, anchor='center', image=coin_tk, tags="coin")

def show_specific_impressive_message(message_type):
    global last_impressive_message_time
    
    current_time = time.time()
    if current_time - last_impressive_message_time < IMPRESSIVE_MESSAGE_COOLDOWN:
        return # Too soon to show another message

    message = IMPRESSIVE_MESSAGES.get(message_type)
    sound = IMPRESSIVE_SOUNDS.get(message_type)

    if message and sound:
        message_id = canvas.create_text(user_fixed_x + BIKE_WIDTH // 2, 
                                         center_y_func(bike_user_position * PIXELS_PER_METER) - 100,
                                         text=message, font=("Arial", 24, "bold"), fill="gold", tags="impressive_message")
        
        # Increased duration to 90000 milliseconds (90 seconds or 1.5 minutes)
        root.after(90000, lambda: canvas.delete(message_id)) 
        
        sound.play()
        last_impressive_message_time = current_time # Update the last message time
def check_coin_collection():
    global score, coins_collected_user, coins_collected_ai
    global last_good_msg_coin_count, last_superb_msg_coin_count, last_awesome_msg_coin_count

    camera_offset = bike_user_position * PIXELS_PER_METER - user_fixed_x

    collected_user = []
    collected_ai = []

    # User bike bounding box (adjusted for image anchor 'nw')
    user_bike_screen_x = user_fixed_x
    user_bike_screen_y = center_y_func(bike_user_position * PIXELS_PER_METER) - 20
    user_rect = (user_bike_screen_x, user_bike_screen_y, BIKE_WIDTH, BIKE_HEIGHT)

    # AI bike bounding box (adjusted for image anchor 'nw')
    ai_bike_screen_x = (bike_computer_position * PIXELS_PER_METER) - camera_offset
    ai_bike_screen_y = center_y_func(bike_computer_position * PIXELS_PER_METER) + 20
    ai_rect = (ai_bike_screen_x, ai_bike_screen_y, BIKE_WIDTH, BIKE_HEIGHT)

    # Prepare coin bounding boxes (adjusted for image anchor 'center')
    coin_size = 30 # Coin image is 30x30
    
    current_coins = list(coins) # Iterate over a copy to allow modification
    for coin_world_x, coin_world_y in current_coins:
        coin_screen_x = coin_world_x - camera_offset
        coin_screen_y = coin_world_y # Coin Y position is already screen Y
        coin_rect = (coin_screen_x - coin_size // 2, coin_screen_y - coin_size // 2, coin_size, coin_size)

        if rect_overlap(user_rect, coin_rect):
            collected_user.append((coin_world_x, coin_world_y))
        elif rect_overlap(ai_rect, coin_rect):
            collected_ai.append((coin_world_x, coin_world_y))

    for coin in collected_user:
        if coin in coins: # Ensure coin still exists before removing
            coins.remove(coin)
        coins_collected_user += 1
        score += 10
        if coin_collect_sound:
            coin_collect_sound.play()
        
        # --- NEW: Conditional impressive message triggering based on new thresholds ---
        if coins_collected_user == 10 and last_good_msg_coin_count < 10:
            show_specific_impressive_message("good")
            last_good_msg_coin_count = 10
        elif coins_collected_user == 30 and last_superb_msg_coin_count < 30:
            show_specific_impressive_message("superb")
            last_superb_msg_coin_count = 30
        elif coins_collected_user == 50 and last_awesome_msg_coin_count < 50:
            show_specific_impressive_message("awesome")
            last_awesome_msg_coin_count = 50


    for coin in collected_ai:
        if coin in coins: # Ensure coin still exists before removing
            coins.remove(coin)
        coins_collected_ai += 1
        # Add coin sound for AI collection here
        if coin_collect_sound:
            coin_collect_sound.play() # ADDED THIS LINE

# Helper function for rectangle collision detection
def rect_overlap(rect1, rect2):
    # rect is (x, y, width, height)
    x1, y1, w1, h1 = rect1
    x2, y2, w2, h2 = rect2
    return not (x1 + w1 < x2 or x1 > x2 + w2 or
                y1 + h1 < y2 or y1 > y2 + h2)


def draw_curved_track(camera_offset):
    canvas.delete("track")
    canvas.delete("bg")  # Clear previous background

    # Draw background image based on level
    if current_level == 1:
        canvas.create_image(0, 0, anchor='nw', image=bg_img1, tags="bg")
        road_color = '#666666'
        road_border = '#888888'
        line_color = 'yellow'
    elif current_level == 2:
        canvas.create_image(0, 0, anchor='nw', image=bg_img2, tags="bg")
        road_color = '#884422'
        road_border = '#DD9955'
        line_color = 'white'
    else:
        canvas.create_image(0, 0, anchor='nw', image=bg_img3, tags="bg")
        road_color = '#444466'
        road_border = '#8888AA'
        line_color = '#CCCCFF'
        draw_stars()

    # Show level text
    canvas.create_text(screen_width // 2, 30, text=f"Level: {current_level}",
                        font=("Arial", 20, "bold"), fill="black", tags="track")

    steps = 300
    step_size = TRACK_LENGTH / steps

    # Side road white lines
    for offset in [-road_width // 2, road_width // 2]:
        points = []
        for i in range(steps + 1):
            x = i * step_size - camera_offset
            y = center_y_func(i * step_size) + offset
            if -50 <= x <= screen_width + 50:
                points.append(x)
                points.append(y)
        if points:
            canvas.create_line(points, fill='white', width=5, tags="track")

    # Road body polygon
    upper_edge = []
    lower_edge = []
    for i in range(steps + 1):
        x = i * step_size - camera_offset
        y_upper = center_y_func(i * step_size) - road_width // 2
        y_lower = center_y_func(i * step_size) + road_width // 2
        if -100 <= x <= screen_width + 100:
            upper_edge.append((x, y_upper))
            lower_edge.append((x, y_lower))
    lower_edge.reverse()
    road_points = upper_edge + lower_edge
    if road_points:
        road_coords = []
        for p in road_points:
            road_coords.extend(p)
        canvas.create_polygon(road_coords, fill=road_color, outline=road_border, width=3, tags="track")

    # Center dash line
    dash_length = 15
    gap_length = 15
    total_length = 0
    for i in range(steps):
        x1 = i * step_size - camera_offset
        y1 = center_y_func(i * step_size)
        x2 = (i + 1) * step_size - camera_offset
        y2 = center_y_func((i + 1) * step_size)
        segment_length = math.hypot(x2 - x1, y2 - y1)
        if (total_length // (dash_length + gap_length)) % 2 == 0:
            if -20 <= x1 <= screen_width + 20 or -20 <= x2 <= screen_width + 20:
                canvas.create_line(x1, y1, x2, y2, fill=line_color, width=2, tags="track")
        total_length += segment_length

    # Start and Finish Text
    start_x = 0 - camera_offset
    finish_x = TRACK_LENGTH - camera_offset
    if -100 < start_x < screen_width + 100:
        canvas.create_text(start_x + 30, center_y_func(0) - road_width // 2 - 20,
                            text="Start", font=("Arial", 16, "bold"), fill="white", tags="track")
    if -100 < finish_x < screen_width + 100:
        canvas.create_text(finish_x + 50, center_y_func(TRACK_LENGTH) - road_width // 2 - 20,
                            text="🏁 Finish", font=("Arial", 16, "bold"), fill="white", tags="track")

    # Green and Red Zones
    for i in range(3):
        zone_x = (TRACK_LENGTH // 4) * (i + 1)
        zone_screen_x = zone_x - camera_offset
        zone_y = center_y_func(zone_x)
        if -100 < zone_screen_x < screen_width + 100:
            color = 'lime' if i % 2 == 0 else 'red'
            canvas.create_rectangle(zone_screen_x - 10, zone_y - 20,
                                     zone_screen_x + 10, zone_y + 20,
                                     fill=color, tags="track")


def draw_bikes(camera_offset):
    canvas.delete("bike")

    # User bike position
    y_user = center_y_func(bike_user_position * PIXELS_PER_METER) - 20
    canvas.create_image(user_fixed_x, y_user, anchor='nw', image=bike_user_tk, tags="bike")
    
    # 👤 User label
    canvas.create_text(user_fixed_x + BIKE_WIDTH // 2, y_user - 10,
                        text=f"👤 {user_name if user_name else 'You'}",
                        font=("Arial", 12, "bold"), fill="cyan", tags="bike")

    # AI bike position
    comp_x = (bike_computer_position * PIXELS_PER_METER) - camera_offset
    y_comp = center_y_func(bike_computer_position * PIXELS_PER_METER) + 20

    if -BIKE_WIDTH < comp_x < screen_width + BIKE_WIDTH:
        canvas.create_image(comp_x, y_comp, anchor='nw', image=bike_computer_tk, tags="bike")

        # 🤖 AI label
        canvas.create_text(comp_x + BIKE_WIDTH // 2, y_comp - 10,
                            text="🤖 AI",
                            font=("Arial", 12, "bold"), fill="orange", tags="bike")


def update():
    global bike_user_position, bike_computer_position, bike_user_speed, bike_computer_speed
    global game_running, frame_count, last_keypress_time
    global zone_effect_active, zone_effect_end_time, zone_speed_change
    global max_coin_generated_x

    if not game_running:
        return

    if paused:
        root.after(UPDATE_INTERVAL, update)
        return

    if current_level == 1:
        bike_computer_speed = random.uniform(9, 12)
    elif current_level == 2:
        bike_computer_speed = random.uniform(10, 13)
    else: 
        bike_computer_speed = random.uniform(11, 14)

    time_since_keypress = (time.time() * 1000) - last_keypress_time
    if time_since_keypress > KEYPRESS_TIMEOUT:
        if bike_user_speed > CRUISE_SPEED:
            bike_user_speed = max(bike_user_speed - 0.1, CRUISE_SPEED)
        elif bike_user_speed < CRUISE_SPEED:
            bike_user_speed = min(bike_user_speed + 0.1, CRUISE_SPEED)

    # Check for Boost/Slow Zone Effects
    current_x = bike_user_position * PIXELS_PER_METER
    for i in range(3):  # 3 zones in track
        zone_x = (TRACK_LENGTH // 4) * (i + 1)
        if abs(current_x - zone_x) < 30 and not zone_effect_active:
            if i % 2 == 0:
                zone_speed_change = BOOST_AMOUNT
                if boost_voice: boost_voice.play()
            else:
                zone_speed_change = SLOW_AMOUNT
                if slow_voice: slow_voice.play()
            zone_effect_active = True
            zone_effect_end_time = time.time() + (BOOST_DURATION if zone_speed_change > 0 else SLOW_DURATION) / 1000
            break

    if zone_effect_active:
        bike_user_speed = min(MAX_SPEED, max(MIN_ACTIVE_SPEED, bike_user_speed + zone_speed_change))
        if time.time() >= zone_effect_end_time:
            zone_effect_active = False
            zone_speed_change = 0.0

    if user_ready and bike_user_speed > 0:
        bike_user_position += bike_user_speed * (UPDATE_INTERVAL / 1000)
    if computer_ready:
        bike_computer_position += bike_computer_speed * (UPDATE_INTERVAL / 1000)

    camera_offset = bike_user_position * PIXELS_PER_METER - user_fixed_x

    # Dynamically generate coins ahead if user passes certain threshold and coins not generated
    coin_generation_ahead_dist = 1000  # pixels ahead to generate coins
    if max_coin_generated_x < bike_user_position * PIXELS_PER_METER + coin_generation_ahead_dist and max_coin_generated_x < TRACK_LENGTH:
        from_x = max_coin_generated_x + 50
        to_x = min(from_x + 600, TRACK_LENGTH)
        generate_coins(from_x, to_x)

    draw_curved_track(camera_offset)
    draw_coins(camera_offset)  # Draw coins with camera offset
    draw_bikes(camera_offset)
    check_coin_collection()  # Check for coin collection

    if zone_effect_active:
        msg = "BOOST!" if zone_speed_change > 0 else "SLOW!"
        canvas.create_text(user_fixed_x + 60, center_y_func(current_x) - 70,
                            text=msg, font=("Arial", 20, "bold"), fill="orange", tags="bike")

    if bike_user_position >= TOTAL_DISTANCE and bike_computer_position >= TOTAL_DISTANCE:
        game_running = False
        show_result("It's a Tie!")
        return
    elif bike_user_position >= TOTAL_DISTANCE:
        game_running = False
        show_result(f"🏆 {user_name if user_name else 'You'} Wins!")
        return
    elif bike_computer_position >= TOTAL_DISTANCE:
        game_running = False
        show_result("🏆 Computer Wins!")
        return

    frame_count += 1
    root.after(UPDATE_INTERVAL, update)
    draw_leaderboard()

def show_result(message):
    global current_level, game_running

    engine_loop.stop()  # stop engine sound
    win_sound.play()

    canvas.delete("result_text")
    fallback_name = user_name if user_name else "You"
    message = message.replace("None", fallback_name)

    canvas.create_text(screen_width//2, canvas_height//2, text=message,
                        font=("Arial", 40, "bold"), fill="red", tags="result_text")

    result_win = tk.Toplevel(root)
    result_win.title("Race Result")
    result_win.geometry("500x300+{}+{}".format(screen_width//2 - 250, screen_height//2 - 150))
    result_win.transient(root)
    result_win.grab_set()
    
    bg_label = tk.Label(result_win, image=popup_bg_img)
    bg_label.place(x=0, y=0, relwidth=1, relheight=1)

    tk.Label(result_win, text=message, font=("Arial", 30, "bold"), fg="red", bg="#000000").pack(pady=60)

    def close_popup():
        result_win.destroy()

    def restart_game_from_popup():
        global current_level
        result_win.destroy()
        if message.startswith("🏆") and (user_name if user_name else "You") in message:
            if current_level < MAX_LEVEL:
                current_level += 1

                def show_level_up_popup():
                    popup = tk.Toplevel(root)
                    popup.title("Level Up")
                    popup.geometry("500x300+{}+{}".format(screen_width//2 - 250, screen_height//2 - 150))
                    popup.transient(root)
                    popup.grab_set()

                    bg_label = tk.Label(popup, image=popup_bg1_img)
                    bg_label.place(x=0, y=0, relwidth=1, relheight=1)

                    tk.Label(popup, text=f"{current_level}", font=("Arial", 30, "bold")).place(x=400, y=60)

                    def on_ok():
                        popup.destroy()
                        reset_race()

                    tk.Button(popup, text="OK", font=("Arial", 20), command=on_ok).place(x=215, y=200)

                show_level_up_popup()

            else:
                def show_victory_popup():
                    popup = tk.Toplevel(root)
                    popup.title("🏁 Victory")
                    popup.geometry("500x300+{}+{}".format(screen_width//2 - 250, screen_height//2 - 150))
                    popup.transient(root)
                    popup.grab_set()

                    bg_label = tk.Label(popup, image=popup_bg2_img)
                    bg_label.place(x=0, y=0, relwidth=1, relheight=1)

                    message = f"{user_name if user_name else 'You'} completed all {MAX_LEVEL} levels! 🏆"
                    tk.Label(popup, text=message, font=("Arial", 20, "bold"), fg="white", bg="#000000",  wraplength=400).place(relx=0.5, rely=0.4, anchor='center')
                    
                    def on_ok():
                        popup.destroy()
                        show_end_screen()

                    tk.Button(popup, text="OK", font=("Arial", 16), command=on_ok).place(relx=0.5, rely=0.7, anchor='center')
                
                show_victory_popup(message)

        else:
            current_level = 1
            #show_end_screen()
            show_end_screen(message)

    btn_frame = tk.Frame(result_win, bg="#000000")
    btn_frame.pack(pady=10)

    tk.Button(btn_frame, text="Close", command=close_popup, width=20).pack(side='left', padx=20)
    tk.Button(btn_frame, text="Next", command=restart_game_from_popup, width=20).pack(side='right', padx=20)
    pause_button.config(text="Pause")

def on_key_press(event):
    global bike_user_speed, last_keypress_time
    if not game_running or not user_ready or paused:
        return
    last_keypress_time = time.time() * 1000
    if event.keysym == 'Up':
        bike_user_speed = min(bike_user_speed + 0.5, MAX_SPEED)
    elif event.keysym == 'Down':
        bike_user_speed = max(bike_user_speed - 0.3, MIN_ACTIVE_SPEED)

def prompt_username():
    global user_name
    if lets_go_sound:
        lets_go_sound.play()

    prompt_win = tk.Toplevel(root)
    prompt_win.title("Enter Your Name")

    popup_width = 500
    popup_height = 300
    x = screen_width // 2 - popup_width // 2
    y = screen_height // 2 - popup_height // 2
    prompt_win.geometry(f"{popup_width}x{popup_height}+{x}+{y}")

    prompt_win.grab_set()
    prompt_win.transient(root)

    bg_label = tk.Label(prompt_win, image=popup_name_bg)
    bg_label.place(x=0, y=0, relwidth=1, relheight=1)

    tk.Label(prompt_win, text="Enter your name:", font=("Arial", 20)).pack(pady=30)
    name_entry = tk.Entry(prompt_win, font=("Arial", 18))
    name_entry.pack(pady=40)

    def submit_name():
        nonlocal prompt_win
        global user_name, user_ready, computer_ready
        name = name_entry.get().strip()
        if not name:
            name = "Player"
        user_name = name
        leaderboard[user_name] = 0
        prompt_win.destroy()
        on_game_start()
        user_ready = False
        computer_ready = False

    tk.Button(prompt_win, text="OK", command=submit_name).pack(pady=10)
    name_entry.focus()

def toggle_pause():
    global paused
    paused = not paused
    pause_button.config(text="Resume" if paused else "Pause")

def reset_race():
    global bike_user_position, bike_computer_position, bike_user_speed, bike_computer_speed
    global start_time, game_running, speed_data, time_data, frame_count, user_ready, computer_ready, paused
    global coins, score, max_coin_generated_x, coins_collected_user, coins_collected_ai, last_impressive_message_time
    global last_good_msg_coin_count, last_superb_msg_coin_count, last_awesome_msg_coin_count
    
    bike_user_position = 0.0
    bike_computer_position = 0.0
    bike_user_speed = 0.0
    bike_computer_speed = 0.0
    start_time = time.time()
    game_running = True
    paused = False
    user_ready = True
    computer_ready = True
    speed_data = {'User    ': [], 'Computer': []}
    time_data = []
    frame_count = 0
    #score = 0
    coins = []
    max_coin_generated_x = 0
    #coins_collected_user = 0
    #coins_collected_ai = 0
    last_impressive_message_time = 0 # Reset cooldown timer
    last_good_msg_coin_count = 0 # Reset milestone counters
    last_superb_msg_coin_count = 0
    last_awesome_msg_coin_count = 0

    canvas.delete("result_text")
    draw_curved_track(0)
    draw_bikes(0)
    generate_coins(0, 800)  # Generate initial coins for first 800 pixels

    engine_loop.play(loops=-1)

    update()
    pause_button.config(text="Pause")

def on_game_start():
    # Hide the intro elements
    canvas.delete("intro_elements")
    canvas.delete("bg_intro") # Delete the intro background
    lets_go_button.place_forget() # Use place_forget for button placed with .place()

    # --- Button Placement Restored ---
    # Pack the game control buttons in their original layout
    button_frame.pack(side='bottom', fill='x', pady=10) # Ensure button_frame is packed
    
    # Use grid to center buttons within the frame
    button_frame.grid_columnconfigure(0, weight=1)
    button_frame.grid_columnconfigure(1, weight=1)
    button_frame.grid_columnconfigure(2, weight=1)

    pause_button.grid(row=0, column=0, padx=10, pady=5)
    down_button.grid(row=0, column=1, padx=10, pady=5)
    restart_button.grid(row=0, column=2, padx=10, pady=5)
    # --- End Button Placement Centered ---
    
    start_countdown()

def on_down():
    global bike_user_speed, last_keypress_time
    if not game_running or not user_ready or paused:
        return
    last_keypress_time = time.time() * 1000
    bike_user_speed = max(bike_user_speed - 0.3, MIN_ACTIVE_SPEED)


def show_end_screen(winner_message):
    canvas.delete("all")
    canvas.create_image(0, 0, anchor='nw', image=end_bg_img)

    if cheer_sound:
        cheer_sound.play()

    # 🏆 Determine the final winner
    #winner_name = user_name if score > coins_collected_ai * 10 else "Computer"
    if "Computer" in winner_message:
        winner_name = "Computer"
    else:
        winner_name = user_name if user_name else "You"
    winner_title = f"👑 WINNER: {winner_name}"

    canvas.create_text(screen_width // 2, canvas_height // 4,
                        text=winner_title, font=("Arial", 42, "bold"), fill="red")

    # 🎯 Show both player's and AI's stats
    canvas.create_text(screen_width // 2, canvas_height // 2 - 60,
                        text=f"{user_name}: {score} points | {coins_collected_user} coins",
                        font=("Arial", 20), fill="black")

    canvas.create_text(screen_width // 2, canvas_height // 2 - 20,
                        text=f"Computer: {coins_collected_ai * 10} points | {coins_collected_ai} coins",
                        font=("Arial", 20), fill="black")

    canvas.create_text(screen_width // 2, canvas_height // 2 + 40,
                        text="Thanks for racing with us!", font=("Arial", 16), fill="white")

    # Hide game control buttons (using grid_forget since they are now gridded)
    pause_button.grid_forget()
    down_button.grid_forget()
    restart_button.grid_forget()
    button_frame.pack_forget() # Hide the frame as well

    # Re-configure restart button for end screen
    restart_button.config(text="Play Again", command=lambda: (
        show_intro_screen_for_restart() # Call a new function to reset and show intro
    ))
    restart_button.place(relx=0.5, rely=0.75, anchor='center')

def show_intro_screen_for_restart():
    global current_level, score, coins_collected_user, coins_collected_ai, last_impressive_message_time
    global last_good_msg_coin_count, last_superb_msg_coin_count, last_awesome_msg_coin_count
    
    current_level = 1 # Reset level
    score = 0
    coins_collected_user = 0
    coins_collected_ai = 0
    last_impressive_message_time = 0 # Reset cooldown
    last_good_msg_coin_count = 0 # Reset milestone counters
    last_superb_msg_coin_count = 0
    last_awesome_msg_coin_count = 0
    
    restart_button.place_forget() # Hide the "Play Again" button
    intro_screen() # Show the intro screen again


def intro_screen():
    # Clear anything that might be on the canvas from previous runs/initial setup
    canvas.delete("all")
    
    # Draw background for intro screen using the new image
    canvas.create_image(0, 0, anchor='nw', image=intro_bg_img, tags="bg_intro")

    
    canvas.create_text(screen_width//2, canvas_height//4 - 10, text="🏁 BIKE RACE 🏁",
                        font=("Arial", 36, "bold"), fill="cyan")
    
    # Instructions
    canvas.create_text(screen_width // 2, canvas_height // 2,
                        text="Compete against the AI and claim victory!\n\n"
                             "Use UP arrow to accelerate, DOWN arrow to slow down.\n"
                             "Collect coins for bonus points! Watch out for speed zones!",
                        font=("Arial", 18), fill="lightgray", justify='center', tags="intro_elements")
    

    # Position the "Let's Go" button
    lets_go_button.place(relx=0.5, rely=0.75, anchor='center')

# Create a frame for the buttons
button_frame = tk.Frame(root)
button_frame.pack(side='bottom', fill='x', pady=10)

# Create buttons and place them in the frame using grid
pause_button = tk.Button(button_frame, text="Pause", command=toggle_pause, width=15, font=("Arial", 16))
down_button = tk.Button(button_frame, text="Slow Down", command=on_down, width=15, font=("Arial", 16))
restart_button = tk.Button(button_frame, text="Restart", command=reset_race, width=15, font=("Arial", 16))

# Place the "Let's Go!" button for the intro screen (initially hidden by grid, shown by .place)
lets_go_button = tk.Button(root, text="Let's Go!", font=("Arial", 24, "bold"),
                           command=prompt_username, bg="green", fg="white",
                           activebackground="darkgreen", activeforeground="white",
                           relief="raised", bd=5, padx=20, pady=10)


# Initial call to show the intro screen
if __name__ == "__main__":
    intro_screen()
    root.bind('<Up>', on_key_press)
    root.bind('<Down>', on_key_press)
    root.mainloop()