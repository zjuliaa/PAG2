import arcpy
import math 
from queue import PriorityQueue
#ustawienie środowiska i tworzenie kursora, który będzie przechodził przez każdy obiekt warstwy 
arcpy.env.workspace = r"C:\Users\user\Documents\ArcGIS\Projects\Projekt_nawigacja\Projekt_nawigacja.gdb"
cursor=arcpy.SearchCursor("skjz2")

#inicjalizacja list i słowników (lista wierzchołków i krawędzi)
vertices = []
edges = []
vertex_ids = {} 
vertex_counter = 0

for row in cursor:
    #pobranie geometrii i objectid, który służy jako identyfikator linii
    polyline = row.Shape  
    id_jezdni = row.OBJECTID   

    #pobranie punktów początkowych i końcowych i długości
    first_point = polyline.firstPoint
    last_point = polyline.lastPoint
    length=polyline.length

    #zapisanie współrzędnych jako krotki
    start_coords = (first_point.X, first_point.Y)
    end_coords = (last_point.X, last_point.Y)

    #sprawdzenie czy punkt jest już w słowniku, jeśli nie nadanie identyfikatorów i dodanie do słownika wraz z atrybutami
    if start_coords not in vertex_ids:
        vertex_ids[start_coords] = f"V{vertex_counter}"
        vertices.append({"id": vertex_ids[start_coords], "x": first_point.X, "y": first_point.Y, "edge_out": []})
        vertex_counter += 1
    if end_coords not in vertex_ids:
        vertex_ids[end_coords] = f"V{vertex_counter}"
        vertices.append({"id": vertex_ids[end_coords], "x": last_point.X, "y": last_point.Y, "edge_out": []})
        vertex_counter += 1

    #tworzenie krawędzi między wierzchołkami
    edge_id = f"E{id_jezdni}"
    edge = {
        "id": edge_id,
        "id_from": vertex_ids[start_coords],
        "id_to": vertex_ids[end_coords],
        "id_jezdni": id_jezdni,
        "edge_length_field":length
    }
    edges.append(edge)

    #dodanie do każdego wierzchołka identyfikatora krawędzi 
    for vertex in vertices:
        if vertex["id"] == vertex_ids[start_coords]:
            vertex["edge_out"].append(edge_id)
        elif vertex["id"] == vertex_ids[end_coords]:
            vertex["edge_out"].append(edge_id)

#zapisanie krawędzi i wierzchołkoów do pliku tekstowego
with open(r"C:\sem5\PAG\projekt\wierzcholki.txt", "w") as vertices_file:
    for vertex in vertices:
        vertices_file.write(f"{vertex['id']}, {vertex['x']}, {vertex['y']}, {vertex['edge_out']}\n")

with open(r"C:\sem5\PAG\projekt\krawedzie.txt", "w") as edges_file:
    for edge in edges:
        edges_file.write(f"{edge['id']}, {edge['id_from']}, {edge['id_to']}, {edge['id_jezdni']}, {edge['edge_length_field']}\n")




def dijkstra(start_vertex_id, end_vertex_id):
    pq = PriorityQueue()  
    distances = {vertex["id"]: float("inf") for vertex in vertices}  
    predecessors = {vertex["id"]: None for vertex in vertices}  
    visited = set()  
    neighbors_checked_count = 0  

    distances[start_vertex_id] = 0
    pq.put((0, start_vertex_id))

    edge_to_vertex = {}

    while not pq.empty():
        current_distance, current_vertex_id = pq.get()
        if current_vertex_id == end_vertex_id:
            break
        if current_vertex_id in visited:
            continue

        visited.add(current_vertex_id)
        current_vertex = next(v for v in vertices if v["id"] == current_vertex_id)
        
        for edge_id in current_vertex["edge_out"]:
            edge = next(e for e in edges if e["id"] == edge_id)
            neighbor_vertex_id = edge["id_to"] if edge["id_from"] == current_vertex_id else edge["id_from"]
            if neighbor_vertex_id in visited:
                continue
            new_distance = current_distance + edge["edge_length_field"]
            if new_distance < distances[neighbor_vertex_id]:
                distances[neighbor_vertex_id] = new_distance
                predecessors[neighbor_vertex_id] = current_vertex_id
                pq.put((new_distance, neighbor_vertex_id))
                edge_to_vertex[neighbor_vertex_id] = edge["id_jezdni"]  
                neighbors_checked_count += 1

    path = []
    shortest_path_edges = []
    total_distance = distances[end_vertex_id]
    current = end_vertex_id

    while current is not None:
        path.append(current)
        if current in edge_to_vertex:
            shortest_path_edges.append(edge_to_vertex[current])  
        current = predecessors[current]
    path = path[::-1]

    if distances[end_vertex_id] == float("inf"):
        print("No path found.")
    else:
        print("Shortest path dijkstra:", " -> ".join(path))
        print("Path length dijkstra:", total_distance)
        print("Vertices in S astar:", len(visited))
        print("Neighbors checked astar:", neighbors_checked_count)
    
    return shortest_path_edges  


start_vertex_id = "V1"  
end_vertex_id = "V20"  
shortest_path_edges = dijkstra(start_vertex_id, end_vertex_id)
print(shortest_path_edges)


arcpy.AddField_management("skjz2", "jest_czescia_trasy", "SHORT")
with arcpy.da.UpdateCursor("skjz2", ["OBJECTID", "jest_czescia_trasy"]) as update_cursor:
    for row in update_cursor:
        if row[0] in shortest_path_edges:  
            row[1] = 1  
        else:
            row[1] = 0  
        update_cursor.updateRow(row)
