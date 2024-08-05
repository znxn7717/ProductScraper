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