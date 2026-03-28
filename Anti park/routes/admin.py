from flask import Blueprint, jsonify, session
from db import query_db

bp = Blueprint('admin', __name__)

@bp.route('/stats', methods=['GET'])
def get_stats():
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 401
        
    total_slots = query_db('SELECT COUNT(*) as count FROM parking_slots', one=True)['count']
    occupied_slots = query_db('SELECT COUNT(*) as count FROM parking_slots WHERE status = "OCCUPIED"', one=True)['count']
    revenue = query_db('SELECT SUM(amount) as total FROM payments WHERE status = "SUCCESS"', one=True)['total'] or 0
    
    # Bookings over last 7 days (mock data for charts if DB is too new, but we will return real db agg)
    # Simple aggregated revenue by date
    daily_revenue = query_db('''
        SELECT date(payment_time) as dt, SUM(amount) as total 
        FROM payments 
        GROUP BY date(payment_time) 
        ORDER BY dt DESC LIMIT 7
    ''')
    
    return jsonify({
        'total_slots': total_slots,
        'occupied_slots': occupied_slots,
        'available_slots': total_slots - occupied_slots,
        'revenue': revenue,
        'daily_revenue': [dict(d) for d in daily_revenue]
    })
