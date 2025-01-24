#plik pomocniczy z funkcjami
import requests, zipfile, io
import pandas as pd
from astral.sun import sun
from scipy.stats import trim_mean
from astral import LocationInfo
from datetime import datetime, timedelta
import numpy as np
import pytz
from tkcalendar import Calendar


def to_float2(d):
    if isinstance(d, dict):  # If it's a dictionary, process its items
        return {k: to_float2(v) for k, v in d.items()}
    elif isinstance(d, np.float64):  # If it's np.float64, convert to float
        return round(float(d),1)
    return d

def statystyki_wybrana_data(df, date):
    filtered_df = df.loc[df['date'] == date]
    stats = statystyki(filtered_df)
    return stats

def statystyki_wybrany_przedzial(df, start_date, end_date, start_time = '00:00:00', end_time = '00:00:00'):
    
    full_start = pd.to_datetime(f"{start_date} {start_time}")
    full_end = pd.to_datetime(f"{end_date} {end_time}")

    filtered_df = df[(df['date_time'] >= full_start) & (df['date_time'] <= full_end)]

    stats = statystyki(filtered_df)

    return stats 

def statystyki(df):
    if df.empty:
        stats = {
            "średnia": 'NaN',
            "mediana": 'Nan',
            "średnia_obc": 'Nan',
        } 
    else:
        srednia = df["value"].mean()
        mediana = df["value"].median()
        srednia_obc = trim_mean(df["value"], proportiontocut=0.1)  # 10% obcinanie
        stats = {"średnia": srednia, "mediana": mediana, "średnia_obc": srednia_obc}
        stats = to_float2(stats)
    return stats

def statystyki_pora_dnia(df):
    data_dzien = df[df["pora"] == "dzien"]
    data_noc = df[df["pora"] == "noc"]

    data_dzien = statystyki(data_dzien)
    data_noc = statystyki(data_dzien)

    stats = {
        "dzień": data_dzien,
        "noc": data_noc,
    }

    return stats

def read_station_file(file):
    df_stacje = pd.read_csv(file, sep=";", header=0, names=['LP','ID','nazwa','rzeka','szer_geo','dl_geo','H', 'geometry', 'powiat', 'wojewodztwo'])
    return df_stacje

def dms_to_decimal(dms):
    degrees, minutes, seconds = map(int, dms.split())
    return degrees + minutes / 60 + seconds / 3600



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

