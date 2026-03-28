from db import get_db, execute_db, query_db
import random
import math

def seed_database():
    db = get_db()
    
    # Check if already seeded
    user = query_db('SELECT id FROM users LIMIT 1', one=True)
    if user:
        return
        
    print("Seeding database...")
    
    from werkzeug.security import generate_password_hash
    admin_pw = generate_password_hash('admin123')
    user_pw = generate_password_hash('user123')
    
    execute_db('INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)', ('admin', admin_pw, 1))
    execute_db('INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)', ('user', user_pw, 0))
    
    # =====================================================
    # REALISTIC PARKING GARAGE BLUEPRINT - Like the reference image
    # Large scale: 3000x2400 SVG units
    # Layout: Rectangular garage with:
    #   - Perimeter slots (top, bottom, left, right walls)
    #   - Central driving lane (U-shape / loop)
    #   - Interior double rows of slots
    #   - Entry/Exit at bottom-left
    # =====================================================
    
    def generate_realistic_floor(floor_num):
        # Garage boundary
        GARAGE_LEFT = 100
        GARAGE_TOP = 100
        GARAGE_RIGHT = 2900
        GARAGE_BOTTOM = 2200
        GARAGE_W = GARAGE_RIGHT - GARAGE_LEFT
        GARAGE_H = GARAGE_BOTTOM - GARAGE_TOP
        
        SLOT_W = 70   # width of a parking slot
        SLOT_H = 120  # depth of a parking slot
        SLOT_GAP = 8  # gap between slots
        
        slot_counter = 1
        
        # Entry point (bottom-left corner)
        entry_x = GARAGE_LEFT + 150
        entry_y = GARAGE_BOTTOM + 80
        entry_id = execute_db(
            'INSERT INTO navigation_nodes (node_name, x_pos, y_pos, is_entry) VALUES (?, ?, ?, ?)',
            (f'F{floor_num}_ENTRY', entry_x, entry_y, 1)
        )
        
        # Exit point (bottom-right corner)
        exit_x = GARAGE_RIGHT - 150
        exit_y = GARAGE_BOTTOM + 80
        exit_id = execute_db(
            'INSERT INTO navigation_nodes (node_name, x_pos, y_pos, is_entry) VALUES (?, ?, ?, ?)',
            (f'F{floor_num}_EXIT', exit_x, exit_y, 1)
        )
        
        # ---- Create driving lane waypoints (U-shape loop) ----
        # The main driving lane forms a rectangular loop inside the garage perimeter
        LANE_MARGIN = 180  # distance from garage wall
        
        lane_points = [
            # Bottom-left (near entry)
            (GARAGE_LEFT + LANE_MARGIN, GARAGE_BOTTOM - LANE_MARGIN),
            # Top-left
            (GARAGE_LEFT + LANE_MARGIN, GARAGE_TOP + LANE_MARGIN),
            # Top-right
            (GARAGE_RIGHT - LANE_MARGIN, GARAGE_TOP + LANE_MARGIN),
            # Bottom-right (near exit)
            (GARAGE_RIGHT - LANE_MARGIN, GARAGE_BOTTOM - LANE_MARGIN),
        ]
        
        # Also add center aisle lane points (vertical center lanes)
        center_x1 = GARAGE_LEFT + GARAGE_W * 0.35
        center_x2 = GARAGE_LEFT + GARAGE_W * 0.65
        
        center_lane_top = GARAGE_TOP + LANE_MARGIN
        center_lane_bot = GARAGE_BOTTOM - LANE_MARGIN
        
        # Create all lane waypoint nodes
        lane_node_ids = []
        
        # Outer loop nodes (corners + intermediate points)
        outer_loop_points = []
        
        # Bottom edge lane (left to right)
        for i in range(8):
            x = GARAGE_LEFT + LANE_MARGIN + i * ((GARAGE_W - 2 * LANE_MARGIN) / 7)
            y = GARAGE_BOTTOM - LANE_MARGIN
            outer_loop_points.append((x, y))
        
        # Right edge lane (bottom to top)
        for i in range(1, 7):
            x = GARAGE_RIGHT - LANE_MARGIN
            y = GARAGE_BOTTOM - LANE_MARGIN - i * ((GARAGE_H - 2 * LANE_MARGIN) / 6)
            outer_loop_points.append((x, y))
        
        # Top edge lane (right to left)
        for i in range(1, 8):
            x = GARAGE_RIGHT - LANE_MARGIN - i * ((GARAGE_W - 2 * LANE_MARGIN) / 7)
            y = GARAGE_TOP + LANE_MARGIN
            outer_loop_points.append((x, y))
        
        # Left edge lane (top to bottom)
        for i in range(1, 6):
            x = GARAGE_LEFT + LANE_MARGIN
            y = GARAGE_TOP + LANE_MARGIN + i * ((GARAGE_H - 2 * LANE_MARGIN) / 6)
            outer_loop_points.append((x, y))
        
        # Insert all outer loop nodes
        for idx, (px, py) in enumerate(outer_loop_points):
            nid = execute_db(
                'INSERT INTO navigation_nodes (node_name, x_pos, y_pos) VALUES (?, ?, ?)',
                (f'F{floor_num}_LANE_{idx}', round(px, 1), round(py, 1))
            )
            lane_node_ids.append(nid)
        
        # Connect outer loop sequentially (circular)
        for i in range(len(lane_node_ids)):
            next_i = (i + 1) % len(lane_node_ids)
            n1 = lane_node_ids[i]
            n2 = lane_node_ids[next_i]
            p1 = outer_loop_points[i]
            p2 = outer_loop_points[next_i]
            dist = math.sqrt((p2[0]-p1[0])**2 + (p2[1]-p1[1])**2)
            execute_db('INSERT INTO navigation_edges (from_node_id, to_node_id, weight) VALUES (?, ?, ?)', (n1, n2, round(dist, 1)))
            execute_db('INSERT INTO navigation_edges (from_node_id, to_node_id, weight) VALUES (?, ?, ?)', (n2, n1, round(dist, 1)))
        
        # Connect entry to nearest lane node (bottom-left)
        execute_db('INSERT INTO navigation_edges (from_node_id, to_node_id, weight) VALUES (?, ?, ?)', (entry_id, lane_node_ids[0], 100))
        execute_db('INSERT INTO navigation_edges (from_node_id, to_node_id, weight) VALUES (?, ?, ?)', (lane_node_ids[0], entry_id, 100))
        
        # Connect exit to nearest lane node (bottom-right)
        execute_db('INSERT INTO navigation_edges (from_node_id, to_node_id, weight) VALUES (?, ?, ?)', (exit_id, lane_node_ids[7], 100))
        execute_db('INSERT INTO navigation_edges (from_node_id, to_node_id, weight) VALUES (?, ?, ?)', (lane_node_ids[7], exit_id, 100))
        
        # Add center vertical aisle lane nodes
        center_aisle_nodes_1 = []
        center_aisle_nodes_2 = []
        for i in range(7):
            y = GARAGE_TOP + LANE_MARGIN + i * ((GARAGE_H - 2 * LANE_MARGIN) / 6)
            
            nid1 = execute_db(
                'INSERT INTO navigation_nodes (node_name, x_pos, y_pos) VALUES (?, ?, ?)',
                (f'F{floor_num}_CLANE1_{i}', round(center_x1, 1), round(y, 1))
            )
            center_aisle_nodes_1.append(nid1)
            
            nid2 = execute_db(
                'INSERT INTO navigation_nodes (node_name, x_pos, y_pos) VALUES (?, ?, ?)',
                (f'F{floor_num}_CLANE2_{i}', round(center_x2, 1), round(y, 1))
            )
            center_aisle_nodes_2.append(nid2)
        
        # Connect center vertical aisles
        for i in range(6):
            for lst in [center_aisle_nodes_1, center_aisle_nodes_2]:
                dist = (GARAGE_H - 2 * LANE_MARGIN) / 6
                execute_db('INSERT INTO navigation_edges (from_node_id, to_node_id, weight) VALUES (?, ?, ?)', (lst[i], lst[i+1], round(dist, 1)))
                execute_db('INSERT INTO navigation_edges (from_node_id, to_node_id, weight) VALUES (?, ?, ?)', (lst[i+1], lst[i], round(dist, 1)))
        
        # Connect center aisles to outer loop at top and bottom
        # Top connections
        top_lane_center = lane_node_ids[len(lane_node_ids) - 8 + 3]  # approximate
        bot_lane_center1 = lane_node_ids[2]  # approximate
        bot_lane_center2 = lane_node_ids[5]
        
        execute_db('INSERT INTO navigation_edges (from_node_id, to_node_id, weight) VALUES (?, ?, ?)', (center_aisle_nodes_1[0], lane_node_ids[17], 100))
        execute_db('INSERT INTO navigation_edges (from_node_id, to_node_id, weight) VALUES (?, ?, ?)', (lane_node_ids[17], center_aisle_nodes_1[0], 100))
        execute_db('INSERT INTO navigation_edges (from_node_id, to_node_id, weight) VALUES (?, ?, ?)', (center_aisle_nodes_1[-1], lane_node_ids[2], 100))
        execute_db('INSERT INTO navigation_edges (from_node_id, to_node_id, weight) VALUES (?, ?, ?)', (lane_node_ids[2], center_aisle_nodes_1[-1], 100))
        
        execute_db('INSERT INTO navigation_edges (from_node_id, to_node_id, weight) VALUES (?, ?, ?)', (center_aisle_nodes_2[0], lane_node_ids[15], 100))
        execute_db('INSERT INTO navigation_edges (from_node_id, to_node_id, weight) VALUES (?, ?, ?)', (lane_node_ids[15], center_aisle_nodes_2[0], 100))
        execute_db('INSERT INTO navigation_edges (from_node_id, to_node_id, weight) VALUES (?, ?, ?)', (center_aisle_nodes_2[-1], lane_node_ids[5], 100))
        execute_db('INSERT INTO navigation_edges (from_node_id, to_node_id, weight) VALUES (?, ?, ?)', (lane_node_ids[5], center_aisle_nodes_2[-1], 100))
        
        # Cross connections between center aisles
        for i in range(7):
            dist = abs(center_x2 - center_x1)
            execute_db('INSERT INTO navigation_edges (from_node_id, to_node_id, weight) VALUES (?, ?, ?)', (center_aisle_nodes_1[i], center_aisle_nodes_2[i], round(dist, 1)))
            execute_db('INSERT INTO navigation_edges (from_node_id, to_node_id, weight) VALUES (?, ?, ?)', (center_aisle_nodes_2[i], center_aisle_nodes_1[i], round(dist, 1)))
        
        # ======================================================
        # CREATE PARKING SLOTS along the walls and center aisles
        # ======================================================
        
        def create_slot(sx, sy, angle, is_ev, nearest_lane_node_id):
            nonlocal slot_counter
            slot_id = execute_db(
                'INSERT INTO parking_slots (slot_number, is_ev, status, x_pos, y_pos) VALUES (?, ?, ?, ?, ?)',
                (f'F{floor_num}-P{slot_counter:03d}', is_ev, 'AVAILABLE', round(sx, 1), round(sy, 1))
            )
            slot_node = execute_db(
                'INSERT INTO navigation_nodes (node_name, x_pos, y_pos, linked_slot_id) VALUES (?, ?, ?, ?)',
                (f'N_F{floor_num}_{slot_counter}', round(sx, 1), round(sy, 1), slot_id)
            )
            execute_db('INSERT INTO navigation_edges (from_node_id, to_node_id, weight) VALUES (?, ?, ?)', (nearest_lane_node_id, slot_node, 30))
            execute_db('INSERT INTO navigation_edges (from_node_id, to_node_id, weight) VALUES (?, ?, ?)', (slot_node, nearest_lane_node_id, 30))
            slot_counter += 1
            return slot_id
        
        # --- TOP WALL SLOTS (facing down) ---
        num_top = 30
        for i in range(num_top):
            sx = GARAGE_LEFT + 120 + i * (SLOT_W + SLOT_GAP)
            sy = GARAGE_TOP + 30
            is_ev = 1 if random.random() < 0.2 else 0
            # Find nearest top lane node
            nearest = min(range(14, 21), key=lambda idx: abs(outer_loop_points[idx][0] - sx) if idx < len(outer_loop_points) else 9999)
            create_slot(sx, sy, 0, is_ev, lane_node_ids[min(nearest, len(lane_node_ids)-1)])
        
        # --- BOTTOM WALL SLOTS (facing up) ---
        num_bot = 30
        for i in range(num_bot):
            sx = GARAGE_LEFT + 120 + i * (SLOT_W + SLOT_GAP)
            sy = GARAGE_BOTTOM - 30
            is_ev = 1 if random.random() < 0.2 else 0
            nearest = min(range(0, 8), key=lambda idx: abs(outer_loop_points[idx][0] - sx))
            create_slot(sx, sy, 180, is_ev, lane_node_ids[nearest])
        
        # --- LEFT WALL SLOTS (facing right) ---
        num_left = 20
        for i in range(num_left):
            sx = GARAGE_LEFT + 30
            sy = GARAGE_TOP + 200 + i * (SLOT_W + SLOT_GAP)
            is_ev = 1 if random.random() < 0.15 else 0
            nearest = min(range(21, len(lane_node_ids)), key=lambda idx: abs(outer_loop_points[idx][1] - sy) if idx < len(outer_loop_points) else 9999)
            create_slot(sx, sy, 90, is_ev, lane_node_ids[min(nearest, len(lane_node_ids)-1)])
        
        # --- RIGHT WALL SLOTS (facing left) ---
        num_right = 20
        for i in range(num_right):
            sx = GARAGE_RIGHT - 30
            sy = GARAGE_TOP + 200 + i * (SLOT_W + SLOT_GAP)
            is_ev = 1 if random.random() < 0.15 else 0
            nearest = min(range(8, 14), key=lambda idx: abs(outer_loop_points[idx][1] - sy) if idx < len(outer_loop_points) else 9999)
            create_slot(sx, sy, 270, is_ev, lane_node_ids[min(nearest, len(lane_node_ids)-1)])
        
        # --- CENTER AISLE SLOTS (both sides of each center lane) ---
        # Left center aisle - slots on both sides
        num_center = 20
        for i in range(num_center):
            sy = GARAGE_TOP + LANE_MARGIN + 60 + i * (SLOT_W + SLOT_GAP)
            is_ev = 1 if random.random() < 0.25 else 0
            # Left side of center aisle 1
            sx_l = center_x1 - 80
            nearest = min(range(7), key=lambda idx: abs((GARAGE_TOP + LANE_MARGIN + idx * ((GARAGE_H - 2 * LANE_MARGIN) / 6)) - sy))
            create_slot(sx_l, sy, 90, is_ev, center_aisle_nodes_1[nearest])
            
            # Right side of center aisle 1
            sx_r = center_x1 + 80
            create_slot(sx_r, sy, 270, is_ev, center_aisle_nodes_1[nearest])
        
        # Right center aisle - slots on both sides
        for i in range(num_center):
            sy = GARAGE_TOP + LANE_MARGIN + 60 + i * (SLOT_W + SLOT_GAP)
            is_ev = 1 if random.random() < 0.25 else 0
            sx_l = center_x2 - 80
            nearest = min(range(7), key=lambda idx: abs((GARAGE_TOP + LANE_MARGIN + idx * ((GARAGE_H - 2 * LANE_MARGIN) / 6)) - sy))
            create_slot(sx_l, sy, 90, is_ev, center_aisle_nodes_2[nearest])
            
            sx_r = center_x2 + 80
            create_slot(sx_r, sy, 270, is_ev, center_aisle_nodes_2[nearest])
        
        print(f"Floor {floor_num}: Created {slot_counter - 1} slots")
        return slot_counter - 1
    
    total = 0
    total += generate_realistic_floor(1)
    total += generate_realistic_floor(2)
    
    print(f"Database seeded with {total} total slots and navigation graph.")
