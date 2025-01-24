
import pandas as pd
import redis

redis_url = "redis://default:b90uh2i9DzbUmGHB4E9aZsqApdUiWkcb@redis-19957.c300.eu-central-1-1.ec2.redns.redis-cloud.com:19957"

# Połączenie z Redis
try:
    redis_client = redis.StrictRedis.from_url(redis_url, decode_responses=True)

    # Test połączenia
    redis_client.set("test_key", "test_value")
    value = redis_client.get("test_key")
    print(f"Wartość testowa: {value}")
except Exception as e:
    print(f"Błąd połączenia z Redis: {e}")
    exit()

# Ścieżka do pliku CSV
file_path = r"C:\sem5\PAG\projekt2\kody_stacji.csv"

try:
    df = pd.read_csv(file_path, sep=';', names=["LP.", "ID", "Nazwa", "Rzeka", "Szerokość geograficzna", "Długość geograficzna", "Wysokość n.p.m."], skiprows=1)
    for _, row in df.iterrows():
        redis_key = f"stacja:{row['ID']}"
        redis_client.hset(redis_key, mapping={
            "Nazwa": row['Nazwa'],
            "Rzeka": row['Rzeka'],
            "Szerokość geograficzna": row['Szerokość geograficzna'],
            "Długość geograficzna": row['Długość geograficzna'],
            "Wysokość n.p.m.": row['Wysokość n.p.m.']
        })
    print(f"Pomyślnie przetworzono plik: {file_path}")
except Exception as e:
    print(f"Błąd przy przetwarzaniu pliku {file_path}: {e}")



