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
def scraper(state: str, city: str, search_type: list[str], num_city: int) -> tuple[list[dict[str, str]], int]: 
    api_requests: int = 0

    #Word filters for business name
    word_filters: list[str] = ['handyman', 'repair', 'remodel', 'remodeling', 'services', 'service', 'renovation', 'renovations', 'kitchen', 'bathroom', 'home', 'contractor', 'contracting', 'serving', 'drywall', 'solutions']  
    blacklist_words = [
        'auto glass', 'windshield', 'collision', 'body shop',
        'auto body', 'auto repair', 'car repair', 'dent removal',
        'dent repair', 'cell phone', 'cellular', 'phone repair',
        'iphone', 'console repair', 'game', 'gaming', 'tv repair',
        'television', 'electronics', 'computer repair', 'pc repair',
        'janitorial', 'maid', 'cleaning service', 'appliance repair',
        'towing', 'mobile home parts', 'paint & body', 'smartphone', 'phone'
    ]


    business_dict: dict[str, dict[str, str]]  = {}     
    #Parameters for geo request
    params: dict[str, str] = {
        'address': f'{city}, {state}',
        'key': API_KEY_PLACES
    }
    
    #display state in
    print(f'STATUS: ({city}, {state}, {num_city+1})') 

    #Get cords of current city, for use in location bias
    response_geo: requests.models.Response = requests.get(url_geo, params=params)
    data_geo = response_geo.json() 
    api_requests += 1
    if(response_geo.status_code != 200):
        print(f'Error: {response_geo.status_code}') 
        print(f'Response: {response_geo.text}')
        print('Failed')  
        return ([], 0)
    
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
                        'radius' : 20000.0
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
                #Get website and review count 
                website: str = place.get('websiteUri')
                business_rating_count: int = place.get('userRatingCount', 0) 
                
                if not website:
                    business_name: str = place.get('displayName', {}).get('text', '') 
                    business_number: str = place.get('nationalPhoneNumber', '')
                    business_page_uri: str = place.get('googleMapsUri', '')
                    business_photos: list = place.get('photos', []) 

                    if not business_name or not business_number or business_rating_count < 5 or len(business_photos) == 0:
                        continue
                    
                    #Ensuring not taking business names with words dont want
                    name_lower = business_name.lower() 
                    add_bizz = False
                    is_blacklist = False

                    #Ensure not getting blacklisted words in business names
                    for bad_word in blacklist_words:
                        if(bad_word in  name_lower):
                            is_blacklist = True
                            break

                    if not is_blacklist:
                        for word in word_filters:
                            #If the name has one of the words want then continue to add it else dont
                            if(word in name_lower):
                                add_bizz = True 
                                break  
                    
                    if(add_bizz):
                        #Labeling each unique business name and number scrape with no site
                        key = f'{business_name}|{business_number}' 
                        #If already has been labled then wont relabel and add, thus avoid duplication
                        if(key not in business_dict): 
                            business_dict[key] = {
                                'business_name': business_name, 
                                'business_number': business_number,
                                'business_page_uri' : business_page_uri
                            }

            #Get token for going to next page
            next_page_token = results.get('nextPageToken')
            print(f'Finished {search}; Current page -> {page_count}')

            if not next_page_token or page_count >= 3:
                break


    return (list(business_dict.values()), api_requests)

def save_as_csv(business_list: list[dict[str, str]], business_type_scrape: str, city_scrape: str) -> None:
    filename: str = f'{directory_name}/{business_type_scrape}_{city_scrape}.csv'
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=['business_name', 'business_number', 'business_page_uri'])
        writer.writerows(business_list)

def scraper_run_loop(state_scrape: str, business_type_scrape: str,  num_cities: int) -> None:  
    leads_found: int = 0
    total_api_requests: int = 0 
    search_queries: list[str] = [] 

    #Generate list of cities
    message_cities = client.messages.create(
            max_tokens=16000,
            messages=[{
                'content': f"""
                Generate a comma-separated list of {num_cities} cities in {state_scrape} that provides maximum geographic coverage of the entire state.

                Format: city1, city2, city3, ...

                Requirements:
                1. Respond with only the list, nothing else
                2. Distribute cities evenly across the state — north, south, east, west, and central regions
                3. Space cities at least 20-25 miles apart to minimize overlap
                4. Include a mix of: major cities, mid-size cities, and smaller towns that serve as regional hubs
                5. Prioritize cities where {business_type_scrape} businesses are likely to operate (areas with residential growth, suburban development, or aging housing stock)
                6. Do not cluster around a single metro area — cover rural corridors and secondary markets too
                7. Population minimum: ~5,000 residents
                """,
                'role': 'user', 
            }],
            model='claude-opus-4-6'
    ) 
    cities = str_to_list(message_cities.content[0].text) #type: ignore

    #Inital search queries
    if(business_type_scrape.lower() == 'handyman'):
        search_queries = ['handyman', 'home remodelers', 'home renovations']  
    #Calling Calude to generate even bigger list of search queries
    message_queries = client.messages.create(
        max_tokens=16000,
        messages=[{
            'content': f"""
            Generate a comma-separated list of 15 Google Maps search queries that would find businesses related to "{business_type_scrape}" in {state_scrape}.

            Format: query 1, query 2, query 3, ...

            Context:
            - I'm scraping Google Places for local service businesses that lack websites, to cold call and sell them web design.
            - I already have these base queries: {search_queries}
            - Do NOT repeat or rephrase any of those existing queries.

            Requirements:
            1. Output only the comma-separated list — no preamble, no explanation
            2. Each query should be a realistic Google Maps search term (how a homeowner would search, e.g. "deck builders" not "deck construction services LLC")
            3. Target adjacent trades and sub-specialties, not synonyms of "{business_type_scrape}"
            4. Prioritize niches where businesses are likely to:
            - Be owner-operated or small crews (1-10 employees)
            - Have high revenue but poor/no online presence
            - Rely on word-of-mouth and repeat customers
            5. Cover different sub-sectors: structural, cosmetic, outdoor, specialty, emergency
            6. Avoid overly broad terms (e.g. "construction") that return large companies
            7. Avoid overly narrow terms that would return zero results
            """,
            'role': 'user',
        }],
        model='claude-opus-4-6'
    )
    search_queries.extend(str_to_list(message_queries.content[0].text)) #type: ignore
    
    #Output for user
    print('*' * 40)
    print('Search terms: ') 
    for term in search_queries:
        print(term) 
    print() 
    print('Cities: ')
    for city in cities:
        print(city)
    print()  

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
            save_as_csv(business_list, business_type_scrape , city)
        else:
            print(f'No businesses without websites found for {business_type_scrape} in {city}') 
    
    #End of scrape session, for the total cities
    print('************************* Finished Scraping *************************')  
    print('DATA: ')
    print(f'Total API Requests {total_api_requests}') 
    print(f'Total Leads found {leads_found}') 
    