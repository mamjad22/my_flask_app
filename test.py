import pyodbc

try:
    # Connects via the Windows ODBC System DSN configuration
    con = pyodbc.connect("DSN=rpldb_odbc;UID=rpl;PWD=rplview123")
    cursor = con.cursor()
    
    # Verify the connection by querying the database version
    cursor.execute("SELECT version FROM v$instance")
    row = cursor.fetchone()
    print("Successfully connected to 9i database via ODBC!")
    print("Database Version:", row[0])
    
except pyodbc.Error as e:
    print("ODBC Error encountered:")
    print(e)
