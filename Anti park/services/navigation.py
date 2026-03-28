import heapq
from db import query_db

def get_graph():
    nodes = query_db('SELECT * FROM navigation_nodes')
    edges = query_db('SELECT * FROM navigation_edges')
    
    graph = {node['id']: [] for node in nodes}
    for edge in edges:
        graph[edge['from_node_id']].append({
            'to': edge['to_node_id'],
            'weight': edge['weight']
        })
    return graph

def find_shortest_path(start_node_id, end_node_id):
    """ Dijkstra's pathfinding algorithm """
    graph = get_graph()
    
    if start_node_id not in graph or end_node_id not in graph:
        return None
        
    distances = {node: float('inf') for node in graph}
    distances[start_node_id] = 0
    previous_nodes = {node: None for node in graph}
    pq = [(0, start_node_id)]
    
    while pq:
        current_distance, current_node = heapq.heappop(pq)
        
        if current_node == end_node_id:
            break
            
        if current_distance > distances[current_node]:
            continue
            
        for neighbor in graph[current_node]:
            neighbor_id = neighbor['to']
            weight = neighbor['weight']
            distance = current_distance + weight
            
            if distance < distances[neighbor_id]:
                distances[neighbor_id] = distance
                previous_nodes[neighbor_id] = current_node
                heapq.heappush(pq, (distance, neighbor_id))
                
    path = []
    current = end_node_id
    while current is not None:
        path.append(current)
        current = previous_nodes[current]
        
    path.reverse()
    
    if path[0] == start_node_id:
        # Fetch node coordinates
        coords = []
        for i in path:
            node = query_db('SELECT x_pos, y_pos FROM navigation_nodes WHERE id = ?', (i,), one=True)
            if node:
                coords.append({'x': node['x_pos'], 'y': node['y_pos']})
        return coords
    
    return None
