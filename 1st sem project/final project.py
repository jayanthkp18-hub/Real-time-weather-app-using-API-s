"""
Formula 4: Real-Time Weather Data Retrieval with OpenWeatherMap API in Python

Description:
This project involves creating a Python application that fetches real-time weather information from the OpenWeatherMap API. 
Users can enter the name of a city to receive current weather data, including temperature, humidity, wind speed, 
and weather conditions. The project demonstrates how to make API calls, handle JSON responses, and present weather 
data in a user-friendly format.

Scope:
- API authentication via API keys
- Building requests to OpenWeatherMap endpoint
- Parsing and handling JSON data formats
- Presenting weather data in a readable format
"""

import tkinter as tk
from tkinter import messagebox, ttk
import requests
from PIL import Image, ImageTk
from io import BytesIO
from tkintermapview import TkinterMapView
from datetime import datetime
import google.generativeai as genai
import os


API_KEY = os.getenv("weather_api")
# Requirement: API authentication via API keys
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

# Configure Gemini AI

GEMINI_API_KEY = os.getenv("gemini_api")
try:
    genai.configure(api_key=GEMINI_API_KEY)
except Exception as e:
    print(f"Error checking Gemini configuration: {e}")

def analyze_weather_with_ai(weather_data, forecast_data):
    """Use Gemini AI to analyze weather data and provide comprehensive insights with model fallback"""
    try:
        # Prepare current weather summary
        current = weather_data.get('main', {})
        weather_desc = weather_data.get('weather', [{}])[0].get('description', 'N/A')
        city_name = weather_data.get('name', 'Unknown')
        wind = weather_data.get('wind', {})
        
        # Extract comprehensive forecast information
        forecast_summary = []
        if forecast_data and 'list' in forecast_data:
            for idx, f in enumerate(forecast_data['list'][:8]):  # Next 24 hours
                dt = datetime.fromtimestamp(f['dt']).strftime('%Y-%m-%d %H:%M')
                temp = f['main']['temp']
                feels = f['main']['feels_like']
                humidity = f['main']['humidity']
                desc = f['weather'][0]['description']
                wind_speed = f['wind']['speed']
                forecast_summary.append(
                    f"{dt}: {temp}°C (feels {feels}°C), {desc}, Humidity: {humidity}%, Wind: {wind_speed} m/s"
                )
        
        # Build comprehensive prompt
        prompt = f"""You are a professional meteorologist. Analyze this weather data for {city_name} and provide practical advice:

CURRENT CONDITIONS:
- Temperature: {current.get('temp', 'N/A')}°C
- Feels Like: {current.get('feels_like', 'N/A')}°C
- Humidity: {current.get('humidity', 'N/A')}%
- Pressure: {current.get('pressure', 'N/A')} hPa
- Weather: {weather_desc}
- Wind Speed: {wind.get('speed', 'N/A')} m/s

24-HOUR FORECAST:
{chr(10).join(forecast_summary)}

Based on this complete weather data, provide expert advice on:
1. Health and wellness impact
2. Best activities for today
3. What to wear
4. Travel conditions
5. Any weather warnings or precautions

Keep your response conversational and practical, around 150-200 words."""

        # List of models to try in order of preference (Lite/Flash models often have better free tier availability)
        models_to_try = [
            'gemini-2.0-flash-lite',
            'gemini-flash-latest',
            'gemini-2.0-flash',
            'gemini-2.0-flash-exp'
        ]

        last_error = None
        for model_name in models_to_try:
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                return response.text
            except Exception as e:
                last_error = e
                print(f"Model {model_name} failed: {e}")
                continue  # Try next model

        # If all failed
        return f"AI Analysis currently unavailable (Quota limit reached). Please try again later.\nDetails: {str(last_error)}"

    except Exception as e:
        return f"AI Analysis unavailable: {str(e)}"

def get_all_data():
    """Fetch and display both current weather and forecast data"""
    city = city_entry.get().strip()
    if not city:
        messagebox.showwarning("Input error", "Please enter a city name.")
        return
    
    # Fetch both current weather and forecast
    weather_result = get_weather()
    forecast_result = get_forecast()
    
    # If both successful, run AI analysis
    if weather_result and forecast_result:
        ai_analysis = analyze_weather_with_ai(weather_result, forecast_result)
        display_ai_analysis(ai_analysis)

# ========== THEME SETTINGS ==========
COLORS = {
    "bg": "#121927",             # Deep Dark Blue background
    "card_bg": "#1e2636",        # Slightly lighter card background
    "text_main": "#ffffff",      # White text
    "text_secondary": "#a0aab8", # Light gray text
    "accent": "#4cc2ff",         # Light Blue accent
    "success": "#28a745",        # Green
    "warning": "#ffc107"         # Yellow
}

FONTS = {
    "h1": ("Segoe UI", 48),       # Large Temp
    "h2": ("Segoe UI", 24),       # City Name
    "h3": ("Segoe UI", 16, "bold"), # Section Headers
    "body": ("Segoe UI", 10),
    "stat_label": ("Segoe UI", 9),
    "stat_value": ("Segoe UI", 12, "bold")
}

# ========== UI FUNCTIONS ==========

def create_card(parent, row, col, rowspan=1, colspan=1, title=None):
    """Factory to create a styled card frame"""
    card = tk.Frame(parent, bg=COLORS["card_bg"], padx=15, pady=15)
    card.grid(row=row, column=col, rowspan=rowspan, columnspan=colspan, 
             sticky="nsew", padx=10, pady=10)
    
    # Configure grid weights for the card contents
    card.grid_columnconfigure(0, weight=1)
    
    if title:
        tk.Label(card, text=title, font=FONTS["h3"], bg=COLORS["card_bg"], 
                fg=COLORS["text_main"], anchor="w").pack(fill="x", pady=(0, 10))
                
    return card

def get_weather():
    city = city_entry.get().strip()
    if not city:
        messagebox.showwarning("Input error", "Please enter a city name.")
        return
    params = {
        "q": city,
        "appid": API_KEY,
        "units": "metric"
    }
    try:
        response = requests.get(BASE_URL, params=params, timeout=5)
        data = response.json()
    except requests.exceptions.RequestException as e:
        messagebox.showerror("Network error", f"Could not reach server:\n{e}")
        return

    if data.get("cod") != 200:
        message = data.get("message", "Unknown error")
        messagebox.showerror("API error", f"Error from API:\n{message}")
        return

    # Extract Data
    city_name = data.get("name", city)
    main = data.get("main", {})
    weather_list = data.get("weather", [])
    wind = data.get("wind", {})
    temp = main.get("temp")
    humidity = main.get("humidity")
    pressure = main.get("pressure")
    feels_like = main.get("feels_like")
    description = weather_list[0].get("description") if weather_list else "N/A"
    icon_code = weather_list[0].get("icon") if weather_list else None
    wind_speed = wind.get("speed")
    
    # Update Map
    coord = data.get("coord", {})
    if coord.get("lat") and coord.get("lon"):
        map_widget.set_position(coord.get("lat"), coord.get("lon"))
        map_widget.set_marker(coord.get("lat"), coord.get("lon"), text=city_name)
    
    # Update UI Labels
    lbl_city.config(text=city_name)
    lbl_date.config(text=datetime.now().strftime("%A, %d %B %Y"))
    
    if temp is not None:
        lbl_temp.config(text=f"{int(temp)}°")
    lbl_desc.config(text=description.title())
    
    # Update Stats Grid
    lbl_stat_wind.config(text=f"{wind_speed} m/s")
    lbl_stat_humid.config(text=f"{humidity}%")
    lbl_stat_press.config(text=f"{pressure} hPa")
    lbl_stat_feels.config(text=f"{feels_like:.1f}°")

    # Update Icon
    if icon_code:
        try:
            icon_url = f"http://openweathermap.org/img/wn/{icon_code}@4x.png"
            icon_response = requests.get(icon_url)
            image_data = icon_response.content
            img = Image.open(BytesIO(image_data))
            img = img.resize((100, 100), Image.LANCZOS)
            icon_img = ImageTk.PhotoImage(img)
            lbl_icon.config(image=icon_img)
            lbl_icon.image = icon_img
        except:
            pass

    return data

def get_forecast():
    """Get and display 5-day weather forecast with detailed table"""
    city = city_entry.get().strip()
    if not city:
        messagebox.showwarning("Input error", "Please enter a city name.")
        return
    
    try:
        url = "http://api.openweathermap.org/data/2.5/forecast"
        params = {'q': city, 'appid': API_KEY, 'units': 'metric'}
        
        response = requests.get(url, params=params, timeout=5)
        data = response.json()
        
        if response.status_code == 200:
            display_forecast(data)
            display_forecast_table(data)  # New detailed table instead of graph
            return data  # Return data for AI analysis
        else:
            messagebox.showerror("API error", data.get("message", "Could not fetch forecast"))
            return None
    except requests.exceptions.RequestException as e:
        messagebox.showerror("Network error", f"Could not reach server:\n{e}")
        return None

def display_forecast(data):
    """Display 5-day forecast cards"""
    # Clear existing cards
    for widget in forecast_container.winfo_children():
        widget.destroy()
        
    # Group forecasts by day
    daily = {}
    for f in data['list']:
        d = f['dt_txt'].split(" ")[0]
        daily.setdefault(d, []).append(f)
    
    # Create a card for each of the next 5 days
    col_idx = 0
    for date, forecasts in list(daily.items())[:5]:
        mid = next((x for x in forecasts if "12:00:00" in x['dt_txt']), forecasts[len(forecasts)//2])
        
        temp = mid['main']['temp']
        icon = mid['weather'][0]['icon']
        
        date_obj = datetime.strptime(date, "%Y-%m-%d")
        day_name = date_obj.strftime("%a") # Mon, Tue...
        
        # Day Card
        day_frame = tk.Frame(forecast_container, bg=COLORS["card_bg"], padx=5, pady=5)
        day_frame.grid(row=0, column=col_idx, padx=5, sticky="ew")
        
        tk.Label(day_frame, text=day_name, font=("Segoe UI", 11), bg=COLORS["card_bg"], fg=COLORS["text_secondary"]).pack()
        
        # Try to load icon
        try:
            icon_url = f"http://openweathermap.org/img/wn/{icon}@2x.png"
            icon_response = requests.get(icon_url)
            image_data = icon_response.content
            img = Image.open(BytesIO(image_data))
            img = img.resize((50, 50), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            icon_lbl = tk.Label(day_frame, image=photo, bg=COLORS["card_bg"])
            icon_lbl.image = photo
            icon_lbl.pack()
        except:
            tk.Label(day_frame, text="☁", bg=COLORS["card_bg"], fg="white").pack()
            
        tk.Label(day_frame, text=f"{int(temp)}°", font=("Segoe UI", 12, "bold"), bg=COLORS["card_bg"], fg=COLORS["text_main"]).pack()
        
        col_idx += 1

def display_forecast_table(data):
    """Update detail table with Dark Mode styling settings"""
    # Simply clear and repopulate the existing treeview
    # Note: Modern styling for Treeview requires ttk.Style
    for item in table.get_children():
        table.delete(item)
        
    for idx, f in enumerate(data['list'][:24]): # Next 72 hours approx
        dt = datetime.fromtimestamp(f['dt']).strftime('%a %H:%M')
        temp = f"{f['main']['temp']:.1f}"
        weather = f['weather'][0]['description'].title()
        wind = f"{f['wind']['speed']}"
        humidity = f"{f['main']['humidity']}"
        
        table.insert("", "end", values=(dt, temp, weather, wind, humidity))

def display_ai_analysis(ai_text):
    text_widget.config(state=tk.NORMAL)
    text_widget.delete(1.0, tk.END)
    text_widget.insert(1.0, ai_text)
    text_widget.config(state=tk.DISABLED)

# ========== MAIN UI SETUP ==========
root = tk.Tk()
root.title("Weather (Formula 4)")
root.geometry("1000x800")
root.configure(bg=COLORS["bg"])

# --- STYLE CONFIGURATION ---
style = ttk.Style()
style.theme_use("clam") # 'clam' allows better color customization
style.configure("Treeview", 
               background=COLORS["card_bg"], 
               foreground=COLORS["text_main"], 
               fieldbackground=COLORS["card_bg"],
               borderwidth=0,
               font=("Segoe UI", 10))
style.configure("Treeview.Heading", 
               background=COLORS["bg"], 
               foreground=COLORS["text_main"],
               font=("Segoe UI", 10, "bold"),
               borderwidth=0)
style.map("Treeview", background=[("selected", COLORS["accent"])])
style.configure("Vertical.TScrollbar", background=COLORS["card_bg"], troughcolor=COLORS["bg"], borderwidth=0, arrowcolor=COLORS["text_main"])

# --- TOP BAR (Search) ---
top_bar = tk.Frame(root, bg=COLORS["bg"], pady=10, padx=20)
top_bar.pack(fill="x")

tk.Label(top_bar, text="Forecast", font=FONTS["h3"], bg=COLORS["bg"], fg=COLORS["text_main"]).pack(side="left")

search_frame = tk.Frame(top_bar, bg="#2c3340", padx=10, pady=5) # Rounded look simulation
search_frame.pack(side="right")

city_entry = tk.Entry(search_frame, bg="#2c3340", fg="white", font=("Segoe UI", 11), borderwidth=0, width=25)
city_entry.pack(side="left", padx=5)
city_entry.insert(0, "Bangalore")
city_entry.bind('<Return>', lambda e: get_all_data())

btn_search = tk.Button(search_frame, text="🔍", command=get_all_data, 
                      bg="#2c3340", fg="white", bd=0, activebackground="#2c3340", activeforeground=COLORS["accent"])
btn_search.pack(side="left")

# --- MAIN SCROLLABLE AREA ---
# To support scrolling the entire dashboard
container = tk.Frame(root, bg=COLORS["bg"])
container.pack(fill="both", expand=True)

canvas = tk.Canvas(container, bg=COLORS["bg"], highlightthickness=0)
scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
scrollable_frame = tk.Frame(canvas, bg=COLORS["bg"])

scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

def _configure_width(event):
    canvas.itemconfig(canvas_window, width=event.width)
canvas.bind("<Configure>", _configure_width)
canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

canvas.configure(yscrollcommand=scrollbar.set)
canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

# --- DASHBOARD GRID ---
# Grid Setup: 2 Columns. Left=Current Weather, Right=Map. Bottom=Forecast/AI
scrollable_frame.grid_columnconfigure(0, weight=3) # Left column wider
scrollable_frame.grid_columnconfigure(1, weight=2) # Right column (Map)

# 1. CURRENT WEATHER CARD (Top Left)
card_current = create_card(scrollable_frame, 0, 0)

# Header (Location + Date)
lbl_city = tk.Label(card_current, text="City Name", font=FONTS["h2"], bg=COLORS["card_bg"], fg=COLORS["text_main"], anchor="w")
lbl_city.pack(fill="x")
lbl_date = tk.Label(card_current, text="Date", font=("Segoe UI", 11), bg=COLORS["card_bg"], fg=COLORS["text_secondary"], anchor="w")
lbl_date.pack(fill="x", pady=(0, 15))

# Hero Content (Icon + Temp + Desc)
hero_frame = tk.Frame(card_current, bg=COLORS["card_bg"])
hero_frame.pack(fill="x", pady=10)

lbl_icon = tk.Label(hero_frame, bg=COLORS["card_bg"])
lbl_icon.pack(side="left", padx=(0, 20))

temp_frame = tk.Frame(hero_frame, bg=COLORS["card_bg"])
temp_frame.pack(side="left")
lbl_temp = tk.Label(temp_frame, text="--°", font=FONTS["h1"], bg=COLORS["card_bg"], fg=COLORS["text_main"])
lbl_temp.pack(anchor="w")
lbl_desc = tk.Label(temp_frame, text="Condition", font=("Segoe UI", 14), bg=COLORS["card_bg"], fg=COLORS["text_secondary"])
lbl_desc.pack(anchor="w")

# Stats Grid (Wind, Humidity, etc.)
stats_frame = tk.Frame(card_current, bg=COLORS["card_bg"], pady=15)
stats_frame.pack(fill="x")
stats_frame.grid_columnconfigure(0, weight=1)
stats_frame.grid_columnconfigure(1, weight=1)
stats_frame.grid_columnconfigure(2, weight=1)
stats_frame.grid_columnconfigure(3, weight=1)

def create_stat(parent, label, row, col):
    f = tk.Frame(parent, bg=COLORS["card_bg"])
    f.grid(row=row, column=col, sticky="w", pady=5)
    tk.Label(f, text=label, font=FONTS["stat_label"], bg=COLORS["card_bg"], fg=COLORS["text_secondary"]).pack(anchor="w")
    val = tk.Label(f, text="--", font=FONTS["stat_value"], bg=COLORS["card_bg"], fg=COLORS["text_main"])
    val.pack(anchor="w")
    return val

lbl_stat_wind = create_stat(stats_frame, "Wind", 0, 0)
lbl_stat_humid = create_stat(stats_frame, "Humidity", 0, 1)
lbl_stat_press = create_stat(stats_frame, "Pressure", 0, 2)
lbl_stat_feels = create_stat(stats_frame, "Feels Like", 0, 3)

# 2. MAP CARD (Top Right)
card_map = create_card(scrollable_frame, 0, 1, title="Location")
map_widget = TkinterMapView(card_map, corner_radius=10)
map_widget.pack(fill="both", expand=True, ipady=100) # ipady adds height

# 3. 5-DAY FORECAST ROW (Middle)
# Container for forecast cards
forecast_area = create_card(scrollable_frame, 1, 0, colspan=2, title="Daily Forecast")
forecast_container = tk.Frame(forecast_area, bg=COLORS["card_bg"])
forecast_container.pack(fill="x")
# We'll pack day-cards into this forecast_container dynamically

# 4. HOURLY GRID & AI ADVICE (Bottom)
# Split bottom row: Left=Table, Right=AI

# Hourly Table Card
card_table = create_card(scrollable_frame, 2, 0)
tk.Label(card_table, text="Hourly Forecast", font=FONTS["h3"], bg=COLORS["card_bg"], fg=COLORS["text_main"], anchor="w").pack(fill="x", pady=(0, 10))

table = ttk.Treeview(card_table, columns=("Time", "Temp", "Weather", "Wind", "Hum"), show="headings", height=8)
table.heading("Time", text="Time")
table.heading("Temp", text="Temp (°C)")
table.heading("Weather", text="Weather")
table.heading("Wind", text="Wind")
table.heading("Hum", text="Hum %")

table.column("Time", width=100)
table.column("Temp", width=70)
table.column("Weather", width=120)
table.column("Wind", width=70)
table.column("Hum", width=70)

table.pack(fill="both", expand=True)

# AI Insight Card
card_ai = create_card(scrollable_frame, 2, 1, title="🤖 AI Weather Analyst")

# Frame to hold text + scrollbar
ai_content_frame = tk.Frame(card_ai, bg=COLORS["card_bg"])
ai_content_frame.pack(fill="both", expand=True)

ai_scrollbar = ttk.Scrollbar(ai_content_frame)
ai_scrollbar.pack(side="right", fill="y")

text_widget = tk.Text(ai_content_frame, bg="#252b36", fg="#d1d5db", font=("Segoe UI", 10), 
                     relief="flat", height=10, padx=10, pady=10, wrap="word",
                     yscrollcommand=ai_scrollbar.set)
text_widget.pack(side="left", fill="both", expand=True)

ai_scrollbar.config(command=text_widget.yview)

root.mainloop()
