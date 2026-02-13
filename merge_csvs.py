import pandas as pd # type: ignore
import glob, os

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
        # Read each CSV with 3 columns: company, phone, url, append the city to it, then append df to all dfs
        title = os.path.basename(input_file).split('_', 1)[1].replace('.csv', '') 
        df_temp = pd.read_csv(input_file, header=None, names=['company', 'phone', 'city']) 
        df_temp['city'] = title
        all_dfs.append(df_temp) 
    
    #Create the output dataframe, for final csv
    merged_df = pd.concat(all_dfs, ignore_index=True)
    output_df = pd.DataFrame({
        'firstname': merged_df['company'],
        'lastname': merged_df['city'],
        'phone': merged_df['phone'],
        'email': '',
        'company': '',
        'title': ''
    })

    
    # Remove duplicates
    output_df.drop_duplicates(inplace=True)
    
    # Save to CSV 
    output_df.to_csv(f'cold-leads-{business_type}-{state}-{num_cities}.csv', index=False)
    
    print(f'\nMerged {len(input_file_list)} CSV files into -> cold-leads-{business_type}-{state}-{num_cities}.csv')
    print(f'Total cold leads after removing dupes: {len(output_df)}')
if __name__ == '__main__':
    main()  
