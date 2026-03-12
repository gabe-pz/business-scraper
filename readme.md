
# A Simple Business Scraper

#### Introduction

One of my buddies saw a **short form video** talking about how a good way to make money, was to cold call business owners with no website, and try to sell them one for their business. Though with it came the problem of actually finding a good number of businesses to call that don't have websites. So I created this simple business scraper to solve that problem 

  
## Overview

#### Idea

The idea of this was to simply input a *specfic business niche*(i.e handyman, auto body), which are denoted with specfic codes, a state to scrape in, and the number of cities within that state, for specifying coverage. Then the scraper will generate you a list of businesses without websites, ready for cold calling.

#### How it works
The scraper uses the Google Places API to fetch Google business listings, it filters for those without a linked website and that meet a certain criteria based upon the inputed type, and saves the results to a CSV file, doing this for each search query, for each city, in the state, thus creating multiple CSV files that can be merged and cleaned in merge_csvs.py 

The general process goes like,
- The search query code is taken in from the user, and then a list of search queries is assigned for that type
-Business data is then fetched for each search query, in each city, within the inputted state, which is done by the scraper calling the Google Places API to retrieve matching business 
- Business without a website are added to a CSV file, and then the scraper moves onto the next search query, repeating this until all queries and cities are processes 


# Usage
1. Create a file called api_keys.py in your project directory with the following functions:
	``` python
	#API Keys
	def  get_places_api_key() -> str:

		return  'YOUR_PLACES_API_KEY'

	def  get_claude_api_key() -> str:
		
		return  'YOUR_ANTHROPIC_API_KEY'
	```

2. Then create a virtual environment within your project directory, and install the following 
	``` bash

	pip  install  anthropic  requests

	```

3. And after thats done simply *run* scraper.py to try it out 

