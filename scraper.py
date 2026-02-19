from scraper_logic import scraper_run

def main() -> None:
    #Get input data from user
    business_type: int = int(input('Enter the business type to scrape: '))
    print() 
    state: str = input('Enter the state to scrape: ')
    print() 
    num_cities: int = int(input(f'Enter the number of cities to scrape in {state}: '))

    #Check input data
    print()
    print('*****INPUTED DATA*****')
    print(f'Business type scraping: {business_type}') 
    print()
    print(f'State scraping: {state}')
    print() 
    print(f'Number of cities scraping in {state}: {num_cities}')
    print()
    data_check: str = input('Does the scraping input data look correct(y/n): ')
    
    #Run
    scraper_run(state, business_type, num_cities) if data_check == 'y' else print('Okay, Ending program') 
    
if __name__ == '__main__':
    main() 