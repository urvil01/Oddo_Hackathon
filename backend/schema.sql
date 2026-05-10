-- ============================================================
-- TRAVELOOP - SQLite Database Schema
-- ============================================================

PRAGMA foreign_keys = ON;

-- USERS TABLE
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    avatar TEXT DEFAULT NULL,
    is_verified INTEGER DEFAULT 0,
    otp TEXT DEFAULT NULL,
    otp_expiry TEXT DEFAULT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- TRIPS TABLE
CREATE TABLE IF NOT EXISTS trips (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    cover_image TEXT DEFAULT NULL,
    start_date TEXT,
    end_date TEXT,
    total_budget REAL DEFAULT 0,
    status TEXT DEFAULT 'planning',  -- planning, ongoing, completed
    share_token TEXT UNIQUE DEFAULT NULL,
    is_public INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- TRIP STOPS (Cities/Destinations)
CREATE TABLE IF NOT EXISTS trip_stops (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trip_id INTEGER NOT NULL,
    city TEXT NOT NULL,
    country TEXT NOT NULL,
    arrival_date TEXT,
    departure_date TEXT,
    notes TEXT,
    order_index INTEGER DEFAULT 0,
    lat REAL DEFAULT NULL,
    lng REAL DEFAULT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (trip_id) REFERENCES trips(id) ON DELETE CASCADE
);

-- ACTIVITIES TABLE
CREATE TABLE IF NOT EXISTS activities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT,          -- sightseeing, food, transport, adventure, culture, shopping
    description TEXT,
    estimated_cost REAL DEFAULT 0,
    duration_hours REAL DEFAULT 1,
    city TEXT,
    country TEXT,
    is_custom INTEGER DEFAULT 1
);

-- TRIP ACTIVITIES (Activities linked to a stop)
CREATE TABLE IF NOT EXISTS trip_activities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trip_id INTEGER NOT NULL,
    stop_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    category TEXT,
    date TEXT,
    time TEXT,
    duration_hours REAL DEFAULT 1,
    cost REAL DEFAULT 0,
    notes TEXT,
    is_completed INTEGER DEFAULT 0,
    order_index INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (trip_id) REFERENCES trips(id) ON DELETE CASCADE,
    FOREIGN KEY (stop_id) REFERENCES trip_stops(id) ON DELETE CASCADE
);

-- BUDGET TABLE
CREATE TABLE IF NOT EXISTS budgets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trip_id INTEGER NOT NULL,
    category TEXT NOT NULL,     -- hotels, transport, activities, food, shopping, misc
    amount REAL DEFAULT 0,
    currency TEXT DEFAULT 'INR',
    notes TEXT,
    date TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (trip_id) REFERENCES trips(id) ON DELETE CASCADE
);

-- PACKING CHECKLIST
CREATE TABLE IF NOT EXISTS packing_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trip_id INTEGER NOT NULL,
    category TEXT DEFAULT 'general',   -- clothing, electronics, documents, toiletries, general
    item_name TEXT NOT NULL,
    quantity INTEGER DEFAULT 1,
    is_packed INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (trip_id) REFERENCES trips(id) ON DELETE CASCADE
);

-- TRIP NOTES / JOURNAL
CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trip_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    title TEXT,
    content TEXT NOT NULL,
    trip_day INTEGER DEFAULT 1,
    mood TEXT DEFAULT 'happy',   -- happy, excited, tired, amazing, meh
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (trip_id) REFERENCES trips(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- SEED: Default Activities
INSERT OR IGNORE INTO activities (name, category, description, estimated_cost, duration_hours, city, country, is_custom) VALUES
('Eiffel Tower Visit', 'sightseeing', 'Visit the iconic iron tower', 25, 3, 'Paris', 'France', 0),
('Louvre Museum', 'culture', 'Worlds largest art museum', 17, 4, 'Paris', 'France', 0),
('Colosseum Tour', 'culture', 'Ancient Roman amphitheater', 16, 2, 'Rome', 'Italy', 0),
('Vatican City', 'culture', 'Smallest country, massive history', 20, 4, 'Rome', 'Italy', 0),
('Sagrada Familia', 'culture', 'Gaudi masterpiece cathedral', 26, 2, 'Barcelona', 'Spain', 0),
('Tokyo Skytree', 'sightseeing', 'Tallest tower in Japan', 20, 2, 'Tokyo', 'Japan', 0),
('Mount Fuji Day Trip', 'adventure', 'Iconic volcano day hike', 80, 8, 'Tokyo', 'Japan', 0),
('Bali Temple Tour', 'culture', 'Sacred Hindu temples', 15, 5, 'Bali', 'Indonesia', 0),
('Santorini Sunset Cruise', 'adventure', 'Catamaran cruise at sunset', 120, 4, 'Santorini', 'Greece', 0),
('Thai Cooking Class', 'food', 'Learn to cook authentic Thai', 45, 3, 'Bangkok', 'Thailand', 0);
