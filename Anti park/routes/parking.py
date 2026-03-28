from flask import Blueprint, jsonify, request
from db import query_db, execute_db
from services.navigation import find_shortest_path

bp = Blueprint('parking', __name__)

@bp.route('/map/<int:floor_num>', methods=['GET'])
def get_map(floor_num):
    # Fetch all navigation nodes for the floor (lane + slot nodes)
    nodes = query_db('SELECT * FROM navigation_nodes WHERE node_name LIKE ?', (f'F{floor_num}%',))
    slot_nodes = query_db('SELECT * FROM navigation_nodes WHERE node_name LIKE ?', (f'N_F{floor_num}%',))
    all_nodes = list(nodes) + list(slot_nodes)
    
    node_ids = [n['id'] for n in all_nodes]
    if not node_ids:
        return jsonify({'nodes': [], 'edges': [], 'slots': []})
        
    placeholders = ','.join(['?'] * len(node_ids))
    
    edges = query_db(
        f'SELECT * FROM navigation_edges WHERE from_node_id IN ({placeholders}) AND to_node_id IN ({placeholders})',
        tuple(node_ids + node_ids)
    )
    
    slots = query_db('SELECT * FROM parking_slots WHERE slot_number LIKE ?', (f'F{floor_num}%',))
    
    return jsonify({
        'nodes': [dict(n) for n in all_nodes],
        'edges': [dict(e) for e in edges],
        'slots': [dict(s) for s in slots]
    })

@bp.route('/slots', methods=['GET'])
def get_all_slots():
    slots = query_db('SELECT * FROM parking_slots')
    return jsonify([dict(s) for s in slots])

@bp.route('/navigate/<int:slot_id>', methods=['GET'])
def navigate_to_slot(slot_id):
    """Get shortest path from entry to a specific slot using Dijkstra"""
    slot = query_db('SELECT * FROM parking_slots WHERE id = ?', (slot_id,), one=True)
    if not slot:
        return jsonify({'error': 'Slot not found'}), 404
    
    # Determine which floor this slot is on
    floor_num = slot['slot_number'].split('-')[0].replace('F', '')
    
    entry_node = query_db('SELECT id FROM navigation_nodes WHERE node_name = ?', (f'F{floor_num}_ENTRY',), one=True)
    slot_node = query_db('SELECT id FROM navigation_nodes WHERE linked_slot_id = ?', (slot_id,), one=True)
    
    if not entry_node or not slot_node:
        return jsonify({'path': None})
    
    path = find_shortest_path(entry_node['id'], slot_node['id'])
    return jsonify({'path': path, 'slot': dict(slot)})

@bp.route('/slots/suggest', methods=['GET'])
def suggest_slot():
    is_ev = request.args.get('is_ev', 'false').lower() == 'true'
    floor = request.args.get('floor', '1')
    
    if is_ev:
        slot = query_db(
            'SELECT * FROM parking_slots WHERE status = "AVAILABLE" AND is_ev = 1 AND slot_number LIKE ? LIMIT 1',
            (f'F{floor}%',), one=True
        )
    else:
        slot = query_db(
            'SELECT * FROM parking_slots WHERE status = "AVAILABLE" AND slot_number LIKE ? LIMIT 1',
            (f'F{floor}%',), one=True
        )
        
    if not slot:
        return jsonify({'error': 'No available slots'}), 404
        
    entry_node = query_db('SELECT id FROM navigation_nodes WHERE node_name = ?', (f'F{floor}_ENTRY',), one=True)
    slot_node = query_db('SELECT id FROM navigation_nodes WHERE linked_slot_id = ?', (slot['id'],), one=True)
    
    path = None
    if entry_node and slot_node:
        path = find_shortest_path(entry_node['id'], slot_node['id'])
        
    return jsonify({'slot': dict(slot), 'path': path})

@bp.route('/slots/create', methods=['POST'])
def create_slot():
    """AI-managed slot creation endpoint"""
    data = request.json
    slot_number = data.get('slot_number')
    is_ev = data.get('is_ev', 0)
    x_pos = data.get('x_pos')
    y_pos = data.get('y_pos')
    
    if not slot_number or x_pos is None or y_pos is None:
        return jsonify({'error': 'slot_number, x_pos, and y_pos are required'}), 400
    
    # Check for duplicate
    existing = query_db('SELECT id FROM parking_slots WHERE slot_number = ?', (slot_number,), one=True)
    if existing:
        return jsonify({'error': f'Slot {slot_number} already exists'}), 400
    
    slot_id = execute_db(
        'INSERT INTO parking_slots (slot_number, is_ev, status, x_pos, y_pos) VALUES (?, ?, ?, ?, ?)',
        (slot_number, is_ev, 'AVAILABLE', x_pos, y_pos)
    )
    
    # Create linked navigation node
    node_id = execute_db(
        'INSERT INTO navigation_nodes (node_name, x_pos, y_pos, linked_slot_id) VALUES (?, ?, ?, ?)',
        (f'N_{slot_number}', x_pos, y_pos, slot_id)
    )
    
    # Find nearest lane node to connect to
    nearest_node = query_db('''
        SELECT id, x_pos, y_pos, 
        ((x_pos - ?) * (x_pos - ?) + (y_pos - ?) * (y_pos - ?)) as dist
        FROM navigation_nodes 
        WHERE linked_slot_id IS NULL AND NOT is_entry
        ORDER BY dist LIMIT 1
    ''', (x_pos, x_pos, y_pos, y_pos), one=True)
    
    if nearest_node:
        import math
        dist = math.sqrt((nearest_node['x_pos'] - x_pos)**2 + (nearest_node['y_pos'] - y_pos)**2)
        execute_db('INSERT INTO navigation_edges (from_node_id, to_node_id, weight) VALUES (?, ?, ?)', (nearest_node['id'], node_id, round(dist, 1)))
        execute_db('INSERT INTO navigation_edges (from_node_id, to_node_id, weight) VALUES (?, ?, ?)', (node_id, nearest_node['id'], round(dist, 1)))
    
    return jsonify({'message': f'Slot {slot_number} created successfully', 'slot_id': slot_id})

@bp.route('/slots/delete', methods=['POST'])
def delete_slot():
    """AI-managed slot deletion"""
    data = request.json
    slot_number = data.get('slot_number')
    
    slot = query_db('SELECT id FROM parking_slots WHERE slot_number = ?', (slot_number,), one=True)
    if not slot:
        return jsonify({'error': f'Slot {slot_number} not found'}), 404
    
    # Remove navigation node and edges
    nav_node = query_db('SELECT id FROM navigation_nodes WHERE linked_slot_id = ?', (slot['id'],), one=True)
    if nav_node:
        execute_db('DELETE FROM navigation_edges WHERE from_node_id = ? OR to_node_id = ?', (nav_node['id'], nav_node['id']))
        execute_db('DELETE FROM navigation_nodes WHERE id = ?', (nav_node['id'],))
    
    execute_db('DELETE FROM parking_slots WHERE id = ?', (slot['id'],))
    
    return jsonify({'message': f'Slot {slot_number} deleted successfully'})
