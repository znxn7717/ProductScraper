# from Scraper import ProductScraper
from Test import ProductScraper

# WebDriverWait 

scraper = ProductScraper()
seller_url = 'https://basalam.com/arayeshii_artemis'
# seller_url = 'https://basalam.com/khaneyesalamat'
# seller_url = 'https://torob.com/shop/5566/%D8%B2%D8%B1%D9%BE%D9%88%D8%B4%D8%A7%D9%86/%D9%85%D8%AD%D8%B5%D9%88%D9%84%D8%A7%D8%AA'
# seller_url = 'https://www.digikala.com/seller/5a6gg/'
# seller_url = 'https://www.digikala.com/seller/c7kvk/'
scraper.basalam_products_details_extractor(seller_url, driver='firefox')
# scraper.torob_products_details_extractor(seller_url, driver='firefox')
# scraper.digikala_products_details_extractor(seller_url, driver='chrome')


        # def scroll_to_end(driver):
        #     action = ActionChains(driver)
        #     # products_len = products_num
        #     getted_num = 0
        #     repeat_count = 0
        #     last_len = 0

        #     while getted_num < products_num:
        #         getted_num = len(driver.find_element(By.XPATH, '/html/body/div[1]/div[1]/div[3]/div[3]/div[3]/div/section[1]/div[2]').find_elements(By.TAG_NAME, 'a'))
        #         print(f'getted: {getted_num}')

        #         # Check if the length has not changed
        #         if getted_num == last_len:
        #             repeat_count += 1
        #         else:
        #             repeat_count = 0
        #             last_len = getted_num

        #         # If the length has not changed for more than 20 times, scroll to the top and then continue
        #         if repeat_count > 10:
        #             driver.execute_script("window.scrollTo(0, 4000);")  # Scroll to the top using JavaScript
        #             time.sleep(1)
        #             repeat_count -= 10  # Reset repeat count

        #         # Scroll down
        #         action.scroll_by_amount(0, 10000).perform()  # Scroll down by 10000 pixels

        # # Scroll to the end of the page to load all products
        # scroll_to_end(driver)