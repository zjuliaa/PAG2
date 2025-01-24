import json
from pyproj import Transformer
from pymongo import MongoClient
import os

def convert_coordinates(coords, transformer, geom_type):
    if geom_type == "Point":
        return transformer.transform(coords[1], coords[0])[::-1]  # Reverse order for GeoJSON [lon, lat]
    elif geom_type == "LineString" or geom_type == "MultiPoint":
        return [transformer.transform(coord[1], coord[0])[::-1] for coord in coords]
    elif geom_type == "Polygon" or geom_type == "MultiLineString":
        return [[transformer.transform(coord[1], coord[0])[::-1] for coord in ring] for ring in coords]
    elif geom_type == "MultiPolygon":
        return [[[transformer.transform(coord[1], coord[0])[::-1] for coord in ring] for ring in polygon] for polygon in coords]
    else:
        raise ValueError(f"Unsupported geometry type: {geom_type}")

def reproject_geojson(input_path, output_path):
    transformer = Transformer.from_crs("EPSG:2180", "EPSG:4326", always_xy=True)

    try:
        with open(input_path, 'r', encoding='utf-8') as file:  # You can try 'latin1' or 'cp1252' if 'utf-8' doesn't work
            data = json.load(file)

        for feature in data.get("features", []):
            geom = feature["geometry"]
            geom["coordinates"] = convert_coordinates(geom["coordinates"], transformer, geom["type"])

        with open(output_path, 'w', encoding='utf-8') as file:  # Save with UTF-8 encoding
            json.dump(data, file, indent=4)

        print(f"Reprojected GeoJSON saved to {output_path}")
    except UnicodeDecodeError as e:
        print(f"UnicodeDecodeError: {e}. Try changing the file encoding to 'latin1' or 'cp1252'.")
    except Exception as e:
        print(f"An error occurred: {e}")

def connect_to_mongo(uri):
    try:
        client = MongoClient(uri)
        print("Connected to MongoDB Atlas")
        return client
    except Exception as e:
        print("Failed to connect to MongoDB:", e)
        return None

def upload_geojson_to_mongo(client, database_name, collection_name, geojson_file_path):
    if not os.path.exists(geojson_file_path):
        print(f"File not found: {geojson_file_path}")
        return

    try:
        # Load GeoJSON data from file
        with open(geojson_file_path, 'r') as file:
            geojson_data = json.load(file)

        # Ensure data is in the correct format
        if 'features' in geojson_data and isinstance(geojson_data['features'], list):
            documents = geojson_data['features']
        else:
            print("Invalid GeoJSON format: 'features' key is missing or not a list.")
            return

        # Select the database and collection
        db = client[database_name]
        collection = db[collection_name]

        # Insert GeoJSON data into the collection
        result = collection.insert_many(documents)
        print(f"Inserted {len(result.inserted_ids)} GeoJSON documents into collection '{collection_name}' in database '{database_name}'")

        # Create a 2D sphere index for geospatial queries
        collection.create_index([("geometry", "2dsphere")])
        print("2D sphere index created on 'geometry' field.")

    except Exception as e:
        print("Error uploading GeoJSON to MongoDB:", e)
        
def find_documents_by_name(client, database_name, collection_name, name_value):
    try:
        # Select the database and collection
        db = client[database_name]
        collection = db[collection_name]

        # Query the collection to find documents where 'name1' equals 'name_value'
        query = {"properties.name1": name_value}  # Assuming 'name1' is a property in the GeoJSON data
        documents = collection.find(query)

        # Print matching documents
        for doc in documents:
            print(doc)

    except Exception as e:
        print(f"Error finding documents: {e}")

if __name__ == "__main__":
    # Replace the following with your MongoDB Atlas connection string
    MONGO_URI = "mongodb+srv://GKaim:Snoopy1929@pagcluster2.l06nj.mongodb.net/pagcluster2?retryWrites=true&w=majority&tls=true" #<database>?retryWrites=true&w=majority

    # Connect to MongoDB
    client = connect_to_mongo(MONGO_URI)

    if client:
        # Define the database and collection
        database_name = "PAGCluster2"
        collection_name = "effacility"

        find_documents_by_name(client, database_name, collection_name, "Krzyżanowice")

        client.close()
