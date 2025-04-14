import time
import re
import pandas as pd
import logging
import os
import sys
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define required columns for the final output
REQUIRED_COLUMNS = [
    'Organization', 'Camp Name', 'Week', 'Days', 
    'Start Time', 'End Time', 'Location', 'Age Range', 
    'Grade Range', 'Price', 'Description', 'Email', 'Contact'
]

# --- Define Base Path for Output Files ---
try:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))
except IndexError:
    SCRIPT_DIR = os.getcwd()
    logger.warning(f"sys.argv[0] not available, using current working directory: {SCRIPT_DIR}")
except Exception as e:
    SCRIPT_DIR = os.getcwd()
    logger.warning(f"Error getting script directory ({e}), using current working directory: {SCRIPT_DIR}")

# Function to save data to CSV
def save_to_csv(camp_data_list, csv_filename):
    """Saves all camp data to a single CSV file."""
    if not camp_data_list:
        logger.warning(f"No data to save to {csv_filename}")
        return False
    
    try:
        df = pd.DataFrame(camp_data_list, columns=REQUIRED_COLUMNS)
        os.makedirs(os.path.dirname(csv_filename), exist_ok=True)
        df.to_csv(csv_filename, index=False, encoding='utf-8')
        logger.info(f"Successfully saved {len(camp_data_list)} records to {csv_filename}")
        return True
    except Exception as e:
        logger.error(f"Failed to save data to {csv_filename}: {e}")
        return False

def scrape_lifetime_camps(url, location_name="Frisco", max_retries=3, delay_between_retries=10):
    """Scrape Lifetime Fitness summer camp data.
    
    Args:
        url (str): The full URL of the camp listings page.
        location_name (str): The name of the location (e.g., "Frisco").
        max_retries (int): Maximum number of attempts if initial load fails.
        delay_between_retries (int): Seconds to wait between retry attempts.
    """
    logger.info(f"===== Starting scrape for Lifetime Fitness Summer Camps at {location_name} (URL: {url}) =====")
    
    # Set up the output filename
    csv_filename = os.path.join(SCRIPT_DIR, f'lifetime_camps_{location_name.lower().replace(" ", "_")}.csv')
    
    driver = None
    camp_data_list = []
    organization = "Lifetime Fitness"
    
    for attempt in range(max_retries + 1):
        if attempt > 0:
            logger.info(f"Retry attempt {attempt} of {max_retries}")
            time.sleep(delay_between_retries)
        
        try:
            logger.info("Setting up Chrome driver...")
            chrome_options = Options()
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
            
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
            
            logger.info(f"Navigating to {url}")
            driver.get(url)
            
            # Wait for page to load and camp cards to appear
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='campCard']"))
            )
            
            # Find all camp cards
            camp_cards = driver.find_elements(By.CSS_SELECTOR, "[data-testid='campCard']")
            logger.info(f"Found {len(camp_cards)} camp cards")
            
            for index, card in enumerate(camp_cards):
                try:
                    logger.info(f"Processing camp card {index+1} of {len(camp_cards)}")
                    
                    # Extract basic camp info from card
                    camp_category = card.find_element(By.CSS_SELECTOR, ".h6").text.strip()
                    camp_name = card.find_element(By.CSS_SELECTOR, ".h4").text.strip()
                    logger.info(f"Processing camp: {camp_name} ({camp_category})")
                    
                    # Extract age range
                    age_range = card.find_element(By.CSS_SELECTOR, "p.small.font-weight-bold").text.strip()
                    
                    # Extract date(s)/week
                    week = ""
                    try:
                        # Check if it's a date range (has time-start and time-end)
                        start_date_elem = card.find_element(By.CSS_SELECTOR, "time.time-start")
                        end_date_elem = card.find_element(By.CSS_SELECTOR, "time.time-end")
                        # Extract the user-visible text part (e.g., "Jun 2")
                        start_date_text = start_date_elem.text.strip()
                        # Extract the full date string (e.g., "Jun 6, 2025")
                        end_date_text = end_date_elem.text.strip()
                        week = f"{start_date_text} to {end_date_text}"
                    except NoSuchElementException:
                        # If not a range, assume single date
                        try:
                            date_elem = card.find_element(By.CSS_SELECTOR, "p.small.m-b-sm > span > time")
                            week = date_elem.get_attribute('aria-label') # Use aria-label for the full date text
                            if not week: # Fallback to text content if aria-label is empty
                                week = date_elem.text.strip().replace('\\n', ' ')
                        except NoSuchElementException:
                             logger.warning(f"Could not find date element for camp {camp_name}")
                             week = "Date not found"
                    
                    # Extract location using CSS attribute selector
                    try:
                        location_elem = card.find_element(By.CSS_SELECTOR, "[id^='campLocation-']")
                        location = location_elem.text.strip().replace("Frisco", "Lifetime Fitness " + location_name)
                    except NoSuchElementException:
                        logger.error(f"Could not find location element for camp {camp_name}")
                        location = "Location not found"
                        # Optionally, decide if you want to skip this card or continue with missing data
                        # continue
                    
                    # Check if field trip info exists ON THE CARD
                    field_trip_card_text = ""
                    try:
                        field_trip_elem = card.find_element(By.CSS_SELECTOR, "[data-testid='fieldTrip']")
                        if field_trip_elem.is_displayed():
                            field_trip_card_text = field_trip_elem.text.strip()
                            # Clean up the prefix if present
                            if field_trip_card_text.startswith("Friday Field Trip:"):
                                field_trip_card_text = field_trip_card_text.replace("Friday Field Trip:", "").strip()
                    except NoSuchElementException:
                        pass # Field trip element is optional
                    
                    # Extract price information
                    price_per_day = "N/A"
                    price = "N/A"
                    try:
                        price_per_day = card.find_element(By.CSS_SELECTOR, ".display-number-value").text.strip()
                        price = f"${price_per_day} per day"
                        # Calculate weekly price (assuming 5 days, might need adjustment for shorter weeks)
                        try:
                            weekly_price = float(price_per_day) * 5
                            price = f"${price_per_day}/day (${weekly_price:.2f}/week)"
                        except ValueError:
                             logger.warning(f"Could not convert price '{price_per_day}' to float for weekly calculation.")
                             # Keep the daily price format if conversion fails
                    except NoSuchElementException:
                        logger.warning(f"Could not find price element for camp {camp_name}")
                    
                    # Check availability
                    availability = ""
                    try:
                        availability_elem = card.find_element(By.CSS_SELECTOR, "p.availability span")
                        if availability_elem.is_displayed():
                            availability = availability_elem.text.strip()
                    except NoSuchElementException:
                        pass # Availability is optional
                    
                    # --- Click "More Details" to get full description and times ---
                    days = "Not specified"
                    start_time = "Not specified"
                    end_time = "Not specified"
                    description = f"Camp: {camp_name} ({camp_category}). Check website for full details." # Default description
                    
                    try:
                        more_details_btn = WebDriverWait(card, 5).until(
                             EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='moreDetailsBtn']"))
                        )
                        # Scroll into view if necessary, sometimes helps with clicks
                        driver.execute_script("arguments[0].scrollIntoView(true);", more_details_btn)
                        time.sleep(0.2) # Brief pause after scroll
                        driver.execute_script("arguments[0].click();", more_details_btn) # Use JS click for reliability

                        # Wait for modal to appear and be ready (wait for description text)
                        modal = WebDriverWait(driver, 15).until(
                            EC.visibility_of_element_located((By.CSS_SELECTOR, ".modal-body"))
                        )
                        # Wait specifically for description text to ensure content is loaded
                        WebDriverWait(modal, 5).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, ".description p"))
                        )
                        time.sleep(0.5) # Small pause for content loading within modal
                        
                        # Get detailed schedule (days)
                        try:
                            # Try the specific structure first based on the example
                            days_info = modal.find_element(By.XPATH, ".//p[contains(text(), 'Meets:')]").text.strip() # Search within modal
                            days = days_info.replace("Meets:", "").strip()
                        except NoSuchElementException:
                            try:
                                # Fallback selector if the specific text isn't found
                                days_info = modal.find_element(By.CSS_SELECTOR, ".time-and-location p.small:nth-of-type(3)").text.strip()
                                if "Meets:" in days_info: # Check if the fallback still contains the keyword
                                     days = days_info.replace("Meets:", "").strip()
                                else:
                                     logger.warning(f"Fallback 'days' selector did not contain 'Meets:' for {camp_name}. Text: {days_info}")
                                     days = "Check website" # Or use days_info directly if appropriate
                            except NoSuchElementException:
                                logger.warning(f"Could not find days schedule in modal for {camp_name}. Using default.")
                                days = "Monday-Friday" # Assume default if not found

                        # Get times (Start/End) using more specific selectors from modal
                        try:
                            start_time_elem = modal.find_element(By.CSS_SELECTOR, ".time-and-location .time-start")
                            start_time = start_time_elem.text.strip()
                        except NoSuchElementException:
                            logger.warning(f"Could not find start time in modal for {camp_name}")
                            start_time = ""

                        try:
                            end_time_elem = modal.find_element(By.CSS_SELECTOR, ".time-and-location .time-end")
                            end_time = end_time_elem.text.strip()
                        except NoSuchElementException:
                            logger.warning(f"Could not find end time in modal for {camp_name}")
                            end_time = ""

                        # Get full description from modal
                        try:
                            description_elem = modal.find_element(By.CSS_SELECTOR, ".description p")
                            description = description_elem.text.strip()
                        except NoSuchElementException:
                            logger.warning(f"Could not find description paragraph in modal for {camp_name}. Using default.")
                            description = f"Camp: {camp_name} ({camp_category})." # Basic description if modal one fails
                        
                        # Append field trip info (from card) to description if available AND not empty
                        if field_trip_card_text:
                             description += f"\\n\\nFriday Field Trip: {field_trip_card_text}"

                        # Close the modal
                        try:
                            close_btn = WebDriverWait(driver, 5).until(
                                EC.element_to_be_clickable((By.CSS_SELECTOR, ".modal-header .close"))
                            )
                            # Use JavaScript click as regular click might be intercepted
                            driver.execute_script("arguments[0].click();", close_btn)
                            # Wait for modal to disappear
                            WebDriverWait(driver, 10).until(
                                EC.invisibility_of_element_located((By.CSS_SELECTOR, ".modal-backdrop.fade.in")) # More specific selector for modal backdrop
                            )
                            time.sleep(0.5) # Small pause after closing
                        except Exception as close_err:
                             logger.warning(f"Could not close modal cleanly for {camp_name}: {close_err}. Attempting to proceed.")
                             # Try sending ESC key as a fallback
                             try:
                                 from selenium.webdriver.common.keys import Keys
                                 driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                                 WebDriverWait(driver, 5).until( # Wait a bit after ESC
                                    EC.invisibility_of_element_located((By.CSS_SELECTOR, ".modal-backdrop.fade.in"))
                                 )
                                 time.sleep(0.5) # Pause after ESC
                             except Exception as esc_err:
                                 logger.error(f"Failed to close modal with ESC key: {esc_err}")

                    except TimeoutException:
                         logger.warning(f"Timed out waiting for modal details for {camp_name}. Using card data only.")
                         # Use default description and times set earlier
                         # Append field trip info if available from card
                         if field_trip_card_text:
                            description += f"\\n\\nFriday Field Trip: {field_trip_card_text}"
                    except Exception as modal_err:
                         logger.error(f"Error opening or processing modal for {camp_name}: {modal_err}")
                         # Use default description and times set earlier
                         # Append field trip info if available from card
                         if field_trip_card_text:
                             description += f"\\n\\nFriday Field Trip: {field_trip_card_text}"

                    # Create data entry
                    camp_data = {
                        'Organization': organization,
                        'Camp Name': f"{camp_name} ({camp_category})",
                        'Week': week,
                        'Days': days,
                        'Start Time': start_time,
                        'End Time': end_time,
                        'Location': location,
                        'Age Range': age_range,
                        'Grade Range': "",  # Not provided
                        'Price': price,
                        'Description': description,
                        'Email': "",  # Not provided
                        'Contact': ""  # Not provided
                    }
                    
                    camp_data_list.append(camp_data)
                    logger.info(f"Added {camp_name} to data list")
                    
                except Exception as e:
                    logger.error(f"Error processing camp card {index+1}: {e}")
                    continue
            
            # If we've processed all cards successfully, break the retry loop
            logger.info(f"Successfully processed {len(camp_data_list)} camp sessions")
            break
            
        except Exception as e:
            logger.error(f"An error occurred during attempt {attempt + 1}: {e}")
            if attempt == max_retries:
                logger.error("Maximum retries reached. Scraping failed.")
            else:
                logger.info(f"Waiting {delay_between_retries} seconds before next retry...")
        
        finally:
            if driver:
                logger.info("Closing Chrome driver.")
                driver.quit()
                driver = None
    
    # Save all collected data to CSV
    if camp_data_list:
        save_to_csv(camp_data_list, csv_filename)
    else:
        logger.warning("No camp data was collected to save.")
    
    logger.info(f"===== Finished scrape for Lifetime Fitness at {location_name}. Check {csv_filename} =====")
    return camp_data_list

# --- Main Execution Block ---
if __name__ == "__main__":
    # URL for the Lifetime Fitness Plano summer camps page
    lifetime_url = "https://my.lifetime.life/clubs/tx/plano/camps.html"
    
    # Run the scraper
    scrape_lifetime_camps(lifetime_url, location_name="Plano")