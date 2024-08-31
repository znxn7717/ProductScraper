# Product.py
import os
import json
import logging
import mysql.connector
from dotenv import load_dotenv
from mysql.connector import Error

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(funcName)s - %(message)s')
logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        load_dotenv()
        self.host = os.getenv('DB_HOST', '127.0.0.1')
        self.port = os.getenv('DB_PORT', 3306)
        self.database = os.getenv('DB_DATABASE')
        self.user = os.getenv('DB_USER', 'root')
        self.password = os.getenv('DB_PASSWORD', '')
        self.connection = None

    def connect_to_database(self):
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user if self.user else None,
                password=self.password if self.password else None
            )
            if self.connection.is_connected():
                logger.info("Successfully connected to the database.")
                return self.connection
        except Error as e:
            logger.error(f"Error while connecting to MySQL: {e}")
            return None

    def setup_product_table(self):
        try:
            if self.connection is None or not self.connection.is_connected():
                logger.warning("Not connected to the database. Call connect_to_database() first.")
                return
            cursor = self.connection.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    is_scraped TINYINT DEFAULT 0,
                    seller_id VARCHAR(255),
                    link VARCHAR(255) UNIQUE,
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
            logger.info("Product table setup completed successfully.")
        except Error as e:
            logger.error(f"Error while setting up product table: {e}")

    def upsert_product_in_table(self, details):
        try:
            if self.connection.is_connected():
                cursor = self.connection.cursor()
                query = """
                    INSERT INTO products (is_scraped, seller_id, link, product_group, title, stock, price, main_pic_link, main_pic_alt, gallery)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        is_scraped=VALUES(is_scraped),
                        seller_id=VALUES(seller_id),
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
                    details['is_scraped'], details['seller_id'], details['link'], details['product_group'], details['title'],
                    details['stock'], details['price'], details['main_pic_link'], details['main_pic_alt'],
                    json.dumps(details['gallery'])
                ))
                self.connection.commit()
                cursor.close()
                logger.info(f"Product inserted/updated successfully for link: {details['link']}")
        except Error as e:
            if "Duplicate entry" in str(e):
                logger.warning(f"Duplicate entry for link: {details['link']}")
            else:
                logger.error(f"Error while inserting product: {e}")

    def update_total_scraped_product_num(self, seller_id):
        try:
            if self.connection.is_connected():
                cursor = self.connection.cursor()
                # Query to calculate total scraped products for the specific seller_id
                query = """
                    SELECT SUM(is_scraped) as total_scraped
                    FROM products
                    WHERE seller_id = %s
                """
                cursor.execute(query, (seller_id,))
                result = cursor.fetchone()
                if result and result[0] is not None:
                    total_scraped = result[0]
                    # Update the sellers table with the total scraped products count for this seller_id
                    update_query = """
                        UPDATE sellers
                        SET total_scraped_product_num = %s
                        WHERE seller_id = %s
                    """
                    cursor.execute(update_query, (total_scraped, seller_id))
                    self.connection.commit()
                    logger.info(f"Sellers' total scraped product count updated successfully for seller_id: {seller_id}.")
                else:
                    logger.warning(f"No scraped products found for seller_id: {seller_id}.")
                cursor.close()
        except Error as e:
            logger.error(f"Error while updating scraped product count for seller_id {seller_id}: {e}")

    def close(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("Database connection closed.")