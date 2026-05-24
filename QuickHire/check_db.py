import sqlite3

conn = sqlite3.connect("quickhire.db")
cursor = conn.cursor()

cursor.execute("SELECT * FROM users")
rows = cursor.fetchall()

print("\n===== ALL USERS =====\n")

for row in rows:
    print(f"""
ID: {row[0]}
Name: {row[1]}
Email: {row[2]}
Password Hash: {row[3]}
Company: {row[4]}
Phone: {row[5]}
""")
    
conn.close()