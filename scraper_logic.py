import requests, csv, time, os #type: ignore
from datetime import date
from api_keys import get_places_api_key

#API Keys, Replace with your own API key
API_KEY_PLACES: str = get_places_api_key()

#Create directory to save CSVs to 
directory_name = 'cold_leads'
os.makedirs(directory_name, exist_ok=True) 

#Request URLs
url_places:str = 'https://places.googleapis.com/v1/places:searchText'
url_geo:str = 'https://maps.googleapis.com/maps/api/geocode/json' 

#Header for the POST request for places API
headers: dict[str, str] = {
    'Content-Type': 'application/json',
    'X-Goog-Api-Key': API_KEY_PLACES,
    'X-Goog-FieldMask': 'places.displayName,places.websiteUri,places.nationalPhoneNumber,nextPageToken,places.googleMapsUri,places.userRatingCount,places.photos'
}


#Simple string to list function for fun
def str_to_list(s:str) -> list[str]:
    string_list: list[str] = []
    char_list: list[str] = []
    count: int = 0
    str_appended: int = 0

    for char in s:
        count += 1
        if(count == len(s)):
            char_list.append(char)
            if(' ' in char_list and str_appended != 0):
                char_list.remove(' ') 
            string_list.append(''.join(char_list))  
        if(char == ','):
            if(' ' in char_list and str_appended != 0):
                char_list.remove(' ') 

            string_list.append(''.join(char_list))  
            str_appended += 1
            char_list.clear() 
        
            continue 
        char_list.append(char)
    return string_list

#Actual scraper function
def scraper(state: str, city:str, business_type:int, type_scrape:int) -> tuple[list[dict[str, str]], int]:
    #Words do not want in business list
    bad_words: set[str] = {
        # Corporate / Legal
        'holding', 'holdings', 'group', 'corporation', 'corp', 'incorporated', 'inc',
        'ltd', 'limited', 'enterprises', 'ventures', 'capital', 'equity',
        'partners', 'partnership', 'franchise',

        # Real Estate / Property
        'real estate', 'realty', 'property', 'properties', 'property management',
        'asset management', 'development', 'developers', 'construction management',

        # Government / Public
        'department', 'authority', 'municipal', 'city of', 'county of',
        'state of', 'federal', 'public works',

        # Global / Generic Business
        'international', 'worldwide', 'global', 'solutions', 'services group',

        # Tech / IT
        'tech', 'technologies', 'electronics', 'phone repair', 'computer repair',
        'it services', 'systems', 'data',

        # Consulting / Finance
        'consulting', 'consultants', 'advisors', 'advisory',
        'brokerage', 'agency',

        # Auto-related (non-target)
        'detail', 'detailing', 'detailers', 'detailing spa', 'auto spa',
        'audio', 'sound', 'stereo', 'car audio',
        'glass', 'auto glass', 'windshield', 'coating',
        'performance', 'motorsports', 'exhaust',

        # Printing / Signs
        'sign', 'signs', 'sign shop', 'signage', 'printing', 'print', 'print shop',

        # Retail / Misc
        'mobile', 'accessories', 'upholstery', 'restoration',
        'distributors', 'sticker', 'stickers', 'store',

        # Home / Leisure
        'pool', 'spa'
    }

    business_dict: dict[str, dict[str, str]]  = {} 
    search_type: list[str] = []
    api_requests: int = 0
    #Get cords for current city
    params: dict[str, str] = {
        'address': f'{city}, {state}',
        'key': API_KEY_PLACES
    }

    response_geo: requests.models.Response = requests.get(url_geo, params=params)
    api_requests += 1

    data_geo = response_geo.json() 

    if response_geo.status_code != 200:
        print(f'Error: {response_geo.status_code}') 
        print(f'Response: {response_geo.text}')
        print('Failed')  
        return ([], 0)
    
    city_lat: str = data_geo['results'][0]['geometry']['location']['lat']
    city_lng: str = data_geo['results'][0]['geometry']['location']['lng']


    #Search query selections;
    
    #Passing in a 1 corresponds to targeting, car customization shops
    if(business_type == 1):  
        search_type = [
            'car customization shop',
            'window tint shop',
            'car wraps',
            'vinyl wraps',
            'vehicle wraps',
            'paint protection film',
            'clear bra',
            'vehicle graphics',
        ]
    
    #Passing in a 2 corresponds to targeting, home remodeling
    else:
        search_type = [ 
            'home remodeling',
            'home remodeler',
            'residential remodeling',
            'general contractor',
            'home renovation',
            'kitchen remodeling',
            'bathroom remodeling',
        ]
    
    #Loop through each search type variation for a given business type
    for search in search_type:

        #Get searched data for a particular query
        next_page_token = None
        page_count: int = 0
        
        while True:
            page_count += 1

            data = {
                'textQuery': f'{search} in {city}',
                'pageSize': 20,
                'locationBias' : {
                    'circle' : {
                        'center' : {
                            'latitude' : city_lat, 
                            'longitude' : city_lng
                        },
                        'radius' : 19000.0
                    }
                }
            }

            if next_page_token:
                time.sleep(2)
                data['pageToken'] = next_page_token 

            #Request places data
            response_places: requests.models.Response = requests.post(url_places, json=data, headers=headers) 
            api_requests += 1

            if response_places.status_code != 200:
                print(f"Error: {response_places.status_code}")
                print(f"Response: {response_places.text}")
                print('Failed')  
                return ([], 0)

            results = response_places.json() 

            #Loop through each business from the places API response 
            for place in results.get('places', []): 
                #Get website and review count 
                website: str = place.get('websiteUri')
                business_rating_count: int = place.get('userRatingCount', 0) 
                
                if type_scrape == 1:
                    if not website:
                        business_name: str = place.get('displayName', {}).get('text', '') 
                        business_number: str = place.get('nationalPhoneNumber', '')
                        business_page_uri: str = place.get('googleMapsUri', '')
                        business_photos: list = place.get('photos', []) 

                        if not business_name or not business_number or business_rating_count < 2 or len(business_photos) < 2:
                            continue
                        
                        #Ensuring not taking business names with words dont want
                        name_lower = business_name.lower() 
                        name_tokens = name_lower.split() 
                        if any(
                            word.lower() in name_tokens or word.lower() in name_lower 
                            for word in bad_words
                        ): 
                            continue 

                        
                        #Labeling each unique business name and number scrape with no site
                        key = f'{business_name}|{business_number}' 
                        #If already has been labled then wont relabel and add, thus avoid duplication
                        if(key not in business_dict): 
                            business_dict[key] = {
                                'business_name': business_name, 
                                'business_number': business_number,
                                'business_page_uri' : business_page_uri
                            }

                else:
                    if website and business_rating_count <= 15: 
                        business_name = place.get('displayName', {}).get('text') 
                        business_number = place.get('nationalPhoneNumber')
                        business_page_uri = place.get('googleMapsUri')
                        business_photos = place.get('photos', []) 
                        business_website_uri: str = place.get('websiteUri')

                        if not business_name or not business_number or len(business_photos) < 2:
                            continue

                        #Ensuring not taking business names with words dont want
                        name_lower = business_name.lower() 
                        name_tokens = name_lower.split() 
                        if any(
                            word.lower() in name_tokens or word.lower() in name_lower 
                            for word in bad_words
                        ):
                            continue 

                        
                        #Labeling each unique business name and number scrape with no site
                        key = f'{business_name}|{business_number}' 
                        #If already has been labled then wont relabel and add, thus avoid duplication
                        if key not in business_dict: 
                            business_dict[key] = {
                                'business_name': business_name, 
                                'business_number': business_number,
                                'business_page_uri' : business_page_uri,
                                'business_website_uri' : business_website_uri
                            } 
            #Get token for going to next page
            next_page_token = results.get('nextPageToken')
            print(f'Finished {search}; Current page -> {page_count}')

            if not next_page_token or page_count >= 3:
                break


    return (list(business_dict.values()), api_requests)

#Saving data
def save_as_csv(business_list: list[dict[str, str]], business_type_scrape: int, type_scrape: int, city_scrape: str, state_scrape: str) -> None:
    today = date.today()
    filename: str = ' '
    
    if business_type_scrape == 1:
        filename = f'{directory_name}/car_custom_{city_scrape}_{state_scrape}_{today}.csv'
    else:
        filename = f'{directory_name}/home_remodel_{city_scrape}_{state_scrape}_{today}.csv'

    if type_scrape == 1:
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=['business_name', 'business_number', 'business_page_uri'])
            writer.writeheader()
            writer.writerows(business_list)
    else:
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=['business_name', 'business_number', 'business_page_uri', 'business_website_uri'])
            writer.writeheader()
            writer.writerows(business_list)

#Runs a single city at a time, and scrapes the corresponding business type and type of scrape in that business. After city is scraped saves it to csv in dir created above
def scraper_run_loop(state_scrape: str, cities_scrape: list[str], business_type_scrape: int, type_scrape: int) -> None:  
    leads_found: int = 0
    total_api_requests: int = 0 

    for city in cities_scrape:
        business_list, api_requests = scraper(state_scrape, city, business_type_scrape, type_scrape)  
        
        leads_found += len(business_list) 
        total_api_requests += api_requests
        
        #UI 
        print('-' * 40) 
        print(f'Finished scraping {city} for {business_type_label(business_type_scrape)}')
        print(f'Now have {leads_found} leads')
        print('-' * 40) 

        if business_list:
            #Saves the businesses got for the city just scraped, to a csv 
            save_as_csv(business_list, business_type_scrape, type_scrape, city, state_scrape)
        else:
            print(f'No businesses without websites found for {business_type_scrape} in {city}') 
    #End of scrape session, for the total cities
    print('************************* Finished Scraping *************************')  
    print('DATA: ')
    print(f'Total API Requests {total_api_requests}') 
    print(f'Total Leads found {leads_found}') 
    
#Some simple labeling for claude
def business_type_label(business_type_val: int) -> str:
    if business_type_val == 1:
        return 'car customization shops'
    elif business_type_val == 2:
        return 'home remodelers'
    else:
        return ' '
def scrape_type_label(scrape_type_val: int) -> str:
    if scrape_type_val == 1:
        return 'get leads with no site'
    elif scrape_type_val == 2:
        return 'get leads with a site, but have low review count'
    else:
        return ' '