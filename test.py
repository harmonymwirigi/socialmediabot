import pymysql

try:
    # Try to establish a connection
    connection = pymysql.connect(
        host='host.cpse32.eu',
        user='g304975_g304975',
        password='(SOilf%n_K(a',  # Your password
        database='g304975_social-media',
        port=3306
    )
    print("Connection successful!")
    connection.close()
except Exception as e:
    print(f"Connection failed: {e}")