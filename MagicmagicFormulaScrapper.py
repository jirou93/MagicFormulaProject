# -*- coding: utf-8 -*-
"""
Created on Sat Apr 11 11:48:55 2020

@author: Pau
"""

import os
import requests
import csv
import argparse
import json
from datetime import datetime
from datetime import timedelta
from datetime import date
from bs4 import BeautifulSoup
from selenium import webdriver


parser = argparse.ArgumentParser()
parser.add_argument("--startDate", help = "Enter start date of interval")
parser.add_argument("--endDate", help="Enter end date of interval")
args = parser.parse_args()

#Function to get the stocks that the Magic Formula suggest
def queryStocks():
    return False
    
#Current directory where is located the script
currentDir = os.path.dirname(__file__)
currentDate = ''
headerValues={}

url = "https://www.magicformulainvesting.com/Account/Logon"
url2 = "https://www.magicformulainvesting.com/Screening/StockScreening"
# In this line I specify the agent to log in in the webpage
headers = {
        'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36'
}
headers2 = {
    'accept': '*/*',
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'ca-ES,ca;q=0.9,en;q=0.8,es;q=0.7',
    'content-length': '51',
    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'cookie': '__cfduid=d42503d44298cea26082074ca7f69a4ff1584359554; .ASPXAUTH=478D5C5C41A9E936552CC5DE4AE4CB22A47E90702EBA373C45A160603B1221EDD5D6662E8F245689EA90D2CD53B93CC55963A98CBB98B5EB752E64C579CF7FA5D1DC393109DECC2BBA44B109A88F657E74BB997C4E9E92C49A18A7A9111DCB38D46A175AF873BED079FB4E5E95903378C6B2CD408BE560D5C6DD0F75B61F699FFE0EDD2A548D62A5867837F5682C1575FE95DF10E7167EEE6A3A86194643A4E625084FFBDD84D4045C64FDCA78E7DEC0',
    'origin': 'https://www.magicformulainvesting.com',
    'referer': 'https://www.magicformulainvesting.com/Screening/StockScreening',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.92 Safari/537.36',
    'x-requested-with': 'XMLHttpRequest'      
}
# Headers that we will use to run thestock screener
stockData = {
       'MinimumMarketCap': '50',
       'Select30': 'true',
       'stocks': 'Get+Stocks' 
}
# Function to read the credentials to login in the Magic Formula
def importCredentials(path):
    data = ""
    with open(path) as f:
        data = json.load(f)
        f.close()
    return data

# current direcotry where is located the script
currentDir = os.getcwd()
credentialsDir = currentDir + "\\credentials\\login.txt"

login_data = importCredentials(credentialsDir)

# This function will find all the stocks codes that can be found in the "table"
def getStocksCode(table) :
    stocks = []
    index = 0
    for row in table.findAll("tr"):
        if (index > 0):
            #This is because exists rowspan, if not use the previous category
            cells = row.findAll('td')
            #name = cells[0].find(text=True) 
            code = cells[1].find(text=True) 
            #MketCap = cells[2].find(text=True) 
            #date = cells[3].find(text=True) 
            #quarterData = cells[4].find(text=True) 
            #stockInfo = [name,code,MketCap,date,quarterData]
            stockInfo = code
            stocks.append(stockInfo)
        index+=1
    return stocks

#This function will build the Financial data of a stock that we found in the Finviz page.
def getFinancialData(table):
    stockInfo = []
    for row in table.findAll("tr"):
        j = 1
        for e in row.findAll("td"):
            if j > 2 and j%2 == 0:
                # This is because we have the information in the multiple of 2 cells.
                # At position 2 we have Index info that we don't need it
                stockInfo.append(e.find(text=True))
            j +=1
    return stockInfo

# This function will rebuild the dataset of magic formula Table to just 2 columns
# First column will conain the date and the second one the stocks separated by _
def transformStockData(data) :
    # First create an array with just the codes of the  stocks  that are in the second column
    codes= []
    for d in data :
        codes.append(d)
    # Get the date of today
    day = date.today().isoformat()
    # get an unique string with all the stocks separated by _
    stocks = '_'.join(codes)
    return [day, stocks]
    


#This funciton will write a CSV in the output filepath with the Financial Data
def writeDataFinancial(filepath, data):
    # Overwrite or create tge specified file.
    file = open(filepath, "w+")  
    # Write all the data in CSV format
    if len(data) == 1 :
        #Special case when we just have 1 line
        for i in range(len(data[0])):
            file.write(data[0][i] + ';')
    else: 
        for i in range(len(data)):
            for j in range(len(data[i])) :
                file.write(data[i][j] + ';')
            file.write("\n")
    file.close()
  
# This function will read a CSV given by the filepath:
def readData(filepath):
    # First check the file exists
    if os.path.isfile(filepath):
        output = []
        with open(filepath, newline= '') as csvfile:
            output = list(csv.reader(csvfile))
            csvfile.close()
        return output
    return []

#This function will add the Date to the financial Matrix
def financialAddDate(matrix) :
    # Get the date of today
    day = date.today().isoformat()
    output = []
    for e in matrix :
        e.insert(0,day)
        output.append(e)
    return output

# Function to add the new lines to Financials Dataset.
def addFinancialLines(oldMat, newMat) :
    for e in newMat :
        oldMat.append(e)
    return oldMat

magicFormula = []
# Start the session to log in in the page
with requests.Session() as s:
    #Make a post to the webpage of the login with the login data and the headers that we need to log in
    r = s.post(url, data = login_data, headers = headers)
    stocks = s.post(url2, data = stockData)
    soup = BeautifulSoup(stocks.text, "html.parser")
    table = soup.find("table", {"class":"divheight screeningdata"})
    magicFormula = getStocksCode(table)

# Once we have the information about the stocks, I need the financial information of all of them
# Webside where I can find all the Financial Data.
finviz = "https://finviz.com/quote.ashx?t="
stocksInfo = []
# Start the session to log in in the page
with requests.Session() as s:  
    for stock in magicFormula :
        code = stock
        url = finviz+str(code)
        r = s.post(url, headers = headers)
        soup = BeautifulSoup(r.text, "html.parser")
        table = soup.find("table", {"class":"snapshot-table2"})
        info = getFinancialData(table)
        info.insert(0,code)
        stocksInfo.append(info)

# We update the two CSV files that we have in folder /datasets

# Datasets folder directory
datasetDir = currentDir + "\\datasets"
filename1 = "magic_formula_stocks.csv"
filename2 = "financial_data.csv"
filePath1 = os.path.join(datasetDir, filename1)
filePath2 = os.path.join(datasetDir, filename2)
# First we read the data that we already have on the file
stocksData = readData(filePath1) 
# Append of the stocks from Magic Formula
stocksData.append(transformStockData(magicFormula))
# Save all the magic formula results
writeDataFinancial(filePath1, stocksData)
# Read of Financial historical Data
financialData = readData(filePath2)
# Append the new financial Data
financialData = addFinancialLines(financialData, financialAddDate(stocksInfo))
writeDataFinancial(filePath2, financialData)
