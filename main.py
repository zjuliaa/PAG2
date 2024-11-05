import arcpy
arcpy.env.workspace = r"C:\Users\user\Documents\ArcGIS\Projects\Projekt_nawigacja\Projekt_nawigacja.gdb"

cursor=arcpy.SearchCursor("skjz1", "OBJECTID<20")


vertices = []
edges = []
vertex_ids = {} 
vertex_counter = 0

for row in cursor:
    polyline = row.Shape  
    id_jezdni = row.OBJECTID   


    first_point = polyline.firstPoint
    last_point = polyline.lastPoint

    length=polyline.length


    start_coords = (first_point.X, first_point.Y)
    end_coords = (last_point.X, last_point.Y)


    if start_coords not in vertex_ids:
        vertex_ids[start_coords] = f"V{vertex_counter}"
        vertices.append({"id": vertex_ids[start_coords], "x": first_point.X, "y": first_point.Y, "edge_out": []})
        vertex_counter += 1

    if end_coords not in vertex_ids:
        vertex_ids[end_coords] = f"V{vertex_counter}"
        vertices.append({"id": vertex_ids[end_coords], "x": last_point.X, "y": last_point.Y, "edge_out": []})
        vertex_counter += 1

    edge_id = f"E{id_jezdni}"
    edge = {
        "id": edge_id,
        "id_from": vertex_ids[start_coords],
        "id_to": vertex_ids[end_coords],
        "id_jezdni": id_jezdni,
        "edge_length_field":length
    }
    edges.append(edge)
    for vertex in vertices:
        if vertex["id"] == vertex_ids[start_coords]:
            vertex["edge_out"].append(edge_id)
        elif vertex["id"] == vertex_ids[end_coords]:
            vertex["edge_out"].append(edge_id)


with open(r"C:\sem5\PAG\projekt\wierzcholki.txt", "w") as vertices_file:
    for vertex in vertices:
        vertices_file.write(f"{vertex['id']}, {vertex['x']}, {vertex['y']}, {vertex['edge_out']}\n")

with open(r"C:\sem5\PAG\projekt\krawedzie.txt", "w") as edges_file:
    for edge in edges:
        edges_file.write(f"{edge['id']}, {edge['id_from']}, {edge['id_to']}, {edge['id_jezdni']}, {edge['edge_length_field']}\n")