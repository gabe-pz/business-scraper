# A Simple Business Scraper
#### Introduction 
One of my buddies saw a **short form video** talking about how a good way to make money, was to cold call business owners with no website, and try to sell them one for their business. So he decided to do so. Though with that came the problem of actually finding a good number of businesses to call, that don't have websites. So I created this simple business scraper for him to use, and this was the reason for creating this project
#### Overview of scraper
The idea of this was you input some **general business type**(i.e handyman, auto body, etc) and the scraper uses that to  create adjacent search quires, to extend the search for the inputted general business type. With each search type in a particular city and state, the scraper will then use Google Places API to fetch data for Google business within that city and state, and then will add those business who don't have a website attached, to a CSV file, and then move onto the next search type. It will continue to do this for each search type, for each city, for a state. 

## Using it 
In order to use this, you first need to create a python file with your projects folder called, **api_keys.py** and then create the functions that return each corresponding API key needed, as such 
``` python 
#API Keys

def  get_places_api_key() -> str:
	
	return  'YOUR_PLACES_API_KEY'

  

def  get_claude_api_key() -> str:
	
	return  'YOUR_ANTHROPIC_API_KEY'
```

Then create a virtual environment within your project folder, and install the following 
``` bash 
pip install anthropic requests
``` 
And after that simply *run* scraper.py and try it out. 

### Conclusions 
This project was really meant for me to get a hold of python after using c++ for a while, as well as use the power of automation and APIs with python. Thus any changes or updates to the codes logic would be appreciated.    
