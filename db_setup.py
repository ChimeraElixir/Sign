import sqlite3

conn = sqlite3.connect("sign_language.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS signs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT UNIQUE,
    image TEXT,
    type TEXT
)
""")

# Sample data
data = [
    ('a','a.jpg','alphabet'),
    ('b','b.png','alphabet'),
    ('c','c.png','alphabet'),
    ('d','d.png','alphabet'),
    ('e','e.png','alphabet'),
    ('f','f.jpg','alphabet'),
    ('g','g.png','alphabet'),
    ('h','h.jpg','alphabet'),
    ('i','i.png','alphabet'),
    ('j','j.png','alphabet'),
    ('k','k.jpg','alphabet'),
    ('l','l.png','alphabet'),
    ('m','m.png','alphabet'),
    ('n','n.png','alphabet'),
    ('o','o.jpg','alphabet'),
    ('p','p.jpg','alphabet'),
    ('q','q.png','alphabet'),
    ('r','r.png','alphabet'),
    ('s','s.png','alphabet'),
    ('t','t.jpg','alphabet'),
    ('u','u.jpg','alphabet'),
    ('v','v.jpg','alphabet'),
    ('w','w.png','alphabet'),
    ('x','x.png','alphabet'),
    ('y','y.jpg','alphabet'),
    ('z','z.png','alphabet'),

    ("hello", "hello.gif", "word"),
    ("good", "good.png", "word"),
    ("rainbow", "rainbow.png", "word")
]

cursor.executemany(
    "INSERT OR IGNORE INTO signs (text, image, type) VALUES (?, ?, ?)",
    data
)

conn.commit()
conn.close()

print("Database created successfully!")
