import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import geopandas as gpd
import redis
from datetime import datetime, timedelta
from shapely.geometry import Point
from pyproj import Transformer
from functions1 import *  
import os
import pytz
from pymongo import MongoClient
import json
from bson import ObjectId

# MongoDB connection
MONGO_URI = "mongodb+srv://GKaim:Snoopy1929@pagcluster2.l06nj.mongodb.net/pagcluster2?retryWrites=true&w=majority&tls=true"
client = MongoClient(MONGO_URI)

def find_documents_by_name(client, database_name, collection_name, name):
    try:
        db = client[database_name]
        collection = db[collection_name]
        query = {"properties.name": name}
        documents = list(collection.find(query))
        return documents
    except Exception as e:
        print(f"Error finding documents: {e}")
        return []

def open_calendar():
    def get_date():
        selected_date = cal.selection_get()
        date_entry.delete(0, tk.END)
        date_entry.insert(0, selected_date.strftime("%Y-%m-%d"))
        top.destroy()

    top = tk.Toplevel(root)
    top.title("Wybierz datę")
    cal = Calendar(top, selectmode="day", date_pattern="yyyy-mm-dd")
    cal.pack(pady=10)
    tk.Button(top, text="Wybierz", command=get_date).pack(pady=10)

def on_station_selected(event):
    selected_station = station_combo.get()
    if selected_station:
        info_button.place(x=10, y=280)  # Show the button at the specified location
    else:
        info_button.place_forget()

def json_serialize(obj):
    if isinstance(obj, ObjectId):
        return str(obj)  # Convert ObjectId to string
    raise TypeError(f"Object of type {obj.__class__.__name__} is not serializable")

def remove_geometry_field(doc):
    if 'geometry' in doc:
        # geom = doc['geometry']
        geometry = doc.pop('geometry')  # Remove the 'geometry' field
    return doc

def clean_value(value):
    """Cleans up unwanted characters or escape sequences."""
    # If the value is a dictionary (e.g., coordinates or nested object), we can convert it to string or handle it
    if isinstance(value, dict):
        return str(value)  # Convert dictionary to string
    elif isinstance(value, list):
        return ', '.join(map(str, value))  # Join list elements into a string
    else:
        return str(value).replace("?", "")  # Clean up unwanted characters like "?" or escape sequences

def show_station_info():
    selected_station_name = station_combo.get()
    if not selected_station_name:
        messagebox.showerror("Błąd", "Proszę wybrać stację.")
        return
    selected_station = station_mapping.get(selected_station_name)
    name = selected_station.split(":")[1]
    documents = find_documents_by_name(client, "PAGCluster2", "effacility", name)
    if not documents:
        messagebox.showinfo("Informacja", f"Brak danych w MongoDB dla stacji: {selected_station_name}")
        return
    
    info_window = tk.Toplevel(root)
    info_window.geometry("700x400")
    info_window.title(f"Informacje o stacji: {selected_station_name}")

    properties_list = []
    for feature in documents:
        if 'properties' in feature:
            properties_list.append(feature['properties'])

    # Create a list of unique attribute names from all properties
    attribute_names = set()
    for properties in properties_list:
        attribute_names.update(properties.keys())
    
    # Convert the properties to a DataFrame where columns are attributes and rows are their corresponding values
    rows = []
    for properties in properties_list:
        row = [properties.get(attr, '') for attr in attribute_names]  # Fetch values for each attribute
        rows.append(row)
    
    # Convert the rows into a DataFrame
    df = pd.DataFrame(rows, columns=list(attribute_names))
    df = df.T
    # Create a Treeview widget
    tree = ttk.Treeview(info_window, columns=["Attribute"] + list(df.columns), show="headings")
    
    # Define the first column for attribute names
    tree.column("Attribute", width=100)
    for col in df.columns:
        tree.column(col, width=500)
    
    # Define the headings for columns
    tree.heading("Attribute", text="Attribute")
    for col in df.columns:
        tree.heading(col, text=col)

    # Insert the data into the Treeview
    for index, row in df.iterrows():
        tree.insert("", "end", values=[row.name] + list(row))  # First column is the attribute name

    # Pack the Treeview widget
    tree.pack(fill=tk.Y, side="left", padx=10, pady=10)
    
    # Run the Tkinter main loop for the info window
    info_window.mainloop()

def get_sensor_code(sensor_name):
    for code, name in sensor_files.items():
        if name == sensor_name:
            return code
    return None

def sun_times(stacja, date_time):
    date_time = date_time + " 12:00"
    date_time = datetime.strptime(date_time, "%Y-%m-%d %H:%M")
    lat = dms_to_decimal(stacja['Szerokość geograficzna'])
    lon = dms_to_decimal(stacja['Długość geograficzna'])
    timezone = stacja.get('Strefa czasowa', 'Europe/Warsaw')
    city = LocationInfo(stacja['Nazwa'], "", timezone, lat, lon)
    tz = pytz.timezone(city.timezone)
    date_time = tz.localize(date_time)
    s = sun(city.observer, date_time.date(), tzinfo=tz)
    return s["sunrise"].strftime("%H:%M:%S"), s["sunset"].strftime("%H:%M:%S")
station_mapping = {}

def update_stations(event):
    selected_county_name = county_combo.get()
    root.update_idletasks()
    station_mapping.clear()
    station_names = []
    try:
        powiat_key = f"powiat:{selected_county_name.strip()}"
        stacje_str = redis_client.hget(powiat_key, "Stacje")
        stacje_list = [s.strip() for s in stacje_str.split(",")]
        for station in stacje_list:
            station_key = f"stacja:{station}"
            station_data = redis_client.hgetall(station_key)
            if station_data:
                station_name = station_data.get("Nazwa", station)
                station_mapping[station_name] = station_key
                station_names.append(station_name)
            else:
                messagebox.showwarning("Brak danych", f"Brak danych dla stacji {station}.")
    except Exception as e:
        messagebox.showerror("Błąd", f"Błąd odczytu stacji: {e}")
        return
    station_combo['values'] = station_names
    station_combo.set("")
    info_button.place_forget()

def display_statistics():
    # Get selected station name from the UI
    selected_station_name = station_combo.get()
    if not selected_station_name:
        messagebox.showerror("Błąd", "Proszę wybrać stację.")
        return

    # Map station name to station code
    selected_station = station_mapping.get(selected_station_name)
    if not selected_station:
        messagebox.showerror("Błąd", "Nie znaleziono klucza dla wybranej stacji.")
        return

    # Collect input data from the UI
    wybrana_data = date_entry.get()
    godzina_start = f"{hour_spin.get()}:{minute_spin.get()}:{second_spin.get()}"
    godzina_end = f"{hour_spin_end.get()}:{minute_spin_end.get()}:{second_spin_end.get()}"
    sensor_name = sensor_combo.get()


    # Fetch station data from Redis
    stacja = redis_client.hgetall(selected_station)
    sunrise_time, sunset_time = sun_times(stacja, wybrana_data)

    # Prepare next day information for nighttime calculations
    data = datetime.strptime(wybrana_data, "%Y-%m-%d")
    następny_dzień = data + timedelta(days=1)
    następny_dzień_str = następny_dzień.strftime("%Y-%m-%d")
    sunrise_time_next_day, sunset_time_next_day = sun_times(stacja, następny_dzień_str)


    # Validate sensor and file existence
    sensor_code = get_sensor_code(sensor_name)
    file_path = f"Meteo_2024-10/{sensor_code}_2024_10.csv" 
    if not os.path.exists(file_path):
        messagebox.showerror("Błąd", f"Plik dla sensora {sensor_code} nie istnieje.")
        return

    # Read and filter data
    df_dane = pd.read_csv(file_path, sep=";", header=None, names=["kodSH", "parametrSH", "date_time", "value"])
    df_dane["date"] = df_dane["date_time"].str.split(" ").str[0]
    df_dane["date_time"] = pd.to_datetime(df_dane["date_time"])
    df_filtered = df_dane[df_dane["kodSH"] == int(selected_station.split(":")[1])]

    if df_filtered.empty:
        messagebox.showinfo("Informacja", "Brak danych dla wybranej stacji i sensora.")
        return

    # Calculate statistics
    try:
        statystyki_dnia = statystyki_wybrana_data(df_filtered, wybrana_data)
        statystyki_godziny = statystyki_wybrany_przedzial(df_filtered, wybrana_data, wybrana_data, godzina_start, godzina_end)
        statystyka_godzina = statystyki_wybrany_przedzial(df_filtered, wybrana_data, wybrana_data, godzina_start, godzina_start)
        statystyki_dnia_dzien = statystyki_wybrany_przedzial(df_filtered, wybrana_data, wybrana_data, sunrise_time, sunset_time)
        statystyki_nocy_noc = statystyki_wybrany_przedzial(df_filtered, wybrana_data, następny_dzień_str, sunset_time, sunrise_time_next_day)

        # Create tables for displaying results
        def create_table(title, data, x1, y1):
            # Create a frame for each table

            table_frame = ttk.LabelFrame(root, width=180, height=105)
            table_frame.place(x=x1,y=y1)
            ttk.Label(root, text=title).place(x=x1-2,y=y1-2)
            # Create the Treeview widget
            tree = ttk.Treeview(table_frame, columns=("Key", "Value"), show="headings", height=5)
            tree.place(x=0,y=0, width=180, height=105)

            # Define columns
            tree.heading("Key", text=" ")
            tree.heading("Value", text="Wartość")
            tree.column("Key", anchor="center", width=30)
            tree.column("Value", anchor="center", width=30)

            # Insert rows
            for key, value in data.items():
                tree.insert("", "end", values=(key, value))

        tk.Label(root, text="Statystyki").place(x=340, y=10, anchor="w")
        # Call create_table for each dataset
        create_table(f"na dzień {wybrana_data}", statystyki_dnia, 340, 20)
        create_table(f"dla godziny {godzina_start}", statystyka_godzina, 340, 140)
        create_table("dla pory dnia: dzień", statystyki_dnia_dzien, 540, 20)
        create_table(f"dla przedziału godzin {godzina_start}-{godzina_end}", statystyki_godziny, 340, 250)
        create_table("dla pory dnia: noc", statystyki_nocy_noc, 540, 140)
        
        ttk.Label(root, text=f"Wschód słońca: {sunrise_time}").place(x=550, y=310)
        ttk.Label(root, text=f"Zachód słońca: {sunset_time}").place(x=550, y=330)

    except Exception as e:
        messagebox.showerror("Błąd", f"Wystąpił błąd podczas obliczeń: {e}")



def update_counties(event):
    selected_voivodeship = voivodeship_combo.get()
    filtered_counties = gdf[gdf['wojewodztw'] == selected_voivodeship]['name'].tolist()
    filtered_counties.sort()
    county_combo['values'] = filtered_counties
    county_combo.set("")
    station_combo.set("")
    station_combo['values'] = []
    info_button.place_forget()

# Load shapefile and Redis
sciezka_do_shp = "Dane/powiaty_woj.shp"
gdf = gpd.read_file(sciezka_do_shp)
counties = gdf['name'].tolist()
counties.sort()
voivodeships = gdf['wojewodztw'].unique().tolist()
voivodeships.sort()
redis_url = "redis://default:b90uh2i9DzbUmGHB4E9aZsqApdUiWkcb@redis-19957.c300.eu-central-1-1.ec2.redns.redis-cloud.com:19957"
redis_client = redis.StrictRedis.from_url(redis_url, decode_responses=True)

sensor_files = {
    "B00300S": "Temperatura powietrza (oficjalna)",
    "B00305A": "Temperatura gruntu (czujnik)",
    "B00202A": "Kierunek wiatru (czujnik)",
    "B00702A": "Średnia prędkość wiatru czujnik 10 minut",
    "B00703A": "Prędkość maksymalna (czujnik)",
    "B00608S": "Suma opadu 10 minutowego",
    "B00604S": "Suma opadu dobowego",
    "B00606S": "Suma opadu godzinowego",
    "B00802A": "Wilgotność względna powietrza (czujnik)",
    "B00714A": "Największy poryw w okresie 10min ze stacji Synoptycznej",
    "B00910A": "Zapas wody w śniegu (obserwator)"
}


root = tk.Tk()
root.title("Statystyki Meteorologiczne")
root.geometry("800x400")
tk.Label(root, text="Wybierz województwo:").place(x=20, y=20, anchor="w")
voivodeship_combo = ttk.Combobox(root, values=voivodeships)
voivodeship_combo.place(x=160, y=10)
voivodeship_combo.bind("<<ComboboxSelected>>", update_counties)


tk.Label(root, text="Wybierz powiat:").place(x=20, y=60, anchor="w")
county_combo = ttk.Combobox(root)
county_combo.place(x=160, y=50)
county_combo.bind("<<ComboboxSelected>>", update_stations)


tk.Label(root, text="Wybierz stację:").place(x=20, y=100, anchor="w")
station_combo = ttk.Combobox(root)
station_combo.place(x=160, y=90)
station_combo.bind("<<ComboboxSelected>>", on_station_selected)


tk.Label(root, text="Wybierz sensor:").place(x=20, y=140, anchor="w")
sensor_combo = ttk.Combobox(root, values=list(sensor_files.values()))
sensor_combo.place(x=160, y=130)


tk.Label(root, text="Data (YYYY-MM-DD):").place(x=20, y=180, anchor="w")
date_entry = tk.Entry(root)
date_entry.place(x=160, y=170)


tk.Button(root, text="📅", command=open_calendar).place(x=300, y=165)

tk.Label(root, text="Godzina startowa:").place(x=20, y=210, anchor="w")

hour_spin = tk.Spinbox(root, from_=0, to=23, width=3, format="%02.0f")
hour_spin.place(x=160, y=200)
hour_spin.delete(0, tk.END)
hour_spin.insert(0, "00")

minute_spin = tk.Spinbox(root, from_=0, to=59, width=3, format="%02.0f")
minute_spin.place(x=200, y=200)
minute_spin.delete(0, tk.END)
minute_spin.insert(0, "00")

second_spin = tk.Spinbox(root, from_=0, to=59, width=3, format="%02.0f")
second_spin.place(x=240, y=200)
second_spin.delete(0, tk.END)
second_spin.insert(0, "00")


tk.Label(root, text="Godzina końcowa:").place(x=20, y=250, anchor="w")
hour_spin_end= tk.Spinbox(root, from_=0, to=23, width=3, format="%02.0f")
hour_spin_end.place(x=160, y=240)
hour_spin_end.delete(0, tk.END)
hour_spin_end.insert(0, "00")   

minute_spin_end = tk.Spinbox(root, from_=0, to=59, width=3, format="%02.0f")        
minute_spin_end.place(x=200, y=240)
minute_spin_end.delete(0, tk.END)
minute_spin_end.insert(0, "00")

second_spin_end = tk.Spinbox(root, from_=0, to=59, width=3, format="%02.0f")
second_spin_end.place(x=240, y=240)
second_spin_end.delete(0, tk.END)
second_spin_end.insert(0, "00")

info_button = tk.Button(root, text="Pokaż informacje o stacji", command=show_station_info)
info_button.place(x=10, y=280)
info_button.place_forget()  # Initially hide the button

result_text = tk.StringVar()
tk.Label(root, textvariable=result_text, wraplength=600).place(x=60, y=450, anchor="w")



tk.Button(root, text="Pokaż statystyki", command=display_statistics).place(x=160, y=280)
root.mainloop()
