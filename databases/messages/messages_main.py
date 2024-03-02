import mysql.connector

# Connect to the MySQL database
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="qpslzmqpslzm",
        database="abothasnoname"
    )

# Insert message details into the database
async def log_message(m_id, server, user, channel, date, time):
    db_connection = get_db_connection()

    cursor = db_connection.cursor()
    sql = "INSERT INTO messages_main (id, server_id, user_id, channel_id, date, time) VALUES (%s, %s, %s, %s, %s, %s)"
    val = (m_id, server, user, channel, date, time)
    cursor.execute(sql, val)
    db_connection.commit()

    # Close the database connection when the bot exits
    db_connection.close()