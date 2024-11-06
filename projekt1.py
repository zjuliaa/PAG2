import arcpy
import math 
#ustawienie środowiska i tworzenie kursora, który będzie przechodził przez każdy obiekt warstwy 
arcpy.env.workspace = r"C:\Sem5\PAG2\MyProject\MyProject.gdb"
cursor=arcpy.SearchCursor("skjz1_ExportFeatures")

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
with open(r"C:\Sem5\PAG2\projekt\wierzcholki.txt", "w") as vertices_file:
    for vertex in vertices:
        vertices_file.write(f"{vertex['id']}, {vertex['x']}, {vertex['y']}, {vertex['edge_out']}\n")

with open(r"C:\Sem5\PAG2\projekt\krawedzie.txt", "w") as edges_file:
    for edge in edges:
        edges_file.write(f"{edge['id']}, {edge['id_from']}, {edge['id_to']}, {edge['id_jezdni']}, {edge['edge_length_field']}\n")

def dijkstra(vertices, edges, start_vertex, end_vertex):
    # Inicjalizacja zbiorów i struktur danych
    S = set()  # Zbiór przetworzonych wierzchołków
    Q = {start_vertex}  # Zbiór wierzchołków do przetworzenia, zaczynamy od wierzchołka startowego
    d = {v['id']: math.inf for v in vertices}  # Długości ścieżek, na początku nieskończoność dla każdego wierzchołka
    p = {v['id']: None for v in vertices}  # Poprzednicy na najkrótszej ścieżce

    # Dla wierzchołka startowego ustalamy odległość na 0
    d[start_vertex] = 0
    liczba_przejrzanych_sasiadow = 0  # Licznik sąsiadów przeglądanych przez algorytm

    while Q:
        # Znalezienie wierzchołka v w Q o najmniejszym d[v]
        v = min(Q, key=lambda vertex: d[vertex])
        Q.remove(v)

        # Jeśli znaleźliśmy wierzchołek końcowy, przerywamy pętlę
        if v == end_vertex:
            break

        # Przetwarzanie sąsiadów wierzchołka v
        for edge in edges:
            if edge['id_from'] == v:
                u = edge['id_to']
                liczba_przejrzanych_sasiadow += 1  # Zliczanie sąsiadów
                
                if u in S:
                    continue

                # Oblicz nową potencjalną długość ścieżki do u przez v
                new_distance = d[v] + edge['edge_length_field']
                
                # Jeśli znaleźliśmy krótszą ścieżkę do u, aktualizujemy d[u] i p[u]
                if new_distance < d[u]:
                    d[u] = new_distance
                    p[u] = v  # Poprzednik wierzchołka u to v

                # Dodaj u do Q, jeśli jeszcze go tam nie ma
                if u not in Q:
                    Q.add(u)

        # Dodaj v do zbioru przetworzonych wierzchołków S
        S.add(v)

    # Odtworzenie najkrótszej ścieżki
    path = []
    if d[end_vertex] != math.inf:  # Sprawdzenie, czy ścieżka istnieje
        current = end_vertex
        while current is not None:
            path.insert(0, current)
            current = p[current]
    
    # Wyniki
    if d[end_vertex] == math.inf:
        print("Brak trasy.")
    else:
        print("Najkrótsza trasa:", path)
        print("Długość trasy:", d[end_vertex])
    print("Liczba przetworzonych wierzchołków w zbiorze S:", len(S))
    print("Liczba przejrzanych sąsiadów:", liczba_przejrzanych_sasiadow)

    return path, d[end_vertex], liczba_przejrzanych_sasiadow

path, distance, liczba_przejrzanych_sasiadow = dijkstra(vertices, edges, start_vertex='V0', end_vertex='V5')
