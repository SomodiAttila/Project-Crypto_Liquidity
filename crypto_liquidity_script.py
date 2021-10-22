

# Description: A script to scrape crpyto data and create visualizations for liquidity analysis.



#Imports
import requests
from bs4 import BeautifulSoup
import urllib.parse
from selenium import webdriver
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import dataframe_image as dfi
import seaborn as sns
from datetime import date

# SCRAPING THE LIST OF TOP 20

headers = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36"}
website = 'https://coinmarketcap.com/coins/'
response = requests.get(website, headers=headers)

soup = BeautifulSoup(response.content, "html.parser")

# Need 2 classes, because the first one only gives me the top 10.

classes_to_scrape = ["sc-16r8icm-0 escjiH", "sc-1rqmhtg-0 jUUSMS"]
landing_url = []

for classes in classes_to_scrape:
    result_container = soup.find_all(class_= classes)
    
    for item in result_container:    
        landing_url.append(item.find('a').get('href'))

landing_url = [x + "markets/" for x in landing_url]

home_page = 'https://coinmarketcap.com/'

# Joining home page with url.
top_20 = []
for link in landing_url[:20]:
    top_20.append(urllib.parse.urljoin(home_page, link))

# SCRAPING THE DATA OF TOP 20

options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

wd = webdriver.Chrome('chromedriver',options=options)

# Create empty df.

coinmarket_data = pd.DataFrame(columns=['Source', 'Pairs', 'Price', '+2% Depth', '-2% Depth', 'Volume', 'Volume %', 'Confidence', 'Liquidity', 'Updated'])

# Filling empty df with the scraped data.

for link in top_20:
    wd.get(link)
    html = wd.page_source
    data = pd.read_html(html)
    coinmarket_data = coinmarket_data.append(data[0].loc[0:4, ['Source', 'Pairs', 'Price', '+2% Depth',
                                              '-2% Depth', 'Volume', 'Volume %', 'Confidence',
                                              'Liquidity', 'Updated']], ignore_index=True)

# DATA TRANSFOMRATION

class DataTransform:
    
    """A class that transforms the scraped data into the desired form."""
    
    def __init__(self, data):
        self.data = data
        
    def rename_cols(self):
        
        # Renames columns as requested.
        
        data = self.data
        data.rename(columns={'Source': 'Exchange', 'Pairs': 'Symbol'}, inplace=True)
        
        return data
    
    def base_quote(self):
        
        # Creates 2 new columns. Base and Quote from Symbol. Then reorders the columns.
        
        data = self.rename_cols()
        data[['Base', 'Quote']] = data['Symbol'].str.split('/', 1, expand=True)
        data = data[['Exchange', 'Symbol', 'Base', 'Quote', 'Price',
                                   '+2% Depth', '-2% Depth', 'Volume', 'Volume %',
                                   'Confidence', 'Liquidity', 'Updated']]
        
        return data
    
    def remove_dollar(self):
        
        # Removes dollar signs and commas.
        
        data = self.base_quote()
        new_data = data.replace({r'\$':''}, regex = True)
        new_data = new_data.replace({r'\,':''}, regex = True)
        
        return new_data
    
    
    def numeric_columns(self):
        
        # Transforms objects to numeric values.
        
        data = self.remove_dollar()
        data["Price"] = pd.to_numeric(data["Price"])
        data["+2% Depth"] = pd.to_numeric(data["+2% Depth"])
        data["-2% Depth"] = pd.to_numeric(data["-2% Depth"])
        data["Volume"] = pd.to_numeric(data["Volume"])
        data["Liquidity"] = pd.to_numeric(data["Liquidity"])
        
        return data

# instance of class
coin = DataTransform(coinmarket_data)

# transforming class instance
coinmarket_data = coin.numeric_columns()

# VISUALIZATION
class CoinViz:
    
    """A class that creates a table and a stacked barchart visualization for a given coin."""

    def __init__(self, data):
        self.data = data


    def liquidity_table(self,base):
        
        # Creates a table for a coin that summarizes its liquidity
        
        data = self.data
        base_table = data.loc[data['Base'] == base]
        table = base_table[['Symbol', 'Exchange', 'Volume', 'Volume %', '+2% Depth', '-2% Depth']]


        return table
    
    def table_style(self, base, title):
        
        # Creates a table visualization that can be saved.
        
        data = self.liquidity_table(base)
        data = data.style.format({'Volume': "{:.2E}".format,
                   '+2% Depth': "{:.2E}".format,
                   '-2% Depth': "{:.2E}".format}).hide_index().set_caption(title)
        
        
            
        dfi.export(data, str(title) + ".png")
            
        
    def bar_chart_data(self, base):
        
        # Creates a dataframe suitable for bar charts.
        
        data = self.data
        base_table = data.loc[(data['Base'] == base) & (data['Quote'].isin(["USD", "USDT"]))]
        table = base_table[['Quote','Exchange', 'Volume']]
    
    
        return table
        
    
    def liquidity_bar_chart(self, base, title):
        
        # Creates a bar chart of the volume for a given coin.
        
        data = self.bar_chart_data(base)
        data.groupby(["Quote", "Exchange"])["Volume"].sum().unstack().plot(kind='bar', stacked=True, title=title,
                                                                 ylabel='Volume', figsize=(8,8))

        plt.xticks(rotation=0, ha='center')
        matplotlib.style.use('seaborn-darkgrid')
        plt.savefig(str(title) + ".png")

# instance of viz class
coinmarket = CoinViz(coinmarket_data)

# List of coins
coins = coinmarket_data['Base'].unique()

# Creating 20 tables and 20 bar charts for the liquidity analysis

today = date.today()

for coin in coins:

    chart_title = str(coin) + " Volume " + str(today)
    table_title = str(coin) + " Top 5 Exchanges Volume " + str(today)
    
    coinmarket.liquidity_bar_chart(coin, chart_title)
    coinmarket.liquidity_table(coin, table_title)
