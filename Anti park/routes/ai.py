import urllib.request
import json
import ssl
from flask import Blueprint, jsonify, request
from config import Config
from db import query_db, execute_db

bp = Blueprint('ai', __name__)

@bp.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')
    user_msg_lower = user_message.lower().strip()
    
    api_key = Config.GEMINI_API_KEY
    
    # Provide system context
    available_ev = query_db('SELECT COUNT(*) as c FROM parking_slots WHERE status = "AVAILABLE" AND is_ev = 1', one=True)['c']
    available_non = query_db('SELECT COUNT(*) as c FROM parking_slots WHERE status = "AVAILABLE" AND is_ev = 0', one=True)['c']
    total_slots = query_db('SELECT COUNT(*) as c FROM parking_slots', one=True)['c']
    occupied = query_db('SELECT COUNT(*) as c FROM parking_slots WHERE status = "OCCUPIED"', one=True)['c']
    
    # ---- SLOT BUILDING COMMANDS (intercepted locally) ----
    # Users can say: "add slot F1-P300 at 500 600 ev" or "create slot F1-NEW1 at 1000 1500"
    if any(kw in user_msg_lower for kw in ['add slot', 'create slot', 'build slot', 'new slot']):
        return handle_slot_creation(user_message)
    
    if any(kw in user_msg_lower for kw in ['delete slot', 'remove slot']):
        return handle_slot_deletion(user_message)
    
    if any(kw in user_msg_lower for kw in ['list slots', 'show slots', 'how many slots']):
        return jsonify({'reply': f'📊 Current Status:\n• Total Slots: {total_slots}\n• Available: {available_ev + available_non} ({available_ev} EV, {available_non} Standard)\n• Occupied: {occupied}\n\nYou can ask me to "add slot F1-P301 at 1500 800 ev" to create a new slot!'})
    
    # ---- QUICK ANSWERS ----
    if "ev slot" in user_msg_lower and "find" in user_msg_lower:
        if available_ev > 0:
            return jsonify({'reply': f'⚡ There are {available_ev} EV charging slots available right now. Click any blue-bordered slot on the map to book one, or I can suggest the nearest one.'})
        else:
            return jsonify({'reply': '😔 Sorry, all EV charging slots are currently occupied. Try checking Floor 2 or wait for one to free up.'})
            
    if "price" in user_msg_lower or "cost" in user_msg_lower or "rate" in user_msg_lower:
        return jsonify({'reply': '💰 EVNPARK Pricing (INR):\n\n• Standard: ₹20/hr\n• EV Charging: ₹30/hr\n• Peak Hours (9-11AM, 5-8PM): ₹50/hr\n• Night (10PM-6AM): ₹10/hr\n\nPrices are calculated dynamically based on your booking time.'})
    
    if "help" in user_msg_lower or "what can you do" in user_msg_lower:
        return jsonify({'reply': '🤖 I can help you with:\n\n1. **Find slots** — "Find EV slot"\n2. **Check prices** — "What are the rates?"\n3. **Build slots** — "Add slot F1-NEW1 at 1500 800 ev"\n4. **Delete slots** — "Delete slot F1-NEW1"\n5. **Slot stats** — "How many slots?"\n6. **Best time** — "Best parking time"\n7. **Any question** — I use Gemini AI!\n\nTry asking me anything! 🚀'})
    
    if "best" in user_msg_lower and "time" in user_msg_lower:
        return jsonify({'reply': '🕐 Best times to park at EVNPARK:\n\n• **Cheapest**: 10PM - 6AM (₹10/hr)\n• **Least crowded**: Early morning (6-8AM)\n• **Avoid**: 9-11AM and 5-8PM (peak pricing at ₹50/hr)\n\nRight now there are {0} slots available.'.format(available_ev + available_non)})
    
    # ---- GEMINI API CALL ----
    system_context = (
        f"You are the AI parking assistant for EVNPARK, a smart EV parking system. "
        f"Current stats: Total slots={total_slots}, Available EV={available_ev}, Available Standard={available_non}, Occupied={occupied}. "
        f"Pricing: Standard ₹20/hr, EV ₹30/hr, Peak ₹50/hr, Night ₹10/hr. "
        f"Users can interact with a visual parking garage map. "
        f"You can help with slot suggestions, pricing info, and general parking queries. "
        f"Keep answers concise and friendly, use emojis. "
        f"If asked to add/create slots, tell them the format: 'add slot F1-NAME at X Y ev' (ev is optional)."
    )
    
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
        payload = {
            "contents": [{
                "parts": [{"text": f"{system_context}\n\nUser message: {user_message}"}]
            }]
        }
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), method='POST')
        req.add_header('Content-Type', 'application/json')
        
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))
            reply = result['candidates'][0]['content']['parts'][0]['text']
            return jsonify({'reply': reply})
            
    except Exception as e:
        print("AI API Error (falling back to mock):", e)
        return jsonify({'reply': f"🤖 EVNPARK Assistant here! We have {available_ev + available_non} slots available ({available_ev} EV). How can I help you park today?\n\n💡 Try: 'Find EV slot', 'What are the rates?', or 'Add slot F1-NEW1 at 1500 800 ev'"})


def handle_slot_creation(message):
    """Parse natural language slot creation: 'add slot F1-P301 at 1500 800 ev'"""
    import re
    
    # Try to parse: slot_name at x y [ev]
    pattern = r'(?:add|create|build|new)\s+slot\s+([\w-]+)\s+at\s+(\d+)\s+(\d+)\s*(ev)?'
    match = re.search(pattern, message, re.IGNORECASE)
    
    if not match:
        return jsonify({'reply': '⚠️ I couldn\'t parse that. Use this format:\n\n**"Add slot F1-P301 at 1500 800 ev"**\n\n• `F1-P301` = slot name\n• `1500 800` = x y position on the map\n• `ev` = optional, marks as EV charging slot'})
    
    slot_number = match.group(1).upper()
    x_pos = float(match.group(2))
    y_pos = float(match.group(3))
    is_ev = 1 if match.group(4) else 0
    
    # Validate position is within garage bounds
    if x_pos < 100 or x_pos > 2900 or y_pos < 100 or y_pos > 2200:
        return jsonify({'reply': f'⚠️ Position ({x_pos}, {y_pos}) is outside the garage boundaries.\n\nValid range: X(100-2900), Y(100-2200)'})
    
    # Check if already exists
    existing = query_db('SELECT id FROM parking_slots WHERE slot_number = ?', (slot_number,), one=True)
    if existing:
        return jsonify({'reply': f'⚠️ Slot **{slot_number}** already exists! Choose a different name.'})
    
    import math
    
    # Create the slot
    slot_id = execute_db(
        'INSERT INTO parking_slots (slot_number, is_ev, status, x_pos, y_pos) VALUES (?, ?, ?, ?, ?)',
        (slot_number, is_ev, 'AVAILABLE', x_pos, y_pos)
    )
    
    # Create navigation node
    node_id = execute_db(
        'INSERT INTO navigation_nodes (node_name, x_pos, y_pos, linked_slot_id) VALUES (?, ?, ?, ?)',
        (f'N_{slot_number}', x_pos, y_pos, slot_id)
    )
    
    # Connect to nearest lane node
    nearest = query_db('''
        SELECT id, x_pos, y_pos,
        ((x_pos - ?) * (x_pos - ?) + (y_pos - ?) * (y_pos - ?)) as dist
        FROM navigation_nodes 
        WHERE linked_slot_id IS NULL AND is_entry = 0
        ORDER BY dist LIMIT 1
    ''', (x_pos, x_pos, y_pos, y_pos), one=True)
    
    if nearest:
        dist = math.sqrt((nearest['x_pos'] - x_pos)**2 + (nearest['y_pos'] - y_pos)**2)
        execute_db('INSERT INTO navigation_edges (from_node_id, to_node_id, weight) VALUES (?, ?, ?)', (nearest['id'], node_id, round(dist, 1)))
        execute_db('INSERT INTO navigation_edges (from_node_id, to_node_id, weight) VALUES (?, ?, ?)', (node_id, nearest['id'], round(dist, 1)))
    
    ev_str = " ⚡ (EV Charging)" if is_ev else ""
    return jsonify({
        'reply': f'✅ Slot **{slot_number}**{ev_str} created successfully!\n\n📍 Position: ({x_pos}, {y_pos})\n🔗 Connected to navigation graph\n\n🔄 Refresh the map to see your new slot.',
        'action': 'reload_map'
    })


def handle_slot_deletion(message):
    """Parse natural language slot deletion: 'delete slot F1-P301'"""
    import re
    
    pattern = r'(?:delete|remove)\s+slot\s+([\w-]+)'
    match = re.search(pattern, message, re.IGNORECASE)
    
    if not match:
        return jsonify({'reply': '⚠️ Use format: **"Delete slot F1-P301"**'})
    
    slot_number = match.group(1).upper()
    
    slot = query_db('SELECT id FROM parking_slots WHERE slot_number = ?', (slot_number,), one=True)
    if not slot:
        return jsonify({'reply': f'❌ Slot **{slot_number}** not found.'})
    
    # Remove navigation links
    nav_node = query_db('SELECT id FROM navigation_nodes WHERE linked_slot_id = ?', (slot['id'],), one=True)
    if nav_node:
        execute_db('DELETE FROM navigation_edges WHERE from_node_id = ? OR to_node_id = ?', (nav_node['id'], nav_node['id']))
        execute_db('DELETE FROM navigation_nodes WHERE id = ?', (nav_node['id'],))
    
    execute_db('DELETE FROM parking_slots WHERE id = ?', (slot['id'],))
    
    return jsonify({
        'reply': f'🗑️ Slot **{slot_number}** has been deleted.\n\n🔄 Refresh the map to see the update.',
        'action': 'reload_map'
    })
