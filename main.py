from scraper_logic import business_type_label, scrape_type_label, scraper_run_loop, str_to_list
from anthropic import Anthropic 
from api_keys import get_claude_api_key 

def main() -> None:
    #Initalize claude client
    client = Anthropic(api_key=get_claude_api_key()) #Use own api key

    #Get input data from user
    business_type_val: int = int(input('Enter the business type to scrape(1 = car customization shops, 2 = home remodeling): '))
    print(' ') 
    scrape_type_val: int = int(input('Enter the type of scrape to do(1 = get leads w no sites, 2 = get leads w site but low review count): '))
    print(' ') 
    state: str = input('Enter the state to scrape: ')
    print(' ') 
    num_cities: int =int (input(f'Enter the number of cities to scrape in {state}: '))

    #Check input data
    print(' ')
    print('*****INPUT DATA*****')
    print(f'Business type scraping: {business_type_label(business_type_val)}') 
    print(' ')
    print(f'Type of scraping: {scrape_type_label(scrape_type_val)}') 
    print(' ')
    print(f'State scraping: {state}')
    print(' ') 
    print(f'Number of cities scraping in {state}: {num_cities}')
    print(' ')

    data_check: str = input('Does the scraping input data look correct(y/n): ')

    #If data looks good then move on
    if(data_check == 'y'):
        #Generate city list
        message = client.messages.create(
            max_tokens=1024, 
            
            messages=[{
                'content':  f"""
                Task: 
                Generate me a comma seperated list of {num_cities} cities in {state}, 
                that are good cities to cold call {business_type_label(business_type_val)}, to try and sell them a website, 
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

        cities = str_to_list(message.content[0].text) #type: ignore
        print(f'Scraping started, scraping the state {state} and the cities of {cities}')
        
        #scraper run function
        scraper_run_loop(state, cities, business_type_val, scrape_type_val) 

    else:
        print(' ')
        print('Okay, Ending program') 

if __name__ == '__main__':
    main() 