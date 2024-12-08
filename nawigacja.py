import arcpy
import math 
from queue import PriorityQueue
from collections import defaultdict

#Ustawienie środowiska pracy
arcpy.env.workspace = r"C:\Users\user\Documents\ArcGIS\Projects\Projekt_nawigacja\Projekt_nawigacja.gdb"

#Inicjalizacja struktur wierzchołków i krawędzi
vertices = {}
edges = {}
vertex_ids = {}
vertex_counter = 1  
edge_counter = 1

#Pobranie geometrii i atrybutów z warstwy dróg
with arcpy.da.SearchCursor("skjz_nowe2", ["OBJECTID", "SHAPE@", "klasaDrogi", "kier_auto"]) as cursor:
    for row in cursor:
        polyline = row[1]
        id_jezdni = row[0]
        klasa = row[2]
        kier_auto = row[3]
        
        first_point = polyline.firstPoint
        last_point = polyline.lastPoint
        length = polyline.length

        start_coords = (first_point.X, first_point.Y)
        end_coords = (last_point.X, last_point.Y)

        #Dodanie wierzchołów do struktury grafu
        if start_coords not in vertex_ids:
            vertex_ids[start_coords] = vertex_counter
            vertices[vertex_counter] = {
                "id": vertex_counter, 
                "x": first_point.X, 
                "y": first_point.Y, 
                "edge_out": {},
                "kier_auto": kier_auto
            }
            vertex_counter += 1

        if end_coords not in vertex_ids:
            vertex_ids[end_coords] = vertex_counter
            vertices[vertex_counter] = {
                "id": vertex_counter, 
                "x": last_point.X, 
                "y": last_point.Y, 
                "edge_out": {},
                "kier_auto": kier_auto

            }
            vertex_counter += 1   

        #Tworzenie krawędzi     
        edge = {
            "id": id_jezdni,
            "id_from": vertex_ids[start_coords],
            "id_to": vertex_ids[end_coords],
            "edge_length_field": length, 
            "klasa_drogi": klasa,
            "kier_auto": kier_auto

        }
        edges[id_jezdni] = edge
        
        start_vertex_id = vertex_ids[start_coords]
        end_vertex_id = vertex_ids[end_coords]

        if kier_auto == 0:  
            edges[f"{id_jezdni}_1"] = {
                "id": id_jezdni,
                "id_from": start_vertex_id,
                "id_to": end_vertex_id,
                "length": length,
                "class": klasa,
                "kier_auto": kier_auto
            }
            edges[f"{id_jezdni}_2"] = {
                "id": id_jezdni,
                "id_from": end_vertex_id,
                "id_to": start_vertex_id,
                "length": length,
                "class": klasa,
                "kier_auto": kier_auto
            }
        elif kier_auto == 1:  
            edges[f"{id_jezdni}"] = {
                "id": id_jezdni,
                "id_from": start_vertex_id,
                "id_to": end_vertex_id,
                "length": length,
                "class": klasa,
                "kier_auto": kier_auto
            }
        elif kier_auto == 2:  
            edges[f"{id_jezdni}"] = {
                "id": id_jezdni,
                "id_from": end_vertex_id,
                "id_to": start_vertex_id,
                "length": length,
                "class": klasa,
                "kier_auto": kier_auto
            }
        elif kier_auto == 3:  
            continue
        vertices[vertex_ids[start_coords]]["edge_out"][id_jezdni] = edge
        vertices[vertex_ids[end_coords]]["edge_out"][id_jezdni] = edge

#Funkcja do sprawdzania kierunku jazdy
def czy_dobry_kierunek(kier_auto, id_from, id_to, current_vertex_id):
    if kier_auto == 0: #Droga dwukierunkowa
        return True
    elif kier_auto == 3:  #Droga wyłączona z ruchu
        return False
    elif kier_auto == 1:  #Droga jednokierunkowana zgodna z geometrią
        return current_vertex_id == id_from  
    elif kier_auto == 2:  #Droga jednokierunkowa przeciwna do geometrii
        return current_vertex_id == id_to  
    else:
        return False  

#Algorytm Dijkstry
def dijkstra(start_vertex_id, end_vertex_id):
    pq = PriorityQueue()
    distances = defaultdict(lambda: float("inf"))
    predecessors = defaultdict(lambda: None)
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
        current_vertex = vertices[current_vertex_id]

        for edge_id in current_vertex["edge_out"]:
            edge = edges[edge_id]
            if edge["id_from"] == current_vertex_id:
                neighbor_vertex_id = edge["id_to"]
            else:
                neighbor_vertex_id = edge["id_from"]
            if not czy_dobry_kierunek(edge["kier_auto"], edge["id_from"], edge["id_to"], current_vertex_id):
                continue
            if neighbor_vertex_id in visited:
                continue
            new_distance = current_distance + edge["edge_length_field"]
            if new_distance < distances[neighbor_vertex_id]:
                distances[neighbor_vertex_id] = new_distance
                predecessors[neighbor_vertex_id] = current_vertex_id
                pq.put((new_distance, neighbor_vertex_id))
                edge_to_vertex[neighbor_vertex_id] = edge["id"]
                neighbors_checked_count += 1
    #Rekonstrukcja ścieżki
    path = []
    shortest_path_edges = []
    current = end_vertex_id
    while current is not None:
        path.append(current)
        if current in edge_to_vertex:
            shortest_path_edges.append(edge_to_vertex[current])
        current = predecessors[current]
    path.reverse()
    if distances[end_vertex_id] == float("inf"):
        print("No path found.")
    else:
        print("Shortest path dijkstra:", " -> ".join(map(str, path)))
        print("Path length dijkstra:", distances[end_vertex_id])
        print("Vertices in S :", len(visited))
        print("Neighbors checked :", neighbors_checked_count)
    return shortest_path_edges

#Wybór startowego i koncowego wierzchołka
start_vertex_id = 3446
end_vertex_id = 4442

#Wywolanie algorytmu Dijkstra
shortest_path_edges = dijkstra(start_vertex_id, end_vertex_id)
print(shortest_path_edges)

def heurystyka(start_vertex_id, end_vertex_id):
    x_start = vertices[start_vertex_id]["x"]
    y_start = vertices[start_vertex_id]["y"]
    x_end = vertices[end_vertex_id]["x"]
    y_end = vertices[end_vertex_id]["y"]
    dist = math.sqrt((x_end-x_start)**2+(y_end-y_start)**2) #Obliczanie odległości euklidesowej
    return dist

#Algorytm A*
def a_star(start_vertex_id, end_vertex_id):
    pq = PriorityQueue() 
    distances = defaultdict(lambda: float("inf"))
    predecessors = defaultdict(lambda: None)
    visited = set() #Odwiedzone wierzchołki
    neighbors_checked_count = 0 #Licznik sprawdzonych sąsiadów
    distances[start_vertex_id] = 0 
    pq.put((0, start_vertex_id)) 
    edge_to_vertex = {} 
    while not pq.empty():
        current_priority, current_vertex_id = pq.get() 
        if current_vertex_id == end_vertex_id:
            break
        if current_vertex_id in visited:
            continue
        visited.add(current_vertex_id)
        current_vertex = vertices[current_vertex_id]
        for edge_id in current_vertex["edge_out"]:
            edge = edges[edge_id]
            neighbor_vertex_id = edge["id_to"] if edge["id_from"] == current_vertex_id else edge["id_from"]
            if not czy_dobry_kierunek(edge["kier_auto"], edge["id_from"], edge["id_to"], current_vertex_id):
                continue
            if neighbor_vertex_id in visited:
                continue
            #Aktualizacja odledgłości o wartość heurystyki
            new_distance = distances[current_vertex_id] + edge["edge_length_field"]
            estimated_distance = new_distance + heurystyka(neighbor_vertex_id, end_vertex_id)
            if new_distance < distances[neighbor_vertex_id]:
                distances[neighbor_vertex_id] = new_distance
                predecessors[neighbor_vertex_id] = current_vertex_id
                pq.put((estimated_distance, neighbor_vertex_id)) 
                edge_to_vertex[neighbor_vertex_id] = edge["id"]
                neighbors_checked_count += 1
    path = []
    shortest_path_edges = []
    current = end_vertex_id
    while current is not None: #Rekonstrukcja ścieżki od końca do początku
        path.append(current)
        if current in edge_to_vertex:
            shortest_path_edges.append(edge_to_vertex[current])
        current = predecessors[current]
    path.reverse()
    if distances[end_vertex_id] == float("inf"):
        print("No path found.")
    else:
        print("Shortest path A*:", " -> ".join(map(str, path)))
        print("Path length A*:", distances[end_vertex_id])
        print("Vertices in S :", len(visited))
        print("Neighbors checked :", neighbors_checked_count)
    return shortest_path_edges

#Wywołanie algorytmu A*
shortest_path_edges1 = a_star(start_vertex_id, end_vertex_id)
print(shortest_path_edges1)

#Algorytm A* z uwzględnieniem predkości
def fastest_a_star(start_vertex_id, end_vertex_id):
    pq = PriorityQueue() 
    distances = defaultdict(lambda: float("inf"))
    predecessors = defaultdict(lambda: None)
    visited = set()
    neighbors_checked_count = 0
    distances[start_vertex_id] = 0 
    pq.put((0, start_vertex_id)) 
    edge_to_vertex = {} 
    travel_times = defaultdict(lambda: float("inf"))  
    travel_times[start_vertex_id] = 0
    while not pq.empty():
        current_priority, current_vertex_id = pq.get() 
        if current_vertex_id == end_vertex_id:
            break
        if current_vertex_id in visited:
            continue
        visited.add(current_vertex_id)
        current_vertex = vertices[current_vertex_id]

        for edge_id in current_vertex["edge_out"]:
            edge = edges[edge_id]
            
            if not czy_dobry_kierunek(edge["kier_auto"], edge["id_from"], edge["id_to"], current_vertex_id):
                continue
            neighbor_vertex_id = edge["id_to"] if edge["id_from"] == current_vertex_id else edge["id_from"]
            if neighbor_vertex_id in visited:
                continue

            edge_length = edge["edge_length_field"]
            if edge["klasa_drogi"] in speed:
                max_speed=speed[edge["klasa_drogi"]]
            else:
                max_speed=speed["G"]
            travel_time = edge_length / max_speed
            new_travel_time = travel_times[current_vertex_id] + travel_time
            estimated_travel_time = new_travel_time + (heurystyka(neighbor_vertex_id, end_vertex_id) / max_speed)
            
            if new_travel_time < travel_times[neighbor_vertex_id]:
                travel_times[neighbor_vertex_id] = new_travel_time
                predecessors[neighbor_vertex_id] = current_vertex_id
                pq.put((estimated_travel_time, neighbor_vertex_id))
                edge_to_vertex[neighbor_vertex_id] = edge["id"]
                neighbors_checked_count += 1                                            

    path = []   
    shortest_path_edges = []
    current = end_vertex_id
    while current is not None:
        path.append(current)    
        if current in edge_to_vertex:
            shortest_path_edges.append(edge_to_vertex[current]) 
        current = predecessors[current]
    path.reverse()  

    if travel_times[end_vertex_id] == float("inf"):    
        print("No path found.")
    else:    
        print("Shortest path A*:", " -> ".join(map(str, path)))
        print("Time A*:", travel_times[end_vertex_id])  
        print("Path length A*:",edge_length)
        print("Vertices in S :", len(visited))
        print("Neighbors checked :", neighbors_checked_count)    
    return shortest_path_edges

speed = {
    "A": 140,  # Autostrada
    "S": 120,
    "GP": 100,  # Droga główna ruchu przyspieszonego
    "G": 80,   # Droga główna
    "Z": 60,   # Droga zbiorcza
    "L": 40,   # Droga lokalna
    "D": 30,   # Droga dojazdowa
    "I": 10    # Droga inna
}

#Wywołanie algorytmu A* z uwzględnieniem predkości
shortest_path_edges2= fastest_a_star(start_vertex_id, end_vertex_id)
print(shortest_path_edges2)

# Dodanie nowego pola i aktualizacja wartości w zależności od wybranego algorytmu
arcpy.AddField_management("skjz_nowe2", "jest_czescia_trasy", "SHORT")
with arcpy.da.UpdateCursor("skjz_nowe2", ["OBJECTID", "jest_czescia_trasy"]) as update_cursor:
    for row in update_cursor:
        if row[0] in shortest_path_edges1:
            row[1] = 1
        elif row[0] in shortest_path_edges2:  
            row[1] = 2
        else:
            row[1] = 0 
        update_cursor.updateRow(row)


##Dodawanie kierunkowości do warstwy dróg
# import math
# import random

# def determine_kier_auto(polyline, threshold=0.05):  # threshold dla losowości '3'
#     first_point = polyline.firstPoint
#     last_point = polyline.lastPoint
#     if random.random() < threshold:
#         return 3  # Droga wyłączona z ruchu
#     delta_x = last_point.X - first_point.X
#     delta_y = last_point.Y - first_point.Y
#     angle = math.atan2(delta_y, delta_x)  # Wartość w radianach
#     if angle >= 0:  # Kąt dodatni - kierunek zgodny z geometrią
#         return 1  
#     else:  # Kąt ujemny - kierunek przeciwny do geometrii
#         return 2  # Jednokierunkowa droga, przeciwnie do geometrii

# def determine_kier_auto_0(polyline, threshold=0.4):
#     # Losowo przypisujemy '0' z określonym prawdopodobieństwem
#     if random.random() < threshold:
#         return 0  # Dwukierunkowa droga
#     else:
#         return determine_kier_auto(polyline)  # W przeciwnym razie, obliczamy zgodnie z geometrią

# # Ścieżka do warstwy
# layer_path = r"C:\Users\user\Documents\ArcGIS\Projects\Projekt_nawigacja\Projekt_nawigacja.gdb\skjz_nowe2"

# new_field = "kier_auto"
# field_names = [field.name for field in arcpy.ListFields(layer_path)]
# if new_field not in field_names:
#     arcpy.AddField_management(layer_path, new_field, "SHORT")  # Typ danych: Liczba całkowita
# with arcpy.da.UpdateCursor(layer_path, ["OBJECTID", "SHAPE@", new_field]) as cursor:
#     for row in cursor:
#         polyline = row[1]  # Geometria krawędzi
#         kier_auto_value = determine_kier_auto_0(polyline)  # Obliczenie kierunku
#         row[2] = kier_auto_value  # Ustaw nową wartość kier_auto
#         cursor.updateRow(row)

# print(f"Kolumna '{new_field}' została utworzona i zaktualizowana.")
