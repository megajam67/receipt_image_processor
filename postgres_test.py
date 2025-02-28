#!/usr/bin/env python3
import psycopg2
import os

def main():
    # Get password from environment variable
    password = os.environ.get('POSTGRES_PASSWORD')
    if not password:
        print("Error: POSTGRES_PASSWORD environment variable not set")
        return
    
    # Connection parameters
    conn_params = {
        'host': 'localhost',
        'database': 'postgres',
        'user': 'postgres',
        'password': password
    }
    
    # Establish connection
    conn = None
    try:
        print("Connecting to PostgreSQL database...")
        conn = psycopg2.connect(**conn_params)
        
        # Create a cursor
        cur = conn.cursor()
        
        # Create test table if it doesn't exist
        print("Creating test_table if it doesn't exist...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS test_table (
                id SERIAL PRIMARY KEY,
                data TEXT NOT NULL
            )
        """)
        
        # Insert test data
        print("Inserting test data...")
        cur.execute("INSERT INTO test_table (data) VALUES (%s) RETURNING id", 
                ("Test data from Python script",))
        inserted_id = cur.fetchone()[0]
        
        # Commit changes
        conn.commit()
        
        # Query data back
        print(f"Querying data with id {inserted_id}...")
        cur.execute("SELECT id, data FROM test_table WHERE id = %s", (inserted_id,))
        row = cur.fetchone()
        
        if row:
            print(f"Data retrieved successfully: id={row[0]}, data='{row[1]}'")
            print("Database connection, write, and read test successful!")
        else:
            print("Error: Failed to retrieve inserted data")
        
        # Close cursor
        cur.close()
    
    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Error: {error}")
    finally:
        if conn is not None:
            conn.close()
            print("Database connection closed.")

if __name__ == "__main__":
    main()

