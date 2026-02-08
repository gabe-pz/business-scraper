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
    all_dfs = []
    input_file_list = glob.glob(f'cold_leads/{business_type}_*.csv')

    for input_file in input_file_list:
        # Read each CSV with 3 columns: company, phone, url, and append to all_dfs list
        df_temp = pd.read_csv(input_file, header=None, names=['company', 'phone', 'url'])
        all_dfs.append(df_temp)
    
    #Combine all dataframes
    combined_df = pd.concat(all_dfs, ignore_index=True)
        
    # Create the output dataframe with correct column structure
    output_df = pd.DataFrame({
        'firstname': 'Jon',    
        'lastname': 'Jones',       
        'phone': combined_df['phone'],  
        'email': 'jonjones@gmail.com',         
        'company': combined_df['company'],
        'title': 'Lock In'          
    })
    
    # Remove duplicates
    output_df.drop_duplicates(inplace=True)
    
    # Save to CSV
    output_df.to_csv(f'cold-leads-{business_type}-{state}-{num_cities}.csv', index=False)
    
    print(f'\nMerged {len(input_file_list)} CSV files into -> cold-leads-{business_type}-{state}-{num_cities}.csv')
    print(f'Total leads after removing dupes: {len(output_df)}')
if __name__ == '__main__':
    main() 