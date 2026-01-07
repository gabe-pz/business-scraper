from scraper_logic import scraper_run_loop

def main() -> None:

    #Get input data from user
    business_type: str = (input('Enter the business type to scrape: '))
    print(' ') 
    scrape_type_val: int = int(input('Enter the type of scrape to do(1 = get cold leads with no sites; 2 = get leads with a site, but with low review count): '))
    print(' ') 
    state: str = input('Enter the state to scrape: ')
    print(' ') 
    num_cities: int =int (input(f'Enter the number of cities to scrape in {state}: '))

    #Check input data
    print()
    print('*****INPUTED DATA*****')
    print(f'Business type scraping: {business_type}') 
    print()
    print(f'Type of scraping: {'get cold leads with no sites' if scrape_type_val == 1 else 'get leads with a site, but with low review count'}') 
    print()
    print(f'State scraping: {state}')
    print() 
    print(f'Number of cities scraping in {state}: {num_cities}')
    print()

    #TO ADD: Directory created in scraper.py and csvs created for this session should go in there 

    data_check: str = input('Does the scraping input data look correct(y/n): ')
    scraper_run_loop(state, business_type, scrape_type_val, num_cities) if data_check == 'y' else print('Okay, Ending program') 

if __name__ == '__main__':
    main() 