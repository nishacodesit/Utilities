"""Author Nisha M
Script to download BEA ErrorCodes from the webpage using Python

Requirements:
    - pandas
    - bs4
    - requests
    - re
    - getpass
    - subprocess
    - sys

Python:
  - 3 and above
Usage:
  - $python3  beaerrorcodes_parser.py
Output:
  - Oracle_BEA_Errorcodes.csv
 """

#Import required libraries
from bs4 import BeautifulSoup
import pandas as pd
import re
import requests
from requests.auth import HTTPProxyAuth
import getpass
import subprocess
import sys


def get_session_user():
    """
    Returns the username of current user logged into the system
    """
    res = subprocess.check_output( ["WMIC", "ComputerSystem", "GET", "UserName"], universal_newlines=True)
    _, username = res.strip().rsplit("\n", 1)
    return username.rsplit("\\", 1)[1]

def extract_htmldata(soup, tag, class_val, delimitors, returnval):
    """
    Author: Nisha M
    Takes a BeautifulSoup obj and splits based on the tag, class, delimitor
    soup - BeautifulSoup obj
    tag - html tag
    class_val = html class name
    delimitors = delimitor to split on, if multiple level of splitting needed use list of delimitors
    returnval = 0 means 'keys' list , 1 means 'values list
    """
    return [re.split(delimitors,row.get_text())[returnval] for row in soup.find_all(tag , class_=class_val) ]

def get_BEA_Errorcodes(proxyUrl):
    """
    Fetches BEA Error codes and their attributes from Oracle Products website and generates a csv file in current dir
    proxyUrl = Optional field - Supply proxy if accessing from intranet.
    """
    # URL to HTML parse for Oracle BEA Error codes
    source_url = "https://docs.oracle.com/cd/E24329_01/doc.1211/e26117/chapter_bea_messages.htm"

    #Data Dictionary:
    bea_code_dictionary = {
                        "BEA-Code": [],
                        "Description": [],
                        "Cause": [],
                        "Action": [],
                        "Level": [],
                        "Type": [],
                        "Impact": []
                        }

    username, password, proxy, port = re.split('[:,@]',proxyUrl)

    ses = requests.Session()
    ses.auth = HTTPProxyAuth(username,password)
    ses.trust_env=False

    try:
        page = ses.get(source_url,
                    proxies={"http": proxyUrl , "https": proxyUrl})
    except requests.exceptions.RequestException as e:
        print(e)
        sys.exit(1)

    #Page error handling
    if page.status_code != 200:
        print ("Error in fetching the html page, check the url ", source_url)
        sys.exit(1)

    # Parse HTML data
    soup = BeautifulSoup(page.content, 'html.parser')
    no_bea_codes = len(soup.find_all('span', class_= "msg") )
    print("No of BEA codes found are", no_bea_codes)
    #Create a df
    bea_code_df = pd.DataFrame(data=bea_code_dictionary)

    #Update the BEA Code dataframe with appropriate values from Oracle html page data
    bea_code_df['BEA-Code'] = extract_htmldata(soup, 'span','msg','[:]', 0 )
    bea_code_df['Description'] = extract_htmldata(soup, 'span','msg','[:]', 1 )
    bea_code_df['Cause'] = extract_htmldata(soup, 'div','msgexplan', '[:]', 1 )
    bea_code_df['Action'] = extract_htmldata(soup, 'div','msgaction', '[\n:]' ,1 )
    bea_code_df['Level'] = extract_htmldata(soup, 'div','msgaction', '[\n:]' ,3 )
    bea_code_df['Type'] = extract_htmldata(soup, 'div','msgaction', '[\n:]' ,5 )
    bea_code_df['Impact'] = extract_htmldata(soup, 'div','msgaction', '[\n:]' ,7 )

    if bea_code_df.isnull().any().any() == True:
        print ("There is some inconsistency with the data fetched from the page, possible missing fields")

    #Creating a csv file to save BEA Codes data from df
    out_filename = 'Oracle_BEA_Errorcodes.csv'
    bea_code_df.to_csv(out_filename, sep=',', encoding='utf-8', header=True, index=False)
    print(" The Oracle Codes are available in ", out_filename)

if __name__ == "__main__":

    print ("Fetching BEA Error-codes data from Oracle docs site....\n\n")
    username = get_session_user().lower()
    password = getpass.getpass('Enter your login password:')

    proxy_detail = 'proxy:80' #Proxy used

    proxy_string = username+':'+password+'@'+proxy_detail
    #print ("proxy used is", proxy_detail)
    get_BEA_Errorcodes(proxy_string)    # Supply proxy if accessing from intranet.
