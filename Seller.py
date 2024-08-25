# Seller.py
from Product import Database as BaseDatabase
from mysql.connector import Error
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(funcName)s - %(message)s')
logger = logging.getLogger(__name__)

class SellerDatabase(BaseDatabase):
    def __init__(self):
        super().__init__()

    def fetch_seller_from_table(self, sid):
        connection = None
        try:
            connection = super().connect_to_database()
            if connection:
                cursor = connection.cursor()
                cursor.execute("""
                    SELECT *
                    FROM sellers 
                    WHERE seller_id=%s
                    """, 
                    (sid,))
                result_tuple = cursor.fetchone()
                columns = [col[0] for col in cursor.description] # Get column names
                cursor.close()
                if result_tuple:
                    result_dict = dict(zip(columns, result_tuple)) # Convert result_tuple to a dictionary with column names as keys
                    logger.info(f"Fetched seller info for seller_id: {sid} - Result: {result_dict}")
                else:
                    logger.info(f"No seller info found for seller_id: {sid}")
                return result_tuple, result_dict
        except Error as e:
            logger.error(f"Error fetching seller info: {e}")
        # finally:
        #     if connection and connection.is_connected():
        #         connection.close()
        #         logger.info("Database connection closed after fetching seller info.")
        # return None

    # def update_total_scraped_product_num(self, sid, num_to_add):
    #     connection = None
    #     try:
    #         connection = super().connect_to_database()
    #         if connection:
    #             cursor = connection.cursor()
    #             cursor.execute("""
    #                 UPDATE sellers
    #                 SET total_scraped_product_num = total_scraped_product_num + %s
    #                 WHERE seller_id = %s
    #             """, 
    #             (num_to_add, sid))
                
    #             connection.commit() # Commit the transaction
    #             logger.info(f"Updated total_scraped_product_num for seller_id: {sid} by adding {num_to_add}")
    #             cursor.close()
    #     except Error as e:
    #         logger.error(f"Error updating total_scraped_product_num for seller_id {sid}: {e}")
    #     # finally:
    #     #     if connection and connection.is_connected():
    #     #         connection.close()
    #     #         logger.info("Database connection closed after updating total_scraped_product_num.")

    def close(self):
        super().close()