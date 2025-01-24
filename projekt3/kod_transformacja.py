from py2neo import Graph, Node, Relationship
import geopandas as gpd
from pyproj import Transformer

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "PAGPAGPAGPAG"

def connect_to_neo4j(uri, user, password):
    try:
        graph = Graph(uri, auth=(user, password))
        result = graph.run("RETURN 'Connection Successful' AS message").data()
        if result:
            print("Połączenie z bazą Neo4j zakończone sukcesem.")
        return graph
    except Exception as e:
        print(f"Nie udało się połączyć z bazą Neo4j. Błąd: {e}")
        return None

def import_shapefile_to_neo4j(shapefile_path, graph):
    if graph is None:
        print("Brak połączenia z bazą Neo4j. Import danych został przerwany.")
        return

    try:
        transformer = Transformer.from_crs("EPSG:2180", "EPSG:4326", always_xy=True)

        gdf = gpd.read_file(shapefile_path)
        print(f"Wczytano plik Shapefile. Liczba rekordów: {len(gdf)}")

        for _, row in gdf.iterrows():
            if row.geometry.geom_type == "LineString":
                coords = list(row.geometry.coords)
                start_coord = coords[0]
                end_coord = coords[-1]

                start_lat, start_lon = transformer.transform(start_coord[0], start_coord[1])
                end_lat, end_lon = transformer.transform(end_coord[0], end_coord[1])

                start_node = Node("Point", x=start_lat, y=start_lon)
                end_node = Node("Point", x=end_lat, y=end_lon)

                graph.merge(start_node, "Point", "x")
                graph.merge(end_node, "Point", "x")

                relationship = Relationship(start_node, "CONNECTS_TO", end_node)
                relationship["length"] = row.geometry.length
                graph.merge(relationship)

        print("Import danych do Neo4j zakończony sukcesem.")
    except Exception as e:
        print(f"Wystąpił błąd podczas importu danych: {e}")

if __name__ == "__main__":
    shapefile_path = "C:\Sem5\PAG2\projket3\skjz\L4_1_BDOT10k__OT_SKJZ_L.shp"  
    graph = connect_to_neo4j(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    import_shapefile_to_neo4j(shapefile_path, graph)

