CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    is_admin INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS parking_slots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slot_number TEXT UNIQUE NOT NULL,
    is_ev INTEGER DEFAULT 0,
    status TEXT DEFAULT 'AVAILABLE', -- AVAILABLE, OCCUPIED, RESERVED
    x_pos REAL,
    y_pos REAL
);

CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    slot_id INTEGER,
    start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    end_time DATETIME,
    status TEXT DEFAULT 'ACTIVE', -- ACTIVE, COMPLETED, CANCELLED
    estimated_price REAL,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (slot_id) REFERENCES parking_slots(id)
);

CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_id INTEGER,
    amount REAL,
    status TEXT DEFAULT 'SUCCESS', -- SUCCESS, FAILED
    payment_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (booking_id) REFERENCES bookings(id)
);

CREATE TABLE IF NOT EXISTS navigation_nodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    node_name TEXT UNIQUE NOT NULL,
    x_pos REAL NOT NULL,
    y_pos REAL NOT NULL,
    is_entry INTEGER DEFAULT 0,
    linked_slot_id INTEGER,
    FOREIGN KEY (linked_slot_id) REFERENCES parking_slots(id)
);

CREATE TABLE IF NOT EXISTS navigation_edges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_node_id INTEGER NOT NULL,
    to_node_id INTEGER NOT NULL,
    weight REAL NOT NULL,
    FOREIGN KEY (from_node_id) REFERENCES navigation_nodes(id),
    FOREIGN KEY (to_node_id) REFERENCES navigation_nodes(id)
);


