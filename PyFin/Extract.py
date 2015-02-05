from datetime import datetime
import re
import urllib.request
from bs4 import BeautifulSoup
from enum import Enum
import PyFin.Company
#import PyFinance.Google

"""
    Enums for Company        
"""

""" """
class Period(Enum):
    Quarter = 1
    Year    = 2

""" """
class Currency(Enum):
    USD     = 1
    EUR     = 2
    GBX     = 3
    JPY     = 4
    CAD     = 5
    AUS     = 6
    CNY     = 7
    SWS     = 8
    SIG     = 9
    HKD     = 10

""" HTML Data Extractor """
class Extractor(object):
    """ For singleton pattern """    
    _instance = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Extractor, cls).__new__(cls, *args, **kwargs)
            return cls._instance

    def __init__(self):        
        self.currencyMap = { Currency.USD:"United States Dollar", Currency.EUR:"Euro", Currency.GBX:"British Pound", \
                             Currency.JPY:"Yen", Currency.CAD:"Canadian Dollar", Currency.AUS:"Australian Dollar",   \
                             Currency.CNY:"Chinese Yuan",  Currency.SWS:"Swiss Franc", 				     \
			     Currency.SIG: "Signapore Dollar", Currency.HKD: "Hong Kong Dollar" 		     \
                           }

        self.yearMap  = { "10":2010,     "11":2011,   "12":2012,   "13":2013,   "14":2014,   "15":2015,   "16":2016, \
                          "2010":2010, "2011":2011, "2012":2012, "2013":2013, "2014":2014, "2015":2015, "2016":2016            
               		}

        self.monthMap = { "Jan":1, "Feb":2, "Mar":3, "Apr":4, "May":5, "Jun":6, "Jul":7, "Aug":8, "Sep":9, "Oct":10, \
			  "Nov":11, "Dec":12 									     			
                        }

    ## Aux function to get currency based on text input 
    def getCurrency(self,x):
        if "USD" in x:
            return Currency.USD
        elif "EUR" in x:
            return Currency.EUR
        elif "GBX" in x:
            return Currency.GBX
        elif "JPY" in x:
            return Currency.JPY
        elif "CAD" in x:
            return Currency.CAD
        elif "AUS" in x:
            return Currency.AUS
        elif "CNY" in x:
            return Currency.CNY
        elif "SWS" in x:
            return Currency.SWS
        elif "SIG" in x:
            return Currency.SIG
        elif "HKD" in x:
            return Currency.HKD
        else:
            return None

    ## Aux function to get multipler based on text input 
    def getMultipler(self,x):
        if "Millions" or "millions" in x:
            return 1000000
        elif "Billions" or "billions" in x:
            return 1000000000
        elif "Trillions" or "trillions" in x:
            return 1000000000000
        else:
            return 1
    
    # Aux function to get return a map containing sector and industry data
    # gets the sector and industry
    # Assumption: there's a unique attribute tag id="sector" and an adjacent tag containing industry information
    # Returns: a map containing the values keyed by "Sector", "Industry" if they exist, given the assumption
    def getSectorAndIndustry(self,soup):
        try:
            ret = {}
            sec = soup.find(attrs={"id":re.compile("sector")})
            if sec:
                ret["Sector"] = sec.text.encode('utf-8')
                ind = sec.findNext('a')
                if ind:
                    ret["Industry"] = ind.text.encode('utf-8')
            else:
                ret["Sector"]   = None
                ret["Industry"] = None
            return ret
        except Exception:
            self.Exceptions["SectorAndIndustry"] = traceback.format_exc()

    def getCompanySummary(self,soup):
        return soup.find(attrs={"class":re.compile("companySummary")}).text.replace("\n","").replace("More from Reuters","")

    # Aux function to extract key stats and ratio data
    # gets the key stats and ratios
    # assumption: 
    # returns: provided that parsing was successful--a map with Period.quarter and Period.year years
    #          which map to maps containing name-value pairs for the following:
    # (1) Net profit margin
    # (2) Operating margin 
    # (3) EBITD margin 
    # (4) Return on average assets 
    # (5) Return on average equity
    # (6) Employees
    # (7) CDP Score
    # (Note: '-' values indicate nulls/unknowns/etc, and will be converted to None in the assignValueToKeyStat method )
    def getKeyStatsAndRatios(self,soup):
        ret = {}
        ksr = soup.find(attrs={"class":"quotes rgt nwp"})
        if ksr:
            header = ksr.find_all(attrs={"class":"colHeader"})
            if header:
                colHeader = ksr.find_all("td", attrs={"class":"colHeader"})
                period    = ksr.find_all("td", attrs={"class":"period"})
                lft_name  = ksr.find_all("td", attrs={"class":"lft name"})
                cH = []
                pH = []
                lN = []
                for c in colHeader:
                    cH.append(c.text.replace("\n",""))
                for p in period:
                    pH.append(p.text.replace("\n",""))
                for l in lft_name:
                    lN.append(l.text.replace("\n",""))
                q = Period.Quarter
                y = Period.Year
                l = len(cH[0])
                x = cH[0].replace(" ","")
                l = len(x)
                y = x[-3:-1]
                qYear = self.yearMap[y]
                qMonth = self.monthMap[cH[0][4:7]]
                ret[q] = {}
                ret[y] = {}
                ret[q]["PeriodDate"] = datetime( qYear, qMonth, 1,  0, 0)
                ret[y]["PeriodDate"] = datetime( self.yearMap[cH[1]],  12, 31, 0)
                ret[q]["Net profit margin"]         = self.assignValueToKeyStat(pH[0],"Net profit margin")
                ret[y]["Net profit margin"]         = self.assignValueToKeyStat(pH[1],"Net profit margin")
                ret[q]["Operating margin"]          =  self.assignValueToKeyStat(pH[2],"Operating margin")
                ret[y]["Operating margin"]          =  self.assignValueToKeyStat(pH[3],"Operating margin")
                ret[q]["EBITD Margin"]              =  self.assignValueToKeyStat(pH[4],"EBITD Margin")
                ret[y]["EBITD Margin"]              =  self.assignValueToKeyStat(pH[5],"EBITD Margin")
                ret[q]["Return on average assets"]  =  self.assignValueToKeyStat(pH[6],"Return on average assets")
                ret[y]["Return on average assets"]  =  self.assignValueToKeyStat(pH[7],"Return on average assets")
                ret[q]["Return on average equity"]  =  self.assignValueToKeyStat(pH[8],"Return on average equity")
                ret[y]["Return on average equity"]  =  self.assignValueToKeyStat(pH[9],"Return on average equity")
                ret[q]["Employees"]                 =  self.assignValueToKeyStat(pH[10],"Employees")
                ret[y]["Employees"]                 =  self.assignValueToKeyStat(pH[11],"Employees")
                ret[q]["CDP Score"]                 =  self.assignValueToKeyStat(pH[12],"CDP Score")
                ret[y]["CDP Score"]                 =  self.assignValueToKeyStat(pH[13],"CDP Score")
        return ret                            
    
    def getKeyStatsAndRatios2(self,soup):
        ret = {}
        ksr = soup.find(attrs={"class":"quotes rgt nwp"})
        # only continue parsing if an attribute with class="quotes ngt nwp" exists
        if ksr:
            header = ksr.find("thead")
            # only continue parsing if there is an thead element within ksr
            if header:
                cols = header.find("td").text.split("\n")
                # only continue parsing if ther are at least 3 elements corresponding to the collection of td elements
                if len(cols) >= 3:
                    # gets the headers for the quarter and year from the array of child "td" attributes
                    # assumption: 2nd index of cols contains quarter header, 3rd index contains the year 
                    t1 = cols[1]
                    t2 = cols[2]
                    l = len(t1)
                    q = Period.quarter
                    y = Period.year
                    ret[q] = {}
                    ret[y] = {}

                    # assign the Period Dates related to each item
                    # annual periods are assumed to end on 12/31
                    #  while quartertly periods are assumed to be related to the beginning of the first day of the associated month 
                    qYear  = self.yearMap[t1[l-3:l-1]]
                    qMonth = self.monthMap[t1[4:7]]
                    ret[q]["PeriodDate"] = datetime( qYear, qMonth, 1,  0, 0)
                    ret[y]["PeriodDate"] = datetime( self.yearMap[t2],  12, 31, 0) 
                    
                    # gets the values by extracting the underlying text contained within the attribute with class="lft name"
                    # and splitting it into a newline delimited array to parse
                    # -
                    # assumption: text is patterned in the following repeated order: key -> quarter.val, year.val 
                    vals = (ksr.find(attrs={"class":"lft name"}).text).split("\n")
                    # i is expected to alternate between 0 and 1, depending on whether a quarter or year value was previously assigned
                    i = 0
                    key = ""
                    for v in vals:
                        if v == "Net profit margin":
                            key = v
                        elif v == "Operating margin": 
                            key = v 
                        elif v == "EBITD margin": 
                            key = v 
                        elif v == "Return on average assets": 
                            key = v 
                        elif v == "Return on average equity":
                            key = v 
                        elif v == "Employees":
                            key = v 
                        elif v == "CDP Score":
                            key = v
                        elif v != "":
                            if i == 0:
                                ret[q][key] = self.assignValueToKeyStat(v,key)
                                i += 1
                            else:
                                ret[y][key] = self.assignValueToKeyStat(v,key)
                                i = 0
        return ret

    ## Converts text input into percentage float input, provided that the key belongs in the set, pct 
    def assignValueToKeyStat(self,v,key):
        pcts = set(["Net profit margin","Operating margin","EBITD margin","Return on average assets","Return on average equity"])
        if key in pcts:
            if self.isFloat(v[:-1]):
                return float(v[:-1])/100
            else:
                return None
        elif key == "Employees":
            if v == "-":
                return None
            else:
                y = v.replace(",","").replace(" ","")
                if self.isFloat(y):
                    return int(y)
                else:
                    return None


    # TODO: Improve extraction for non-American addresses		
    # TODO: Add corner case handling, as encountered, if feasible
    # Aux function to extract address related data from HTML
    # Input: Company summary site
    # Assumption: Contains a standard formatted address field for proper mappings
    # Returns: A mapping of the address items, if they exist:
    #         * Street
    #         * Zip 
    #         * City 
    #         * State
    #         * Country
    #         * Phone
    #         * Fax
    def getAddress(self,soup):
        ret = {}
        L = []
        hdg = soup.find_all(attrs={"class":"hdg"})
        for h in hdg:
            if h.text == "Address":
                sfe = h.findNext(attrs={"class":"sfe-section"})
                s = str(sfe).replace("<div class=\"sfe-section\">", "").replace("<div class=\"sfe-section\">, ", "").replace("<br/>", "\n").replace("<br>", "\n")
                rows = s.split("\n")
                for r in rows:
                    if not "<a href=\"http://maps.google.com" in r and r != "" and "</div>" not in r:
                        L.append(r)

                ret["Street"] = L[0]
                ret["Country"] = L[2]
                i = L[1].index(', ') + 1
                if ret["Country"] and ret["Country"] == "United States" and i >= 0 and len(L[1]) >= 3 + i:
                    j = L[1].index(' ', i + 3) + 1
                    if j >= 0:             
                        ret["State"] = L[1][i+1:j-1]
                        ret["City"] = L[1][0:i-1]
                        ret["Zip"] = L[1][j:]
                        if len(L) >= 4:
                            ret["Phone"] = L[3]
                        if len(L) >= 5:                
                            ret["Fax"] = L[4]
		# return after an address meeting expected parameters was extracted		        	
                return ret
	# return an empty dict if nothing meeting expected parameters encountered
        return ret
    
    # Aux function to attempt to get a list of related people from HTML 
    # Input: Summary of a company on Google Finance
    # Assumption: 
    #               - The address field exists for the company's site
    #               - For the newline delimited text contained within each element with
    #                 class="p linkbtn":
    #                                   * [0] maps to the Name   
    #                                   * [2] maps to the Role                                   
    # Returns: A list of person found, containing the following keys:
    #         - Name: string name
    #         - URL: string name
    #         - Role: string name, or a list of strings, if a comma delimter is contained 
    def getRelatedPeople(self,soup):
        ret = []
        mt = soup.find(attrs={"class":"id-mgmt-table"})
        if mt: 
            rows = mt.find_all(attrs={"class":"p linkbtn"})            
            for r in rows:
                m = {}
                rs = r.text.split("\n")
                link = r.findNext("a")["href"][2:]
                m["Name"] = rs[0]
                m["URL"] = link
                # case for handling what is assumed to be a person with multiple roles: creates a list
                if  len(rs) > 2 and "," in rs[2]:
                    cc = rs[2].count(",")
                    l = []
                    i = 0
                    while cc:
                        j = rs[2].index(",", i)
                        if cc == rs[2].count(","):
                            role = rs[2][i:j]
                        else:
                            role = rs[2][i+1:j]
                        i = j + 1
                        l.append(role)
                        cc = cc - 1
                        if cc == 0:
                            role = rs[2][j+1:]
                            l.append(role)
                    m["Role"] = l
                    m["Multiple Roles"] = True
                # standard case for handling what is assumed to be a person with a single role                
                else:                
                    m["Role"] = rs[2]
                    m["Multiple Roles"] = False 
                ret.append(m)
        return ret

    # Aux function to extract meta data from HTML
    # Input: Summary of a company on Google Finance
    # Assumption: The site contains an id="sharebox-data" containing the metadata in the "content" attribute
    # Returns: A mapping with the following keys, which are assumed to be "all or nothing":
    #         - Currency
    #         - Name
    #         - URL
    #         - Ticker
    #         - Exchange
    # (INACTIVE)         - TimeZone
    #         - Price
    #         - PriceChangePercent
    #         - QuoteTime
    #         - DataSource
    def getMetaData(self,soup):
        ret = {}
        md = soup.find(attrs={"id":re.compile("sharebox-data")})
        if md:
            ret["Currency"]             = md.find(attrs={"itemprop": re.compile("priceCurrency")     })["content"]
            ret["Name"]                 = md.find(attrs={"itemprop": re.compile("name")              })["content"]
            ret["URL"]                  = md.find(attrs={"itemprop": re.compile("url")               })["content"]
            ret["Ticker"]               = md.find(attrs={"itemprop": re.compile("tickerSymbol")      })["content"]
            ret["Exchange"]             = md.find(attrs={"itemprop": re.compile("exchange")          })["content"]
            # Immediately below varies and is not relevant to extracted data
            # ret["TimeZone"]             = md.find(attrs={"itemprop": re.compile("exchangeTimeZone")  })["content"]
            ret["Price"]                = float(md.find(attrs={"itemprop": re.compile("price")             })["content"].replace(",",""))
            
            try:
                ret["PriceChange"]          = float(md.find(attrs={"itemprop": re.compile("priceChange")       })["content"].replace(",",""))
            except:
                ret["Price"] = None
    
            try:    
                ret["PriceChangePercent"]   = float(md.find(attrs={"itemprop": re.compile("priceChangePercent")})["content"].replace(",",""))
            except:
                    ret["PriceChangePercent"] = None
        
            try:    
                ret["QuoteTime"]            = md.find(attrs={"itemprop": re.compile("quoteTime")         })["content"]
            except:
                ret["QuoteTime"] = None
            
            try:
                ret["DataSource"]           = md.find(attrs={"itemprop": re.compile("dataSource")        })["content"]
            except:
                ret["DataSource"] = None
        
        return ret    

    # Aux function to test whether input can be converted into a float
    # Input: a string
    # Assumption: None
    # Returns: Whether the string can be converted to a float without a ValueError exception
    def isFloat(self,x):
        try:
            float(x)
            return True
        except ValueError:
            return False

    # Aux function process a single line of text into numeric input or "-" if the text cannot be processed
    # Input: Text and an optional map of abbreviation : abbreviation amount
    # Assumption: Only one abbreviation type exists for the given text. 
    # Returns: Parsed text in either float form, or the default: '-' indicating nullity.
    def processLine(self,x, d):
        # assign the default multipler 
        m = 1
        # clean and sanitize the string of extraneous whitespace
        x = x.replace(" ", "").replace("\n", "")
        
        # return default
        if len(x) >= 1 and not x[0].isdigit():
            return None

            # a map d is provided, check last character for an abbreviation  
        for k in d:
            if x[-1] == k:
                x = x[:-1]
                m = d[k]
        # remove any non-digit characters from the end of the string, such as '*'
        # (Example: 1234.56*] -> 1234.56 )
        b = not x[-1].isdigit()
        while b:
            x = x[:-1]
            b = not x[-1].isdigit()
        # return either a number, or a default value, arbitrarily assigned as '-' 
        if self.isFloat(x):
            return float(x) * m
        else:
            return "-"

    # Aux function returning the number of standard number digits in the input text 
    def digitCount(self,x):
        if x:            
            digs = 0
            for i in x:
                if i.isdigit():
                    digs += 1
            return digs
        else:
            return 0

    def purgeTDClass(self,x):
        if x and "<td class=\"val\"" in x:
            y = x.replace("<td class=\"val\"","")
            return y.replace("</td>","").replace("<","").replace(">","")
        elif x:
            return x
        else:
            return ""
    
    # Aux function to process multiple lines of text into list of floats, with "-" designating nulls
    # Input: Text, a separator, and an optional map of abbreviation : abbreviation amount 
    # Assumption: All of the lines will contain the same abbreviation type, if one is found. 
    # Returns: 
    def processLines(self, x, c, d):
        # assign the default multipler and the list to be returned
        m = 1
        x = self.purgeTDClass(str(x)).replace(" ","").replace("\n","").replace("\t","")
        L = []
        y = ""

        # Error handling for malformed HTML: encountered 01/06/2015
        # TODO: Make more generalized purge function

        # TODO: Verify that this logical case works correctly 
        # return default, if there are no digits whatsoever in the input to be potentially parsed 
        if self.digitCount(x) == 0:
            return [None,None]
    
              
        # special case to handle negative number identifiers if c = '-'
        # NOTE: Arbitrarily use '$' as a dummy replacement, which may be problematic
        if c == "-" and x:
            cc = x.count("-")
            if cc > 1:
                if x[0] == "-":
                    ci = x.index("-", 1)
                    x[ci] = "$"
                    cc = x.count("-")
                    if cc > 1:
                        ci = x.index("-", 1)
                        x[ci] = "$"
                        c = "$"
            # sanitize the string of whitespace/newlines, then split is based on c
        y = x.split(c)
            # if a dict of abbreviations is given, check for the presence of abbreviations
            # and modify the split strings and multipler, if necessary 
            # ( abbreviations are expected to be on the final line of the split strings )
        for k in d:
            i = 0
            for z in y:
                if z[-1] == k:
                    z = z[:-1]
                    m = d[k]
                y[i] = z
                i += 1      

        # remove any non-digit characters from the end of the string, such as '*'
        # (Example: 1234.56*] -> 1234.56 )
        i = 0 
        for z in y:
            b = not z[-1].isdigit()
            while b:
                z = z[:-1]
                if len(z) == 0:
                    break
                b = not z[-1].isdigit()
            y[i] = z
            i += 1
        for z in y:
            if self.isFloat(z):
                L.append((float(z)*m))
            else:
                L.append(None)
        
        if len(L) == 0:
            return [None,None]
        else:
            return L 

    # Aux function which conditionally attempts to process a single line or multiple lines
    # Input: x := text, c := separator, d := mapping of -- abbreviations : abbreviation amount
    # Assumptions: The text will be mostly numeric. '$' will never be used as a separator 
    # Returns: 
    #          - If no separator parameter, or "" given, a line.
    #          - If a non-blank separator parameter is given, a list. 
    def cleanAndSplit(self, x, c, d = {}): 
        if not c or c == "":
            return self.processLine(x, d)
        else:
            return self.processLines(x, c, d)

    # Aux function to extract summary info from HTML
    # Input: Summary info site of a company
    # Assumptions: 
    #               - The site contains at least two elements with class="snap-data"
    #               - Abbreviation mappings: M -> Million, B -> Billion, T -> Trillion 
    # Returns: All-or-nothing mappings of the following:
    #           - Range
    #           - Volume
    #           - 52 Week
    #           - Open 
    #           - Market Cap
    #           - P/E
    #           - Dividends
    #           - EPS
    #           - Shares
    #           - Beta
    #           - Ownership
    def getSummarizedInfo(self,soup):
        ret = {}
        si = soup.find_all(attrs={"class":re.compile("snap-data")})
        if len(si) >= 2:
            d = {"M":1000000, "B":1000000000, "T":1000000000000}
            
            siL = si[0]

            ret["Range"]        = self.cleanAndSplit(siL.find(attrs={"data-snapfield":re.compile("range")}).findNext("td").text, "-")
            ret["Volume"]       = self.cleanAndSplit(siL.find(attrs={"data-snapfield":re.compile("vol_and_avg")}).findNext("td").text, "/", d) 
            ret["52 Week"]      = self.cleanAndSplit(siL.find(attrs={"data-snapfield":re.compile("range_52week")}).findNext("td").text, "-") 
            ret["Open"]         = self.cleanAndSplit(siL.find(attrs={"data-snapfield":re.compile("open")}).findNext("td").text, "", d) 
            # note replace("*","") for cases where the currency is denominated in GBP
            ret["MarketCap"]    = self.cleanAndSplit( siL.find(attrs={"data-snapfield":re.compile("market_cap")}).findNext("td").text.replace("*",""), "", d)
            ret["P/E"]          = self.cleanAndSplit(siL.find(attrs={"data-snapfield":re.compile("pe_ratio")}).findNext("td").text, "", d) 


            siR = si[1]

            ret["Dividends"]    = self.cleanAndSplit(siR.find(attrs={"data-snapfield":re.compile("latest_dividend-dividend_yield")}).findNext("td").text, "/")
            ret["EPS"]          = self.cleanAndSplit(siR.find(attrs={"data-snapfield":re.compile("eps")}).findNext("td").text, "", d) 
            ret["Shares"]       = self.cleanAndSplit(siR.find(attrs={"data-snapfield":re.compile("shares")}).findNext("td").text, "", d) 
            ret["Beta"]         = self.cleanAndSplit(siR.find(attrs={"data-snapfield":re.compile("beta")}).findNext("td").text, "", d) 
            ret["Ownership"]    = self.cleanAndSplit(siR.find(attrs={"data-snapfield":re.compile("inst_own")}).findNext("td").text, "", d) 
        else:
            table = soup.find("table", attrs={"class":"snap-data"})
            if table:
                keys = table.find(attrs={"class":"keys"})
                if keys: 
                    siL = keys
                    ret["Range"]        = self.cleanAndSplit(siL.find(attrs={"data-snapfield":re.compile("range")}).findNext("td").text, "-")
                    ret["Volume"]       = self.cleanAndSplit(siL.find(attrs={"data-snapfield":re.compile("vol_and_avg")}).findNext("td").text, "/", d) 
                    ret["52 Week"]      = self.cleanAndSplit(siL.find(attrs={"data-snapfield":re.compile("range_52week")}).findNext("td").text, "-") 
                    ret["Open"]         = self.cleanAndSplit(siL.find(attrs={"data-snapfield":re.compile("open")}).findNext("td").text, "", d) 
                    ret["MarketCap"]    = self.cleanAndSplit(siL.find(attrs={"data-snapfield":re.compile("market_cap")}).findNext("td").text, "", d)
                    ret["P/E"]          = self.cleanAndSplit(siL.find(attrs={"data-snapfield":re.compile("pe_ratio")}).findNext("td").text, "", d) 
                    
                    siR = keys 
                    ret["Dividends"]    = self.cleanAndSplit(siR.find(attrs={"data-snapfield":re.compile("latest_dividend-dividend_yield")}).findNext("td").text, "/")
                    ret["EPS"]          = self.cleanAndSplit(siR.find(attrs={"data-snapfield":re.compile("eps")}).findNext("td").text, "", d) 
                    ret["Shares"]       = self.cleanAndSplit(siR.find(attrs={"data-snapfield":re.compile("shares")}).findNext("td").text, "", d) 
                    ret["Beta"]         = self.cleanAndSplit(siR.find(attrs={"data-snapfield":re.compile("beta")}).findNext("td").text, "", d) 
                    ret["Ownership"]    = self.cleanAndSplit(siR.find(attrs={"data-snapfield":re.compile("inst_own")}).findNext("td").text, "", d) 
        return ret

    # Aux function to extract HTML tables with financial statement data from HTML
    # ( NOTE: Only expected to be used internally by getFinancialStatements(soup) )
    # Input: URL of the finanicals page of a company from Google Finance
    # Assumption: Contains HTML data for Balance Sheet, Income Statement, and Statement of Cash Flow
    # Returns: A list with mappings for each annual/quarterly collection of I/S, B/S, SoCF
    #          * Each mapping contains a header that maps to a list of data items, where each individual
    #          * item for a given list corresponds to a specific financial statement
    #
    #          * ["Header"][0] := Will identify the currency denomination if fed to getMultipler and/or getCurrency
    #          * ["Header"][i] := Will identify the period that all other lists are associated to given that j = i - 1.
    #                           - For example, if ["Header]"[2] = "3 months ending 2014-09-30", then it is expected that
    #                             all of the [x][1] mappings for a given x relate to a quarterly financial statement for
    #                             September 9, 2014
    #          * For the ordering of the returning list, L, the following is expected:
    #            - L[0]: Quarterly Income Statements 
    #            - L[1]: Annual Income Statements
    #            - L[2]: Quarterly Balance Sheets
    #            - L[3]: Annual Balance Sheets
    #            - L[4]: Quarterly Cash Flow Statements 
    #            - L[5]: Annual Cash Flow Statements
    # ( Notes: all data is simply mapped and extracted as is displayed the site, with some elimination of newlines ) 
    def getFinancialTables(self,urlFinancial):
        # declare return value
        L = []

        # create a BeautifulSoup object from the URL
        htmldoc = urllib.request.urlopen(urlFinancial)
        soupFS = BeautifulSoup(htmldoc)
        fst = soupFS.find_all(attrs={"id":"fs-table"})

        # if the relevant html exists, then begin parsing
        if fst:
            # for each table in the collection of table
            # expected to be ~6 tables, which represent the annual/quartertly:
            # 1) Income Statements, 2) Balance Sheets 3) Cash Flow Statements
            for t in fst:
                # get all of the rows and headers contained within a specific table
                trs = t.find_all("tr")
                ths = t.find_all("th")
                tL = []
                m = {}
                for th in ths:
                    tL.append(th.text.replace("\n",""))
                # map the "Header" key to a list of all the column headers
                # the lists are expected have 6 items for quarter and 5 for annual 
                m["Header"] = tL

                #process each row within the table
                for tr in trs:
                    # queries the first type of row header
                    h = tr.find(attrs={"class":"lft lm"})
                    if h:
                        tR = []
                        for r in tr.find_all("td", attrs={"class":re.compile("r")}):
                            tR.append(r.text)
                        # maps the header's text value to to a list containing the row data related to a specific column                        
                        m[h.text.replace("\n","")] = tR
                    else:
                        # queries the second type of row header, performing the same operations as for the first type
                        h = tr.find(attrs={"class":"lft lm bld"})
                        if h:
                            tR = []
                            for r in tr.find_all("td", attrs={"class":re.compile("r")}):
                                tR.append(r.text)
                            m[h.text.replace("\n","")] = tR
                # add each mapping to a list after all the rows have been processed
                L.append(m)                        
        return L

    # Aux function to create a dummy Statement of Cashflows for non-standard structure/currency
    # TODO: Implement fully-fledged assignment
    def createCNY_CF(self,x,y):
        # 1 - Cash Generated from (Used in) Operations
        for i in range(len(x["Cash Generated from (Used in) Operations"])):
            y[i].CashGeneratedFrom_Used_in_Operations = x["Cash Generated from (Used in) Operations"]
        
        return y        

    # Aux function to create a list of Cash Flow Statements from partially parsed HTML
    ## Input: a dict; key: text headers , value: array of data associated with each header
    #         * each array index is consistently mapped to a specific cash flow statement 
    #           for text header keys, with the exception of the "Header" key, where the 
    #           the first index contains information identifying the currency's type and 
    #           the multipler 
    ## Assumption: the value arrays are properly mapped in the input x
    #              * the dates from x["Header"] are expected to be parsed via
    #                the  getDate() function
    #              * getPeriod properly determines the period
    ## Returns: a list containing the created cash flow statements
    def createCashFlowStatements(self,x):

        # declare return list and get the multipler and currency from the dict
        statements = []
        m = self.getMultipler(x["Header"][0])
        cur = self.getCurrency(x["Header"][0])
        
        # create the cash flow statements to be assigned data from each header
        # that contains a parseable date
        # expectation: x["Header"][1] to x["Header][n] should contain information
        #              that returns a Date from getDate, ( n = len(x["Header"]) - 1 ) 
        for y in x["Header"]:
            z = self.getDate(y)
            if z:
                cf = PyFin.Company.CashFlowStatement()  
                cf.Date = z
                cf.Period = self.getPeriod(y)
                cf.Currency = cur
                statements.append(cf)

        # if there is information on the table other than the header, return "empty" statements 
        if len(x) == 1:
            return statements

        # from the source data in x, assign each full value to the associated cash flow statement 
        # ASSUMPTION: the input contains properly mapped data
        if cur == Currency.CNY:
            return createCNY_CF(x, statements)
        # 1 - Net Income/Starting Line
        i = 0
        for a in x["Net Income/Starting Line"]:
            statements[i].NetIncome = self.getValue(x["Net Income/Starting Line"][i], m)
            i += 1
        # 2 - Depreciation/Depletion
        i = 0
        for a in x["Depreciation/Depletion"]:
            statements[i].Depreciation_Depletion = self.getValue(x["Depreciation/Depletion"][i], m)
            i += 1
        # 3 - Amortization
        i = 0
        for a in x["Amortization"]:
            statements[i].Amortization = self.getValue(x["Deferred Taxes"][i], m)
            i += 1
        # 4 - Deferred Taxes
        i = 0
        for a in x["Deferred Taxes"]:
            statements[i].DeferredTaxes = self.getValue(x["Deferred Taxes"][i], m)
            i += 1
        # 5 - Non-Cash Items
        i = 0
        for a in x["Non-Cash Items"]:
            statements[i].NonCashItems = self.getValue(x["Non-Cash Items"][i], m)
            i += 1
        # 6 - Changes in Working Capital
        i = 0
        for a in x["Changes in Working Capital"]:
            statements[i].ChangesInWorkingCapital = self.getValue(x["Changes in Working Capital"][i], m)
            i += 1
        # 7 - Cash from Operating Activities
        i = 0
        for a in x["Cash from Operating Activities"]:
            statements[i].CashFromOperatingActivities = self.getValue(x["Cash from Operating Activities"][i], m)
            i += 1
        # 8 - Capital Expenditures
        i = 0
        for a in x["Capital Expenditures"]:
            statements[i].CapitalExpenditures = self.getValue(x["Capital Expenditures"][i], m)
            i += 1
        # 9 - Other Investing Cash Flow Items, Total
        i = 0
        for a in x["Other Investing Cash Flow Items, Total"]:
            statements[i].OtherInvestingCashFlowItems_Total = self.getValue(x["Other Investing Cash Flow Items, Total"][i], m)
            i += 1
        
        # 10 - Cash from Investing Activities 
        i = 0
        for a in x["Cash from Investing Activities"]: 
            statements[i].CashFromInvestingActivities = self.getValue(x["Cash from Investing Activities"][i], m)
            i += 1
        # 11 - Financing Cash Flow Items 
        i = 0
        for a in x["Financing Cash Flow Items"]:
            statements[i].FinancingCashFlowItems = self.getValue(x["Financing Cash Flow Items"][i], m)
            i += 1
        # 12 - Total Cash Dividends Paid 
        i = 0
        for a in x["Total Cash Dividends Paid"]:
            statements[i].TotalCashDividendsPaid = self.getValue(x["Total Cash Dividends Paid"][i], m)
            i += 1
        # 13 - Issuance (Retirement) of Stock, Net 
        i = 0
        for a in x["Issuance (Retirement) of Stock, Net"]:
            statements[i].Issuance_Retirement_OfStock_Net = self.getValue(x["Issuance (Retirement) of Stock, Net"][i], m)
            i += 1
        # 14 - Issuance (Retirement) of Stock, Net  
        i = 0
        for a in x["Issuance (Retirement) of Debt, Net"]:
            statements[i].Issuance_Retirement_OfDebt_Net = self.getValue(x["Issuance (Retirement) of Debt, Net"][i], m)
            i += 1
        # 15 - Cash from Financing Activities 
        i = 0
        for a in x["Cash from Financing Activities"]:
            statements[i].CashFromFinancingActivities = self.getValue(x["Cash from Financing Activities"][i], m)
            i += 1
        # 16 - Foreign Exchange Effects 
        i = 0
        for a in x["Foreign Exchange Effects"]:
            statements[i].ForeignExchangeEffects = self.getValue(x["Foreign Exchange Effects"][i], m)
            i += 1
        # 17 - Net Change in Cash 
        i = 0
        for a in x["Net Change in Cash"]:
            statements[i].NetChangeInCash = self.getValue(x["Net Change in Cash"][i], m)
            i += 1
        # 18 - Cash Interest Paid, Supplemental 
        i = 0
        for a in x["Cash Interest Paid, Supplemental"]:
            statements[i].CashInterestPaid_Supplemental = self.getValue(x["Cash Interest Paid, Supplemental"][i], m)
            i += 1
        # 19 - Cash Taxes Paid, Supplemental 
        i = 0
        for a in x["Cash Taxes Paid, Supplemental"]:
            statements[i].CashTaxesPaidSupplemental = self.getValue(x["Cash Taxes Paid, Supplemental"][i], m)
            i += 1

        return statements 

    # Aux function to create a dummy Balance Sheet from non-standard structure/currency
    def createCNY_BS(x,y):
        # 1 - Cash and short-term funds
        for i in range(len(x["Cash and short-term funds"])):
            y[i].CashGeneratedFrom_Used_in_Operations = x["Cash and short-term funds"]
        
        return y        

    # Aux function to create a list of Balance Sheets from a partially parsed dict
    # ( NOTE: The site contains no period identification in the headers for Balance Sheets,
    #         so a second identifying parameter is necessary. )
    # Input: (1) a dict; key: text headers , value: array of data associated with each header
    #        (2) the Period type of the BalanceSheets to be created 
    #         * each array index is consistently mapped to a specific cash flow statement 
    #           for text header keys, with the exception of the "Header" key, where the 
    #           the first index contains information identifying the currency's type and 
    #           the multipler 
    ## Assumption: the value arrays are properly mapped in the input x
    #              * the dates from x["Header"] are expected to be correctly parsed via
    #                the  getDateBS() function
    ## Returns: a list containing the created balance sheets 
    def createBalanceSheets(self, x, p):
        # declare return list and get the multipler and currency from the dict
        statements = []
        m = self.getMultipler(x["Header"][0])
        cur = self.getCurrency(x["Header"][0])

        # create the balance sheets to be assigned data from each header
        # that contains a parseable date
        # expectation: x["Header"][1] to x["Header][n] should contain information
        #              that returns a Date from getDate, ( n = len(x["Header"]) - 1 ) 
        for y in x["Header"]:
            z = self.getDateBS(y)
            if z:
                bs = PyFin.Company.BalanceSheet() 
                bs.Date = z
                bs.Period = p
                bs.Currency = cur
                statements.append(bs)

        # if there is information on the table other than the header, return "empty" statements 
        if len(x) == 1:
            return statements
            
        if cur == Currency.CNY:
            return createCNY_BS(x, statements)

        # from the source data in x, assign each full value to the associated cash flow statement 
        # ASSUMPTION: the input contains properly mapped data
        
        # 1 - Cash & Equivalents
        i = 0
        for a in x["Cash & Equivalents"]:
            statements[i].CashAndEquivalents = self.getValue(x["Cash & Equivalents"][i], m)
            i += 1
        # 2 - Short Term Investments
        i = 0
        for a in x["Short Term Investments"]:
            statements[i].ShortTermInvestments = self.getValue(x["Short Term Investments"][i], m)
            i += 1
        # 3 - Cash and Short Term Investments
        i = 0
        for a in x["Cash and Short Term Investments"]:
            statements[i].CashAndShortTermInvestments = self.getValue(x["Cash and Short Term Investments"][i], m)
            i += 1
        # 4 - Accounts Receivable - Trade, Net
        i = 0
        for a in x["Accounts Receivable - Trade, Net"]:
            statements[i].AccountsReceivableLessTrade_Net = self.getValue(x["Accounts Receivable - Trade, Net"][i], m)
            i += 1
        # 5 - Receivables - Other
        i = 0
        for a in x["Receivables - Other"]:
            statements[i].Receivables_Other = self.getValue(x["Receivables - Other"][i], m)
            i += 1
        # 6 - Total Receivables, Net 
        i = 0
        for a in x["Total Receivables, Net"]:
            statements[i].TotalReceivables_Net = self.getValue(x["Total Receivables, Net"][i], m)
            i += 1
        # 7 - Total Inventory 
        i = 0
        for a in x["Total Inventory"]:
            statements[i].TotalInventory = self.getValue(x["Total Inventory"][i], m)
            i += 1
        # 8 - Prepaid Expenses
        i = 0
        for a in x["Prepaid Expenses"]:
            statements[i].PrepaidExpenses = self.getValue(x["Prepaid Expenses"][i], m)
            i += 1
        # 9 - Other Current Assets, Total
        i = 0
        for a in x["Other Current Assets, Total"]:
            statements[i].OtherCurrentAssets_Total = self.getValue(x["Other Current Assets, Total"][i], m)
            i += 1
        # 10 - Total Current Assets
        i = 0
        for a in x["Total Current Assets"]:
            statements[i].TotalCurrentAssets = self.getValue(x["Total Current Assets"][i], m)
            i += 1
        # 11 - Property/Plant/Equipment, Total - Gross
        i = 0
        for a in x["Property/Plant/Equipment, Total - Gross"]:
            statements[i].Property_Plant_Equipment_Total = self.getValue(x["Property/Plant/Equipment, Total - Gross"][i], m)
            i += 1
        # 12 - Accumulate Depreciation, Total
        i = 0
        for a in x["Accumulated Depreciation, Total"]:
            statements[i].AccumulatedDepreciation_Total = self.getValue(x["Accumulated Depreciation, Total"][i], m)
            i += 1
        # 13 - Goodwill, Net
        i = 0
        for a in x["Goodwill, Net"]:
            statements[i].Goodwill_Net = self.getValue(x["Goodwill, Net"][i], m)
            i += 1
        # 14 - Intangibles, Net
        i = 0
        for a in x["Intangibles, Net"]:
            statements[i].Intangibles_Net = self.getValue(x["Intangibles, Net"][i], m)
            i += 1
        # 15 - Long Term Investments
        i = 0
        for a in x["Long Term Investments"]:
            statements[i].LongTermInvestments = self.getValue(x["Long Term Investments"][i], m)
            i += 1
        # 16 - Other Long Term Assets, Total
        i = 0
        for a in x["Other Long Term Assets, Total"]:
            statements[i].OtherLongTermAssets_Total = self.getValue(x["Other Long Term Assets, Total"][i], m)
            i += 1
        # 17 - Total Assets
        i = 0
        for a in x["Total Assets"]:
            statements[i].TotalAssets = self.getValue(x["Total Assets"][i], m)
            i += 1
        # 18 - Accounts Payable
        i = 0
        for a in x["Accounts Payable"]:
            statements[i].AccountsPayable = self.getValue(x["Accounts Payable"][i], m)
            i += 1
        # 19 - Accrued Expenses
        i = 0
        for a in x["Accrued Expenses"]:
            statements[i].AccruedExpenses = self.getValue(x["Accrued Expenses"][i], m)
            i += 1
        # 20 - Notes Payable/Short Term Debt
        i = 0
        for a in x["Notes Payable/Short Term Debt"]:
            statements[i].NotesPayable_ShortTermDebt = self.getValue(x["Notes Payable/Short Term Debt"][i], m)
            i += 1
        # 21 - Current Port. of LT Debt/Capital Leases
        i = 0
        for a in x["Current Port. of LT Debt/Capital Leases"]:
            statements[i].CurrentPortOfLongTermDebt_CapitalLeases = self.getValue(x["Current Port. of LT Debt/Capital Leases"][i], m)
            i += 1
        # 22 - Other Current liabilities, Total
        i = 0
        for a in x["Other Current liabilities, Total"]:
            statements[i].OtherCurrentLiabilities_Total = self.getValue(x["Other Current liabilities, Total"][i], m)
            i += 1
        # 23 - Total Current Liabilities
        i = 0
        for a in x["Total Current Liabilities"]:
            statements[i].TotalCurrentLiabilities =self.getValue(x["Total Current Liabilities"][i], m)
            i += 1
        # 24 = Long Term Debt
        i = 0
        for a in x["Long Term Debt"]:
            statements[i].LongTermDebt =self.getValue(x["Long Term Debt"][i], m)
            i += 1
        # 25 - Capital Lease Obligations
        i = 0
        for a in x["Capital Lease Obligations"]:
            statements[i].CapitalLeaseObligations =self.getValue(x["Capital Lease Obligations"][i], m)
            i += 1
        # 26 - Long Term Debt
        i = 0
        for a in x["Long Term Debt"]:
            statements[i].LongTermDebt =self.getValue(x["Long Term Debt"][i], m)
            i += 1
        # 27 - Total Debt
        i = 0
        for a in x["Total Debt"]:
            statements[i].TotalDebt =self.getValue(x["Total Debt"][i], m)
            i += 1
        # 28 - Deferred Income Tax
        i = 0
        for a in x["Deferred Income Tax"]:
            statements[i].DeferredIncomeTax =self.getValue(x["Deferred Income Tax"][i], m)
            i += 1
        # 29 - Minority Interest
        i = 0
        for a in x["Minority Interest"]:
            statements[i].MinorityInterest =self.getValue(x["Minority Interest"][i], m)
            i += 1
        # 30 - Other Liabilities, Total 
        i = 0
        for a in x["Other Liabilities, Total"]:
            statements[i].OtherLiabilities_Total =self.getValue(x["Other Liabilities, Total"][i], m)
            i += 1
        # 31 - Total Liabilities
        i = 0
        for a in x["Total Liabilities"]:
            statements[i].TotalLiabilities =self.getValue(x["Total Liabilities"][i], m)
            i += 1
        # 32 - Redeemable Preferred Stock, Total
        i = 0
        for a in x["Redeemable Preferred Stock, Total"]:
            statements[i].RedeemablePreferredStock_Total =self.getValue(x["Redeemable Preferred Stock, Total"][i], m)
            i += 1
        # 33 - Preferred Stock - Non Redeemable, Net
        i = 0
        for a in x["Preferred Stock - Non Redeemable, Net"]:
            statements[i].PreferredStockLessNonRedeemable_Net =self.getValue(x["Preferred Stock - Non Redeemable, Net"][i], m)
            i += 1
        # 34 - Common Stock, Total
        i = 0
        for a in x["Common Stock, Total"]:
            statements[i].CommonStock_Total =self.getValue(x["Common Stock, Total"][i], m)
            i += 1
        # 35 - Additional Paid-In Capital
        i = 0
        for a in x["Additional Paid-In Capital"]:
            statements[i].AdditionalPaidInCapital = self.getValue(x["Additional Paid-In Capital"][i], m)
            i += 1
        # 36 - Retained Earnings (Accumulated Deficit)
        i = 0
        for a in x["Retained Earnings (Accumulated Deficit)"]:
            statements[i].RetainedEarnings_AccumulationDeficit_ =self.getValue(x["Retained Earnings (Accumulated Deficit)"][i], m)
            i += 1
        # 37 - Treasury Stock - Common
        i = 0
        for a in x["Treasury Stock - Common"]:
            statements[i].TreasuryStockLessCommon =self.getValue(x["Treasury Stock - Common"][i], m)
            i += 1
        # 38 - Other Equity, Total 
        i = 0
        for a in x["Other Equity, Total"]:
            statements[i].OtherEquity_Total =self.getValue(x["Other Equity, Total"][i], m)
            i += 1
        # 39 - Total Equity
        i = 0
        for a in x["Total Equity"]:
            statements[i].TotalEquity =self.getValue(x["Total Equity"][i], m)
            i += 1
        i = 0
        # 40 - Total Liabilities & Shareholders' Equity 
        for a in x["Total Liabilities & Shareholders' Equity"]:
            statements[i].TotalLiabilitiesAndShareholdersEquity = self.getValue(x["Total Liabilities & Shareholders' Equity"][i], m)
            i += 1
        # 41 - Shares Out - Common Stock Primary Issue
        i = 0
        for a in x["Shares Outs - Common Stock Primary Issue"]:
            statements[i].SharesOutsLessCommonStockPrimaryIssue = self.getValue(x["Shares Outs - Common Stock Primary Issue"][i], m)
            i += 1
        # 42 - Total Common Shares Outstanding
        i = 0
        for a in x["Total Common Shares Outstanding"]:
            statements[i].TotalCommonSharesOutstanding = self.getValue(x["Total Common Shares Outstanding"][i], m)
            i += 1
        
        return statements 

    # Aux function  
    ## Input: Text containing text identifying whether a financial statement is quarterly or annual.
    ## Assumption: All the period cases are checked. May need to add new designations!
    ## Returns: Either the period, or None, if the parsing is unsuccessful
    def getPeriod(self,x):
        if "13 weeks" in x.lower() or "3 months" in x.lower():
            return Period.Quarter
        elif "52 weeks" in x.lower() or "12 months" in x.lower():
            return Period.Year
        else:
            return None

    # Aux function
    ## Input: header text from an income statment/cashflow HTML table
    ## Assumption: Headers for these sheets contain "ending" before the date 
    ## Returns: datetime created from a string associated with ending date in: YYYY-MM-DD format
    def getDate(self,x):
        if "ending" in x:
            i = x.index("ending") + 7
            y = x[i:]
            d = datetime( int(y[:4]), int(y[5:7]), int(y[8:])) 
            return d
        else:
            return None

    # Aux function
    ## Input: header text from a balance sheet HTML table
    ## Assumption: Headers for balance sheets begin with "As of"
    ## Returns: the associated ending date in: YYYY-MM-DD format
    def getDateBS(self,x):
        if "As of" in x:
            i = x.index("As of") + 6
            return x[i:]
        else:
            return None

    # Aux function
    ## TODO: Delete or implement
    ## PLACEHOLDER FOR NON-STANDARD INCOME STATEMENTS 
    ## THAT RESULT FROM CNY-Denominated Income Statements
    def createCNY_IS(x,y):

        # 1 - Turnover 
        for i in range(len(x["Turnover"])):
            y[i].Turnover = x["Turnover"]
        
        return y      

    # Aux function
    # Input: (1) a dict; key: text headers , value: array of data associated with each header
    #         * each array index is consistently mapped to a specific cash flow statement 
    #           for text header keys, with the exception of the "Header" key, where the 
    #           the first index contains information identifying the currency's type and 
    #           the multipler 
    ## Assumption: the value arrays are properly mapped in the input x
    #              * the dates from x["Header"] are expected to be correctly parsed via
    #                the  getDateBS() function
    ## Returns: a list containing the created income statements 
    def createIncomeStatements(self,x):
        # declare return list and get the multipler and currency from the dict
        statements = []
        m = self.getMultipler(x["Header"][0])
        cur = self.getCurrency(x["Header"][0])

        # create the balance sheets to be assigned data from each header
        # that contains a parseable date
        # expectation: x["Header"][1] to x["Header][n] should contain information
        #              that returns a Date from getDate, ( n = len(x["Header"]) - 1 ) 
        for y in x["Header"]:
            z = self.getDate(y)
            if z:
                nIS = PyFin.Company.IncomeStatement()
                # nIS = IncomeStatement()
                nIS.Date = z
                nIS.Period = self.getPeriod(y)
                nIS.Currency = cur
                statements.append(nIS)

    
        # if there is information on the table other than the header, return "empty" statements 
        if len(x) == 1:
            return statements
        
        if cur == Currency.CNY:
            return createCNY_IS(x, statements)
                
        # from the source data in x, assign each full value to the associated cash flow statement 
        # ASSUMPTION: the input contains properly mapped data
        
        # 1 - Revenue
        i = 0
        for a in x["Revenue"]:
            statements[i].Revenue = self.getValue(x["Revenue"][i], m)
            i += 1
        # 2 - Other Revenue, Total
        i = 0
        for a in x["Other Revenue, Total"]:
            statements[i].OtherRevenueTotal = self.getValue(x["Other Revenue, Total"][i], m)
            i += 1
        # 3 - Total Revenue         
        i = 0
        for a in x["Total Revenue"]:
            statements[i].TotalRevenue = self.getValue(x["Total Revenue"][i], m)
            i += 1
        # 4 - Cost of Revenue, Total
        i = 0
        for a in x["Cost of Revenue, Total"]:
            statements[i].CostOfRevenueTotal = self.getValue(x["Cost of Revenue, Total"][i], m)
            i += 1
        # 5 - Gross Profit
        i = 0
        for a in x["Gross Profit"]:
            statements[i].GrossProfit = self.getValue(x["Gross Profit"][i], m)
            i += 1
        # 6 - Selling/General/Admin. Expenses, Total
        i = 0
        for a in x["Selling/General/Admin. Expenses, Total"]:
            statements[i].Selling_General_AdminExpenseTotal = self.getValue(x["Selling/General/Admin. Expenses, Total"][i], m)
            i += 1
        # 7 - Research & Development
        i = 0
        for a in x["Research & Development"]:
            statements[i].ResearchAndDevelopment = self.getValue(x["Research & Development"][i], m)
            i += 1
        # 8 - Depreciation/Amortization
        i = 0
        for a in x["Depreciation/Amortization"]:
            statements[i].Depreciation_Amortization = self.getValue(x["Depreciation/Amortization"][i], m)
            i += 1
        # 9 Interest Expense(Income) - Net Operating
        i = 0
        for a in x["Interest Expense(Income) - Net Operating"]:
            statements[i].InterestExpense_Income_LessNetOperating = self.getValue(x["Interest Expense(Income) - Net Operating"][i], m)
            i += 1
        # 10 - Unusual Expense (Income)
        i = 0
        for a in x["Unusual Expense (Income)"]:
            statements[i].UnusualExpense_Income_ = self.getValue(x["Unusual Expense (Income)"][i], m)
            i += 1
        # 11 - Other Operating Expenses, Total
        i = 0
        for a in x["Other Operating Expenses, Total"]:
            statements[i].OtherOperatingExpenses_Total = self.getValue(x["Other Operating Expenses, Total"][i], m)
            i += 1
        # 12 - Total Operating Expense
        i = 0
        for a in x["Total Operating Expense"]:
            statements[i].TotalOperatingExpense = self.getValue(x["Total Operating Expense"][i], m)
            i += 1
        # 13 - Operating Income
        i = 0
        for a in x["Operating Income"]:
            statements[i].OperatingIncome = self.getValue(x["Operating Income"][i], m)
            i += 1
        # 14 - Interest Income(Expense), Net Non-Operating
        i = 0
        for a in x["Interest Income(Expense), Net Non-Operating"]:
            statements[i].InterestIncome_Expense_NetNonOperating = self.getValue(x["Interest Income(Expense), Net Non-Operating"][i], m)
            i += 1
        # 15 - Gain (Loss) on Sale of Assets         
        i = 0
        for a in x["Gain (Loss) on Sale of Assets"]:
            statements[i].Gain_Loss_OnSaleOfAssets = self.getValue(x["Gain (Loss) on Sale of Assets"][i], m)
            i += 1
        # 16 - Other, Net
        i = 0
        for a in x["Other, Net"]:
            statements[i].Other_Net = self.getValue(x["Other, Net"][i], m)
            i += 1
        # 17 - Income Before Tax
        i = 0
        for a in x["Income Before Tax"]:
            statements[i].IncomeBeforeTax = self.getValue(x["Income Before Tax"][i], m)
            i += 1
        # 18 - Income After Tax
        i = 0
        for a in x["Income After Tax"]:
            statements[i].IncomeAfterTax = self.getValue(x["Income After Tax"][i], m)
            i += 1  
        # 19 - Minority Interest
        i = 0
        for a in x["Minority Interest"]:
            statements[i].MinorityInterest = self.getValue(x["Minority Interest"][i], m)
            i += 1
        # 20 - Equity In Affiliates
        i = 0
        for a in x["Equity In Affiliates"]:
            statements[i].EquityInAffiliates = self.getValue(x["Equity In Affiliates"][i], m)
            i += 1
        # 21 - Net Income Before Extra. Items
        i = 0
        for a in x["Net Income Before Extra. Items"]:
            statements[i].NetIncomeBeforeExtraItems = self.getValue(x["Net Income Before Extra. Items"][i], m)
            i += 1
        # 22 - Accounting Change
        i = 0
        for a in x["Accounting Change"]:
            statements[i].AccountingChange = self.getValue(x["Accounting Change"][i], m)
            i += 1
        # 23 - Discontinued Operations
        i = 0
        for a in x["Discontinued Operations"]:
            statements[i].DiscontinuedOperations = self.getValue(x["Discontinued Operations"][i], m)
            i += 1
        # 24 - Extraordinary Item
        i = 0
        for a in x["Extraordinary Item"]:
            statements[i].ExtraordinaryItem = self.getValue(x["Extraordinary Item"][i], m)
            i += 1
        # 25 - Net Income
        i = 0
        for a in x["Net Income"]:
            statements[i].NetIncome = self.getValue(x["Net Income"][i], m)
            i += 1
        # 26 - Preferred Dividends 
        i = 0
        for a in x["Preferred Dividends"]:
            statements[i].PreferredDividends = self.getValue(x["Preferred Dividends"][i], m)
            i += 1
        # 27 - Income Available to Common Excl. Extra Items
        i = 0
        for a in x["Income Available to Common Excl. Extra Items"]:
            statements[i].IncomeAvailableToCommonExclExtraItems= self.getValue(x["Income Available to Common Excl. Extra Items"][i], m)
            i += 1
        # 28 - Income Available to Common Incl. Extra Items 
        i = 0
        for a in x["Income Available to Common Incl. Extra Items"]:
            statements[i].IncomeAvailableToCommonInclExtraItems= self.getValue(x["Income Available to Common Incl. Extra Items"][i], m)
            i += 1
        # 29 - Basic Weighted Average Shares
        i = 0
        for a in x["Basic Weighted Average Shares"]:
            statements[i].BasicWeightedAverageShares = self.getValue(x["Basic Weighted Average Shares"][i], m)
            i += 1
        # 30 - Basic EPS Excluding Extraordinary Items
        i = 0
        for a in x["Basic EPS Excluding Extraordinary Items"]:
            statements[i].BasicEPSExcludingExtraordinaryItems = self.getValue(x["Basic EPS Excluding Extraordinary Items"][i], m)
            i += 1
        # 31 - Basic EPS Including Extraordinary Items
        i = 0   
        for a in x["Basic EPS Including Extraordinary Items"]:
            statements[i].BasicEPSIncludingExtraordinaryItems = self.getValue(x["Basic EPS Including Extraordinary Items"][i], m)
            i += 1
        # 32 - Dilution Adjustment
        i = 0
        for a in x["Dilution Adjustment"]:
            statements[i].DilutionAdjustment = self.getValue(x["Dilution Adjustment"][i], m)
            i += 1
        # 33 - Diluted Weighted Average Shares
        i = 0
        for a in x["Diluted Weighted Average Shares"]:
            statements[i].DilutedWeightedAverageShares = self.getValue(x["Diluted Weighted Average Shares"][i], m)
            i += 1
        # 34 - Diluted EPS Excluding Extraordinary Items
        i = 0
        for a in x["Diluted EPS Excluding Extraordinary Items"]:
            statements[i].DilutedEPSExcludingExtraordinaryItems = self.getValue(x["Diluted EPS Excluding Extraordinary Items"][i], m)
            i += 1
        # 35 - Diluted EPS Including Extraordinary Items
        i = 0
        for a in x["Diluted EPS Including Extraordinary Items"]:
            statements[i].DilutedEPSIncludingExtraordinaryItems = self.getValue(x["Diluted EPS Including Extraordinary Items"][i], m)
            i += 1
        # 36 - Dividends per Share - Common Stock Primary Issue
        i = 0
        for a in x["Dividends per Share - Common Stock Primary Issue"]:
            statements[i].DividendsPerShareLessCommonStockPrimaryIssue = self.getValue(x["Dividends per Share - Common Stock Primary Issue"][i], m)
            i += 1
        # 37 - Gross Dividends - Common Stock
        i = 0
        for a in x["Gross Dividends - Common Stock"]:
            statements[i].GrossDividendsLessCommonStock = self.getValue(x["Gross Dividends - Common Stock"][i], m)
            i += 1
        # 38 - Net Income after Stock Based Comp. Expense
        i = 0
        for a in x["Net Income after Stock Based Comp. Expense" ]:
            statements[i].NetIncomeAfterStockBAsedCompExpense = self.getValue(x["Net Income after Stock Based Comp. Expense"][i], m)
            i += 1
        # 39 - Basic EPS after STock BAsed Comp. Expense
        i = 0
        for a in x["Basic EPS after Stock Based Comp. Expense"]:
            statements[i].BasicEPSAfterStockBAsedCompExpense = self.getValue(x["Basic EPS after Stock Based Comp. Expense"][i], m)
            i += 1
        # 40 - Diluted EPS after Stock Based Comp. Expense
        i = 0
        for a in x["Diluted EPS after Stock Based Comp. Expense"]:
            statements[i].DilutedEPSAfterSTockBasedCompExpense = self.getValue(x["Diluted EPS after Stock Based Comp. Expense"][i], m)
            i += 1
        # 41 - Depreciation, Supplemental
        i = 0
        for a in x["Depreciation, Supplemental"]:
            statements[i].Depreciation_Supplemental = self.getValue(x["Depreciation, Supplemental"][i], m)
            i += 1
        # 42 - Total Specialk Items
        i = 0
        for a in x["Total Special Items"]:
            statements[i].TotalSpecialItems = self.getValue(x["Total Special Items"][i], m)
            i += 1
        # 43 - Normalized Income Before Taxes
        i = 0
        for a in x["Normalized Income Before Taxes"]:
            statements[i].NormalizedIncomeBeforeTaxes = self.getValue(x["Normalized Income Before Taxes"][i], m)
            i += 1
        # 44 - Effect of Special Items on Incom eTaxes
        i = 0
        for a in x["Effect of Special Items on Income Taxes"]:
            statements[i].EffectOfSpecialItemsOnIncomeTaxes = self.getValue(x["Effect of Special Items on Income Taxes"][i], m)
            i += 1
        # 45 - Income Taxes Ex. Impact of Special Items
        i = 0
        for a in x["Income Taxes Ex. Impact of Special Items"]:
            statements[i].IncomeTaxesExImpactOFSpecialItems = self.getValue(x["Income Taxes Ex. Impact of Special Items"][i], m)
            i += 1
        # 46 - Normalized Income After Taxes
        i = 0
        for a in x["Normalized Income After Taxes"]:
            statements[i].NormalizedIncomeAfterTaxes = self.getValue(x["Normalized Income After Taxes"][i], m)
            i += 1
        # 47 - Normalized Income Avail to Common
        i = 0
        for a in x["Normalized Income Avail to Common"]:
            statements[i].NormalizedIncomeAvailToCommon = self.getValue(x["Normalized Income Avail to Common"][i], m)
            i += 1
        # 48 - Basic Normalized EPS
        i = 0
        for a in x["Basic Normalized EPS"]:
            statements[i].BasicNormalizedEPS = self.getValue(x["Basic Normalized EPS"][i], m)
            i += 1
        # 49 - Diluted Normalized EPS
        i = 0
        for a in x["Diluted Normalized EPS"]:
            statements[i].DilutedNormalizedEPS = self.getValue(x["Diluted Normalized EPS"][i], m)
            i += 1

        return statements 

    # Aux function 
    # #TODO: COMMENTARY!!!!
    #
    def getValue( self, x, y):
        if x == "-" or y == "-":
            return None
        x1 = str(x).replace(",","")
        x2 = str(y).replace(",","")
        return float(x1) * float(x2)


    # Aux function
    def getFinancialStatements(self,soup):
        financialsURL = "https://www.google.com"
        suffix = None
        data   = None
        for link in soup.find(attrs={"class":"fjfe-nav"}).find_all("a"):
            if "Financials" in link.text:
                suffix = link["href"]
        if suffix:
            financialsURL += suffix
            data = self.getFinancialTables(financialsURL)
            if data:
                return [ [ data[0], data[1] ], [data[2], data[3]], [data[4], data[5]] ]
        return None

    def QueryHTML(self,term):
        t = term.replace("\"","")
        if "https://www.google.com/finance?cid=" not in t:
            url  = "http://www.google.com/finance?q=" + t 
        else:
            url = t 
        doc  = urllib.request.urlopen(url)
        soup = BeautifulSoup(doc)
        return soup
