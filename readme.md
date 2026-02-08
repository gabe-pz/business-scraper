
# A Simple Business Scraper

#### Introduction

One of my buddies saw a **short form video** talking about how a good way to make money, was to cold call business owners with no website, and try to sell them one for their business, so he decide to pursue that. Though with it came the problem of actually finding a good number of businesses to call that don't have websites. So I created this simple business scraper for him to use 

  
## Overview

#### Idea

The idea of this was to simply input a *general business type*(i.e handyman, auto body), a state, and the number of cities within that state. Then the scraper will generate you a list of businesses without websites, ready for cold calling. Where number of cities input is proportional to coverage of state 

#### How it works
The scraper uses the Google Places API to fetch Google business listings, filters for those without a linked website and that meet a certain criteria, and saves the results to a CSV file, doing this for each search query, for each city, in the state, thus creating multiple CSV files that can be merged and cleaned in merge_csvs.py. 

The general process goes like,
- The search queries are expanded by taking initial inputted business type and sending it to Claude, which generates adjacent search queries to broaden coverage.
-Business data is then fetched for each search query, in each city, within the inputted state, which is done by the scraper calling the Google Places API to retrieve matching business 
- Business without a website are added to a CSV file, and then the scraper moves onto the next search query, repeating this until all queries and cities are processes 


# Usage
1. Create a file called api_keys.py in your project folder with the following functions:
	``` python
	#API Keys
	def  get_places_api_key() -> str:

		return  'YOUR_PLACES_API_KEY'

	def  get_claude_api_key() -> str:
		
		return  'YOUR_ANTHROPIC_API_KEY'
	```

2. Then create a virtual environment within your project folder, and install the following 
	``` bash

	pip  install  anthropic  requests

	```

3. And after thats done simply *run* scraper.py to try it out.

  

### Conclusions

This project was really meant for me to get a hold of python after using c++ for a while, by trying out the power of automation via APIs with python. Thus any changes or updates to the codes logic would be appreciated.