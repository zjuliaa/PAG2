
import redis
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from pyproj import Transformer

def dms_to_decimal(dms_str):
    degrees, minutes, seconds = map(float, dms_str.split())
    return degrees + (minutes / 60) + (seconds / 3600)

# Połączenie z Redis
redis_url = "redis://default:b90uh2i9DzbUmGHB4E9aZsqApdUiWkcb@redis-19957.c300.eu-central-1-1.ec2.redns.redis-cloud.com:19957"
redis_client = redis.StrictRedis.from_url(redis_url, decode_responses=True)
print("Połączono z bazą Redis.")

sciezka_powiaty = r"C:\sem5\PAG\projekt2\Dane\powiaty_woj.shp"
# Wczytanie danych o powiatach (przykładowy plik Shapefile)
gdf = gpd.read_file(sciezka_powiaty)

data = {}

try:
    all_station_data = redis_client.keys("stacja:*")
    print(f"Znaleziono {len(all_station_data)} stacji w bazie.")
    for station_key in all_station_data:
        station_data = redis_client.hgetall(station_key)
        if 'Długość geograficzna' in station_data and 'Szerokość geograficzna' in station_data:
            longitude = dms_to_decimal(station_data['Długość geograficzna'])
            latitude = dms_to_decimal(station_data['Szerokość geograficzna'])
            transformer = Transformer.from_crs("EPSG:4326", "EPSG:2180", always_xy=True)
            x, y = transformer.transform(longitude, latitude)
            point = Point(x, y)

            matching_county = gdf[gdf.contains(point)]
            if not matching_county.empty:
                county_name = matching_county.iloc[0]['name']
                if county_name not in data:
                    data[county_name] = []
                station_id = station_key.split(":")[1]  
                data[county_name].append(station_id)  
                print(f"Dodano stację {station_id} do powiatu {county_name}.")
except Exception as e:
    print(f"Błąd odczytu danych: {e}")

# Zapis do pliku CSV
output_df = pd.DataFrame(list(data.items()), columns=['Powiat', 'Stacje'])
output_df['Stacje'] = output_df['Stacje'].apply(lambda x: ', '.join(x))
output_df.to_csv('stacje_w_powiatach_ID.csv', index=False)

print("Dane zapisano do pliku stacje_w_powiatach_ID.csv")
