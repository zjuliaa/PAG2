import pandas as pd
import redis


redis_url = "redis://default:b90uh2i9DzbUmGHB4E9aZsqApdUiWkcb@redis-19957.c300.eu-central-1-1.ec2.redns.redis-cloud.com:19957"


try:
    redis_client = redis.StrictRedis.from_url(redis_url, decode_responses=True)

    # Test połączenia
    redis_client.set("test_key", "test_value")
    value = redis_client.get("test_key")
    print(f"Wartość testowa: {value}")
except Exception as e:
    print(f"Błąd połączenia z Redis: {e}")
    exit()

# Ścieżka do pliku CSV z danymi o powiatach i stacjach
file_path_powiaty = r"C:\sem5\PAG\projekt2\stacje_w_powiatach_ID.csv"

try:
    df_powiaty = pd.read_csv(file_path_powiaty, sep=',', names=["Powiat", "Stacje"])
    for _, row in df_powiaty.iterrows():
        powiat_key = f"powiat:{row['Powiat']}"
        stacje = row['Stacje'].split(',')  
        redis_client.hset(powiat_key, "Stacje", ",".join(stacje))

    print(f"Pomyślnie przetworzono plik powiatów: {file_path_powiaty}")

except Exception as e:
    print(f"Błąd przy przetwarzaniu pliku powiatów: {e}")
