import requests, csv, time, os, math #type: ignore
from api_keys import get_places_api_key, get_claude_api_key
from anthropic import Anthropic 

#Conversion constants
RADIUS_EARTH: float = 6.371 * (10**6)
PI: float = math.pi

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
    'X-Goog-FieldMask': 'places.displayName,places.websiteUri,places.nationalPhoneNumber,places.userRatingCount,places.photos,nextPageToken'
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
def scraper(state: str, city: str, search_type: list[str], num_city: int) -> tuple[list[dict[str, str]], int]: 
    api_requests: int = 0
    
    #List for filtering
    blacklist_words: list[str] = [
        'auto glass', 'windshield', 'collision', 'body shop',
        'auto body', 'auto repair', 'car repair', 'dent removal',
        'dent repair', 'cell phone', 'cellular', 'phone repair',
        'iphone', 'console repair', 'game', 'gaming', 'tv repair',
        'television', 'electronics', 'computer repair', 'pc repair',
        'janitorial', 'maid', 'cleaning service', 'appliance repair',
        'towing', 'mobile home parts', 'paint & body', 'smartphone', 'phone',
        'fiberglass', 'shop', 'Oilfield', 'RPM', 'closed', 'window', 'tint'  
    ]
    filtered_words: list[str] = [
        'service', 'services', 'repair', 'repairs', 'handyman', 'remodeling',
        'remodel', 'home', 'general', 'construction', 'bath', 'bathroom', 'kitchen',
        'contractors', 'HVAC', 'AC', 'painting', 'painter', 'roofers', 'roofing'
    ]

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
    
    #Creating cords for location restriction
    city_lat_0: float = data_geo['results'][0]['geometry']['location']['lat']
    city_lng_0: float = data_geo['results'][0]['geometry']['location']['lng']

    dx: int = 45000
    dy: int = 45000

    lat_py: float = float(city_lat_0) + ((dy/RADIUS_EARTH) * (180/PI))
    lat_ny: float = float(city_lat_0) + ((-dy/RADIUS_EARTH) * (180/PI))
    lng_px: float = float(city_lng_0) + ((dx/RADIUS_EARTH) * (180/PI) /math.cos(float(city_lat_0)* PI/180))
    lng_nx: float = float(city_lng_0) + ((-dx/RADIUS_EARTH) * (180/PI) /math.cos(float(city_lat_0)* PI/180))

    print(f'Low cord: ({lat_ny},{lng_nx})') 
    print(f'High cord: ({lat_py},{lng_px})')  
    print(f'STATUS: ({city}, {state}, {num_city+1})') 

    #Loop through each search type variation for a given business type
    for search in search_type:
        #Get searched data for a particular query
        next_page_token = None
        page_count: int = 0
        
        while True:
            page_count += 1

            data = {
                'textQuery': f'{search}',
                'pageSize': 20,
                'locationRestriction' : {
                    'rectangle' : {
                        'low' : {
                            'latitude' : lat_ny,
                            'longitude' : lng_nx
                        },
                        'high' : {
                            'latitude' : lat_py,
                            'longitude' : lng_px
                        }
                    }
                }
            }

            if next_page_token:
                time.sleep(5)
                data['pageToken'] = next_page_token 

            #Request places data
            response_places: requests.models.Response = requests.post(url_places, json=data, headers=headers) 
            api_requests += 1

            if response_places.status_code != 200:
                print(f'Error: {response_places.status_code}')
                print(f'Response: {response_places.text}')
                print('Failed')  
                return ([], 0)

            results = response_places.json() 

            #Loop through each business from the places API response 
            for place in results.get('places', []): 
                #Get website 
                website: str = place.get('websiteUri')
                if not website:
                    business_name: str = place.get('displayName', {}).get('text', '') 
                    business_number: str = place.get('nationalPhoneNumber', '')
                    business_photos: list = place.get('photos', []) 
                    
                    if((not business_name) or (not business_number) or (len(business_photos) == 0)):
                        continue
                    
                    #Noting business names and initalizing vars
                    name_lower: str = business_name.lower() 
                    add_bizz: bool = True
                    name_filtered: bool = False

                    #Ensure not getting blacklisted words in business names
                    for bad_word in blacklist_words:
                        if(bad_word in name_lower):
                            add_bizz = False
                            break
                            
                    for good_word in filtered_words:
                        if(good_word in name_lower):
                            name_filtered = True
                            break
                    
                    if(add_bizz and name_filtered):
                        #Labeling each unique business name and number scrape with no site
                        key = f'{business_name}|{business_number}' 
                        #If already has been labled then wont relabel and add, thus avoid duplication
                        if(key not in business_dict): 
                            business_dict[key] = {
                                'business_name': business_name, 
                                'business_number': business_number,
                            }

            #Get token for going to next page
            next_page_token = results.get('nextPageToken')
            print(f'Finished {search}, Current page -> {page_count}')
            
            if not next_page_token or page_count >= 3:
                break


    return (list(business_dict.values()), api_requests)

def save_as_csv(business_list: list[dict[str, str]], business_type_scrape: int, city_scrape: str) -> None:
    filename: str = f'{directory_name}/{business_type_scrape}_{city_scrape}.csv'
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=['business_name', 'business_number'])
        writer.writerows(business_list)

def scraper_run(state_scrape: str, business_type_scrape: int,  num_cities: int) -> None:  
    leads_found: int = 0
    total_api_requests: int = 0 
    search_queries: list[str] = [] 

    #Generate list of cities, for (lat, lng) pt's
    message_cities = client.messages.create(
            max_tokens=16000,
            messages=[{
                'content': f"""
                Generate a comma separated list of {num_cities} cities in {state_scrape} that provides maximum geographic coverage of the entire state.

                Format: city1, city2, city3, ..., cityN

                Requirements:
                1. Respond with only the list, nothing else
                2. Distribute cities evenly across the state, north, south, east, west, and central regions
                3. Space cities at least ~100km apart to minimize overlap 
                4. Population minimum: ~100,000 residents
                5. Prioritize cities that are wealthy cities 
                """,
                'role': 'user', 
            }],
            model='claude-opus-4-6'
    ) 
    cities = str_to_list(message_cities.content[0].text) #type: ignore

    #search queries 
    if(business_type_scrape == 0):
        search_queries = [
        'handyman',
        'home remodelers',
        'general contractors',
        'kitchen and bath remodeling',
        'roofing contractors',
        'plumbers near me',
        'HVAC contractors',
        'painters',
        ]

    for num_city, city in enumerate(cities):
        business_list, api_requests = scraper(state_scrape, city, search_queries, num_city)   
        
        leads_found += len(business_list) 
        total_api_requests += api_requests
        
        #User output
        print('-' * 40) 
        print(f'Finished scraping {city} for {business_type_scrape}')
        print(f'Now have {leads_found} leads')
        print('-' * 40) 

        if business_list:
            #Saves the businesses got for the city just scraped, to a csv 
            save_as_csv(business_list, business_type_scrape, city)
        else:
            print(f'No businesses without websites found for {business_type_scrape} in {city}') 
    
    #End of scrape session, for the total cities
    print('************************* Finished Scraping *************************')  
    print('DATA: ')
    print(f'Total API Requests {total_api_requests}') 
    print(f'Total Leads found {leads_found}') 
    