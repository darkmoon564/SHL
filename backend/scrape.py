import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_URL = "https://www.shl.com/solutions/products/product-catalog/"
OUTPUT_JSON = "d:/shl/data/assessments.json"
OUTPUT_CSV = "d:/shl/data/assessments.csv"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124 Safari/537.36"
}

def fetch_assessment_details(assessment):
    """Fetch details from the assessment's detail page."""
    url = assessment["assessment_url"]
    try:
        response = requests.get(url, headers=HEADERS)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            
            description = None
            duration_info = None
            
            product_module = soup.find("div", class_="product-catalogue module")
            if not product_module:
                product_module = soup.find("div", class_=lambda x: x and "product-catalogue" in x and "module" in x)
            
            if product_module:
                # Find all rows with class "product-catalogue-training-calendar__row typ"
                detail_rows = product_module.find_all("div", class_="product-catalogue-training-calendar__row typ")
                
                # If no results, try finding by partial class match
                if len(detail_rows) == 0:
                    detail_rows = product_module.find_all("div", class_=lambda x: x and "product-catalogue-training-calendar__row" in x)
                
                for row in detail_rows:
                    # Look for Description section
                    h4_tag = row.find("h4")
                    if h4_tag:
                        h4_text = h4_tag.text.strip()
                        
                        # Extract description
                        if "description" in h4_text.lower():
                            p_tag = row.find("p")
                            if p_tag:
                                description = p_tag.text.strip()
                        
                        # Extract duration/assessment length
                        elif "assessment length" in h4_text.lower():
                            p_tag = row.find("p")
                            if p_tag:
                                p_text = p_tag.text.strip()
                                 
                                duration_match = re.search(r'=\s*(\d+)', p_text, re.IGNORECASE)
                                if duration_match:
                                    duration_info = f"{duration_match.group(1)} minutes"
                                else:
                                    duration_match = re.search(r'(\d+)\s*(?:min|minute|minutes)', p_text, re.IGNORECASE)
                                    if duration_match:
                                        duration_info = f"{duration_match.group(1)} minutes"
                                    else:
                                        num_match = re.search(r'(\d+)', p_text)
                                        if num_match:
                                            duration_info = f"{num_match.group(1)} minutes"
            
            # Update the assessment object
            if description:
                assessment["description"] = description
            if duration_info:
                assessment["duration"] = duration_info
                
    except Exception as e:
        print(f"Error fetching details for {url}: {e}")
    
    return assessment

def scrape_table(table):
    """Extract data from a single table."""
    assessments = []
    rows = table.find_all("tr")[1:]  # Skip header

    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 4:
            continue

        name_col = cols[0]
        name_tag = name_col.find("a")
        name = name_tag.text.strip() if name_tag else "Unknown"
        url = name_tag["href"] if name_tag and "href" in name_tag.attrs else ""
        
        # Ensure absolute URL
        full_url = "https://www.shl.com" + url if url.startswith("/") else url

        # Check filtering (optional, based on previous logic, but user script didn't have it. keeping it broader is safer)
        # But we should probably filter out non-individual tests if that was important?
        # The user's script didn't filter, so I will NOT filter, to maximize data collection.

        remote_col = cols[1]
        remote_testing = "Yes" if remote_col.find("span", class_="catalogue__circle -yes") else "No"

        adaptive_col = cols[2]
        adaptive_irt = "Yes" if adaptive_col.find("span", class_="catalogue__circle -yes") else "No"

        test_type_col = cols[3]
        test_keys = test_type_col.find_all("span", class_="product-catalogue__key")
        test_type = ", ".join(key.text.strip() for key in test_keys) if test_keys else "N/A"

        assessments.append({
            "assessment_name": name,
            "assessment_url": full_url,
            "duration": "N/A",
            "description": "N/A",
            "test_type": test_type,
            "remote_testing": remote_testing,
            "adaptive_irt": adaptive_irt
        })

    return assessments

def scrape_pages_for_assessments(type_param, max_pages):
    all_assessments = []
    # Scrape up to max_pages
    for page_start in range(0, max_pages * 12, 12):
        print(f"Fetching page start: {page_start}")
        url = f"{BASE_URL}?start={page_start}&type={type_param}"
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            if response.status_code != 200:
                print(f"Failed to fetch {url}: {response.status_code}")
                break

            soup = BeautifulSoup(response.content, "html.parser")

            tables = soup.find_all("table")
            
            if len(tables) == 0:
                print(f"No table found at start={page_start}, stopping.")
                break
            elif len(tables) == 1:
                table = tables[0]
            elif len(tables) >= 2:
                table = tables[1]

            assessments = scrape_table(table)
            if not assessments:
                print(f"No assessments found at start={page_start}, stopping.")
                break
            
            print(f"Found {len(assessments)} assessments on this page.")
            all_assessments.extend(assessments)
            time.sleep(0.5)  # Be nice to their server
            
        except Exception as e:
            print(f"Exception fetching {url}: {e}")
            break

    return all_assessments

def scrape():
    # Max pages 40 * 12 = 480 items, enough to cover target of ~377
    assessments = scrape_pages_for_assessments(type_param=1, max_pages=40)
    
    print(f"Start fetching details for {len(assessments)} items...")
    
    # Use ThreadPoolExecutor to fetch details in parallel
    with ThreadPoolExecutor(max_workers=8) as executor:
        future_to_assessment = {executor.submit(fetch_assessment_details, assessment): assessment 
                               for assessment in assessments}
        
        completed = 0
        for future in as_completed(future_to_assessment):
            completed += 1
            if completed % 10 == 0:
                print(f"Progress: {completed}/{len(assessments)} details processed")
    
    return assessments

def save_data(assessments):
    # Save to JSON
    os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(assessments, f, indent=2)
    print(f"Saved {len(assessments)} items to JSON: {OUTPUT_JSON}")

    # Save to CSV
    df = pd.DataFrame(assessments)
    if not df.empty:
        df.to_csv(OUTPUT_CSV, index=False)
        print(f"Saved {len(df)} items to CSV: {OUTPUT_CSV}")
    else:
        print("No data to save to CSV")

if __name__ == "__main__":
    data = scrape()
    save_data(data)
