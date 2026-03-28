from flask import Blueprint, jsonify, request, session
from datetime import datetime, timedelta
from db import get_db, execute_db, query_db
from services.pricing import calculate_price

bp = Blueprint('booking', __name__)

@bp.route('/estimate', methods=['POST'])
def estimate_price():
    data = request.json
    slot_id = data.get('slot_id')
    hours = int(data.get('hours', 1))
    
    slot = query_db('SELECT is_ev FROM parking_slots WHERE id = ?', (slot_id,), one=True)
    if not slot:
        return jsonify({'error': 'Slot not found'}), 404
        
    start_time = datetime.now()
    end_time = start_time + timedelta(hours=hours)
    
    price = calculate_price(slot['is_ev'], start_time, end_time)
    return jsonify({'estimated_price': price, 'currency': 'INR', 'symbol': '₹'})

@bp.route('/create', methods=['POST'])
def create_booking():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
        
    data = request.json
    slot_id = data.get('slot_id')
    hours = int(data.get('hours', 1))
    
    slot = query_db('SELECT * FROM parking_slots WHERE id = ? AND status = "AVAILABLE"', (slot_id,), one=True)
    if not slot:
        return jsonify({'error': 'Slot is not available'}), 400
        
    start_time = datetime.now()
    end_time = start_time + timedelta(hours=hours)
    
    price = calculate_price(slot['is_ev'], start_time, end_time)
    
    db = get_db()
    cur = db.cursor()
    try:
        cur.execute('INSERT INTO bookings (user_id, slot_id, end_time, estimated_price) VALUES (?, ?, ?, ?)',
                    (session['user_id'], slot_id, end_time, price))
        booking_id = cur.lastrowid
        cur.execute('UPDATE parking_slots SET status = "OCCUPIED" WHERE id = ?', (slot_id,))
        cur.execute('INSERT INTO payments (booking_id, amount) VALUES (?, ?)', (booking_id, price))
        db.commit()
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
        
    return jsonify({'message': 'Booking successful', 'booking_id': booking_id, 'price': price})

@bp.route('/history', methods=['GET'])
def get_history():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
        
    user_id = session['user_id']
    bookings = query_db('''
        SELECT b.*, p.slot_number, pay.status as payment_status 
        FROM bookings b 
        JOIN parking_slots p ON b.slot_id = p.id 
        LEFT JOIN payments pay ON pay.booking_id = b.id
        WHERE b.user_id = ? ORDER BY b.start_time DESC
    ''', (user_id,))
    
    return jsonify([dict(b) for b in bookings])
