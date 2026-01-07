import requests, csv, time, os #type: ignore
from datetime import date
from api_keys import get_places_api_key, get_claude_api_key
from anthropic import Anthropic 


#API Keys, Replace with your own API key
API_KEY_PLACES: str = get_places_api_key()
API_KEY_CLAUDE: str = get_claude_api_key()

#Create directory to save CSVs to 
directory_name = 'cold_leads'
os.makedirs(directory_name, exist_ok=True) 

#Request URLs
url_places: str = 'https://places.googleapis.com/v1/places:searchText'
url_geo: str = 'https://maps.googleapis.com/maps/api/geocode/json' 

#Header for the POST request for places API
headers: dict[str, str] = {
    'Content-Type': 'application/json',
    'X-Goog-Api-Key': API_KEY_PLACES,
    'X-Goog-FieldMask': 'places.displayName,places.websiteUri,places.nationalPhoneNumber,nextPageToken,places.googleMapsUri,places.userRatingCount,places.photos'
}

#Initalize claude client for use
client = Anthropic(api_key=API_KEY_CLAUDE)  


#Simple string to list function. Added for fun
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
def scraper(state: str, city: str, search_type: list[str], type_scrape: int) -> tuple[list[dict[str, str]], int]: 
    api_requests: int = 0
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
    #Parameters for geo request
    params: dict[str, str] = {
        'address': f'{city}, {state}',
        'key': API_KEY_PLACES
    }
    
    #Get cords of current city, for use in location bias
    response_geo: requests.models.Response = requests.get(url_geo, params=params)
    data_geo = response_geo.json() 
    api_requests += 1
    if(response_geo.status_code != 200):
        print(f'Error: {response_geo.status_code}') 
        print(f'Response: {response_geo.text}')
        print('Failed')  
        return ([], 0)
    
    #Store cords
    city_lat: str = data_geo['results'][0]['geometry']['location']['lat']
    city_lng: str = data_geo['results'][0]['geometry']['location']['lng']

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

def save_as_csv(business_list: list[dict[str, str]], business_type_scrape: str, type_scrape: int, city_scrape: str, state_scrape: str) -> None:
    today = date.today()
    filename: str = f'{directory_name}/{business_type_scrape}_{city_scrape}_{state_scrape}_{today}.csv'
    
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

def scraper_run_loop(state_scrape: str, business_type_scrape: str, type_scrape: int, num_cities: int) -> None:  
    leads_found: int = 0
    total_api_requests: int = 0 

    #Inital search query
    search_queries = [business_type_scrape] #Type ignore
     
    #Generate city list
    message_cities = client.messages.create(
        max_tokens=1024, 
        
        messages=[{
            'content':  f"""
            Task: 
            Generate me a comma seperated list of {num_cities} cities in {state_scrape}, 
            that are good cities to cold call {business_type_scrape}, to try and sell them a website, 
            in this format-> city1, city2, city 3. 
            -----------------------------------------------------------------------------------------------------------
            Requirements:
            1. Respond with only the list of cities, nothing else. 
            2. Ensure the cities are not too close to each other
            3. Ensure the cities are not too small
            """,
            'role': 'user', 
        }],

        model='claude-sonnet-4-5-20250929'
    )
    cities = str_to_list(message_cities.content[0].text) #type: ignore
    
    #Generate search list
    message_queries = client.messages.create(
        max_tokens=1024,     
        messages=[{
            'content':  f"""
            Task: Generate a comma separated list of 10 distinct, adjacent business niches related to {business_type_scrape} in {state_scrape}. These niches must be high value prospects for cold calling to sell web design services.

            Requirements:

                Format: Output only the comma-separated list (e.g., search 1, search 2, search 3). No conversational filler or introductory text.

                Relevance: Each niche must be logically related to {business_type_scrape} but not a direct synonym.

                Diversity: Ensure searches represent different sub-sectors or complementary industries to avoid repetitive results.

            Intent: Focus on businesses that typically have high revenue but often have outdated or non existent websites (e.g., specialized contractors, local service providers).
            """,
            'role': 'user', 
        }],

        model='claude-sonnet-4-5-20250929'
    )
    
    #add on the additional searches to search list 
    search_queries.extend(str_to_list(message_queries.content[0].text)) #type: ignore
    print()
    print('Search Queries')  
    for search in search_queries: print(search)
    print() 

    for city in cities:
        business_list, api_requests = scraper(state_scrape, city, search_queries, type_scrape)  
        
        leads_found += len(business_list) 
        total_api_requests += api_requests
        
        #UI 
        print('-' * 40) 
        print(f'Finished scraping {city} for {business_type_scrape}')
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
    