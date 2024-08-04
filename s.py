# def scroll_to_end(driver):
    #     action = ActionChains(driver)
    #     products_len = int(re.sub(r'\D', '', driver.find_element(By.XPATH, '/html/body/div[1]/div[1]/div[3]/div[3]/div[3]/div/section[1]/div[1]/div/div/div/div[3]/span').text))
    #     getted_len = 0
    #     repeat_count = 0
    #     last_len = 0

    #     while getted_len < products_len:
    #         getted_len = len(driver.find_element(By.XPATH, '/html/body/div[1]/div[1]/div[3]/div[3]/div[3]/div/section[1]/div[2]').find_elements(By.TAG_NAME, 'a'))
    #         print(f'getted: {getted_len}')

    #         # Check if the length has not changed
    #         if getted_len == last_len:
    #             repeat_count += 1
    #         else:
    #             repeat_count = 0
    #             last_len = getted_len

    #         # If the length has not changed for more than 20 times, scroll to the top and then continue
    #         if repeat_count > 10:
    #             driver.execute_script("window.scrollTo(0, 5000);")  # Scroll to the top using JavaScript
    #             repeat_count -= 10  # Reset repeat count

    #         # Scroll down
    #         action.scroll_by_amount(0, 10000).perform()  # Scroll down by 10000 pixels

    # # Scroll to the end of the page to load all products
    # scroll_to_end(driver)
