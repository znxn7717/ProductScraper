import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os
import json

class Database:
    def __init__(self):
        load_dotenv()
        self.host = os.getenv('DB_HOST', '127.0.0.1')
        self.port = os.getenv('DB_PORT', 3306)
        self.database = os.getenv('DB_DATABASE')
        self.user = os.getenv('DB_USER', '')
        self.password = os.getenv('DB_PASSWORD', '')
        self.connection = None

    def product_connect(self):
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user if self.user else None,
                password=self.password if self.password else None
            )
            if self.connection.is_connected():
                cursor = self.connection.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS products (
                        id INT PRIMARY KEY,
                        link VARCHAR(255),
                        product_group VARCHAR(255),
                        title VARCHAR(255),
                        stock INT,
                        price DECIMAL(10, 2),
                        main_pic_link VARCHAR(255),
                        main_pic_alt VARCHAR(255),
                        gallery JSON
                    )
                """)
                cursor.execute("""
                    ALTER TABLE products
                    ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                """)
                cursor.close()
        except Error as e:
            print(f"Error while connecting to MySQL: {e}")

    def product_create(self, details):
        try:
            if self.connection.is_connected():
                cursor = self.connection.cursor()
                query = """
                    INSERT INTO products (id, link, product_group, title, stock, price, main_pic_link, main_pic_alt, gallery)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        link=VALUES(link),
                        product_group=VALUES(product_group),
                        title=VALUES(title),
                        stock=VALUES(stock),
                        price=VALUES(price),
                        main_pic_link=VALUES(main_pic_link),
                        main_pic_alt=VALUES(main_pic_alt),
                        gallery=VALUES(gallery),
                        updated_at=CURRENT_TIMESTAMP
                """
                cursor.execute(query, (
                    details['id'], details['link'], details['product_group'], details['title'],
                    details['stock'], details['price'], details['main_pic_link'], details['main_pic_alt'],
                    json.dumps(details['gallery'])
                ))
                self.connection.commit()
                cursor.close()
        except Error as e:
            print(f"Error while inserting product: {e}")

    def close(self):
        if self.connection.is_connected():
            self.connection.close()
