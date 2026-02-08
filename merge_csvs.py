import glob 
import pandas as pd

def main() -> None:
    #Get type of scrape did
    business_type: str = (input('Enter the business type scraped: '))
    print(' ') 
    state: str = input('Enter the state scraped: ')
    print(' ') 
    num_cities: int =int (input(f'Enter the number of cities scraped in {state}: '))

    #Merge csvs from scraping
    with open(f'cold-leads-{business_type}-{state}-{num_cities}.csv', 'w') as output_file:
        input_file_list = glob.glob(f'cold_leads/{business_type}_*.csv')

        for input_file in input_file_list:

            with open(input_file, 'r') as source_file:
                #read and write one line at a time to the output file
                for line in source_file:
                    output_file.write(line) 
    
    #Remove dupes
    df = pd.read_csv(f'cold-leads-{business_type}-{state}-{num_cities}.csv')
    df.drop_duplicates(inplace=True)
    df.to_csv(f'cold-leads-{business_type}-{state}-{num_cities}.csv', index=False)
    
if __name__ == '__main__':
    main() 