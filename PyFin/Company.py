from datetime import datetime
#from PyFinance.Google import Extract
#from PyFin import Extract
from enum import Enum
import traceback
from PyFin.Extract import Extractor, Period 
htmlExtractor = Extractor()

# represents an address for a company
class Address(object):
    def __init__(self, m):
        self.Street  = None
        self.Zip     = None
        self.City    = None
        self.State   = None
        self.Country = None
        self.Phone   = None
        self.Fax     = None
        for k in m:
            if k == "Street":
                self.Street = m["Street"]
            elif k == "Zip":
                self.Zip = m["Zip"]
            elif k == "City":
                self.City = m["City"]
            elif k == "State":
                self.State = m["State"]
            elif k == "Country":
                self.Country = m["Country"]
            elif k == "Phone":
                self.Phone = m["Phone"][:-9]
            elif k == "Fax":
                self.Fax = m["Fax"][:-7]

# TODO: Add parsing for the URL to flesh out Description/Compensation
# Represents a person associated with a specific company
# d := a dict containing the keys present in the constructor
class RelatedPerson(object):
    def __init__(self, d):
        self.Name           = d["Name"] 
        self.Role           = d["Role"] 
        self.URL            = d["URL"]
        self.MultipleRoles  = d["Multiple Roles"] 
        self.Description    = None
        self.Compensation   = None

class IncomeStatement(object):
    def __init__(self):
        self.Empty = True
    def __str__(self):
        return "<IncomeStatement( period='%s', annual='%s', revenue='%s')" % (self.Period, self.Annual, self.Revenue) 
    def __repr__(self):
        return "<IncomeStatement( period='%s' periodEnd='%s', revenue='%s')" % (self.Period, self.Date, self.Revenue) 
            

class BalanceSheet(object):
    def __init__(self):
        self.Empty = True

class CashFlowStatement(object):
    def __init__(self):
        self.Empty = True

class KeyStats(object):
    def __init__(self, d):
        if "Net profit margin" in d:
            self.NetProfitMargin        = d["Net profit margin"] 
        else:
            self.NetProfitMargin        = None
        if "EBITD margin" in d:
            self.EBITDMargin            = d["EBITD margin"]
        else:
            self.EBITDMargin            = None
        if "Return on average assets" in d:
            self.ReturnOnAverageAssets  = d["Return on average assets"]
        else:
            self.ReturnOnAverageAssets  = None 
        if "Return on average equity" in d:
            self.ReturnOnAverageEquity  = d["Return on average equity"]
        else:
            self.ReturnOnAverageEquity  = None
        if "Employees" in d: 
            self.Employees              = d["Employees"]
        else:
            self.Employees = None
        if "CDP Score" in d:            
            self.CDPScore               = d["CDP Score"]
        else:
            self.CDPScore               = None

        if "PeriodDate" in d:            
            self.PeriodDate             = d["PeriodDate"]
        else:
            self.PeriodDate             = None 

class Company(object):

    def extractHTML(self,text):
       self.QueryText = text
       soup = self.queryHTML(text)
       if soup:
           self.assignMD(soup)
           self.assignSI(soup)
           self.assignSectorAndIndustry(soup)
           self.assignKeyStatsAndRatios(soup)
           self.assignAddress(soup)
           self.assignDescription(soup)
	   # TODO: RelatedPeople is BROKEN, need to eventually fix--commented out
	   # self.assignRelatedPeople(soup)
           self.assignFinancialStatements(soup)

    def __init__(self):
       self.declarations()
    
    def __str_meta__(self):
        return "<MetaData (Name='%s', Ticker='%s', Exchange='%s', URL='%s', Currency='%s', Close='%s' )" \
               %                                                                                         \
               ( self.Name, self.Ticker, self.Exchange, self.URL, self.Currency, self.Close )
                
    def __str_si__(self):
        return "<SummaryInfo (Range='%s', YearRange='%s', Volume='%s', Dividends='%s', Open='%s',    \
                              MarketCap='%s', PriceEarnings='%s', EarningsPerShare='%s', Shares='%s' \
                              Beta='%s', Ownership='%s' )"                                           \
                %                                                                                    \
                ( self.Range, self.YearRange, self.Volume, self.Dividends, self.Open, self.MarketCap,\
                  self.PriceEarnings, self.EarningsPerShare, self.Shares, self.Beta, self.Ownership )      
                                              
    
    def assignDescription(self,soup):
        try:
            self.CompanySummary = htmlExtractor.getCompanySummary(soup)
        except Exception:
            self.Exceptions["CommpanySummary"] = traceback.format_exc()

    # invokes Extract.Extractor to parse HTML data related to company
    # assigns related items, if keys exist for a given item in the returned dict
    def assignMD(self,soup):
        try: 
            md = htmlExtractor.getMetaData(soup)
            for k in md:
                if k == "Name":
                    self.Name = md["Name"]
                elif k == "Ticker":
                    self.Ticker = md["Ticker"]
                elif k == "Exchange":
                    self.Exchange = md["Exchange"]
                elif k == "URL":
                    self.URL = md["URL"]
                elif k == "Currency":
                    self.Currency = htmlExtractor.getCurrency(md["Currency"])
                elif k == "Price":
                    self.Close = md["Price"]
        except Exception:
            self.Exceptions["MetaData"] = traceback.format_exc()


    def assignSI( self, soup):
        try:
            si = htmlExtractor.getSummarizedInfo(soup)
            if len(si) != 0:
                self.YearRange = si["52 Week"] 
                self.Range = si["Range"]
                self.Volume = si["Volume"]
                self.Open = si["Open"]
                self.MarketCap = si["MarketCap"]
                self.PriceEarnings = si["P/E"]
                self.Dividends = si["Dividends"]
                self.EarningsPerShare = si["EPS"]
                self.Shares = si["Shares"]
                self.Beta = si["Beta"]
                self.Ownership = si["Ownership"]
        except Exception:
            self.Exceptions["SummaryInfo"] = traceback.format_exc()

    def assignSectorAndIndustry(self,soup):
        try:
            res = htmlExtractor.getSectorAndIndustry(soup)
            if "Sector" in res:
               self.Sector = str(res["Sector"])[2:].replace("'","");
            if "Industry" in res:
               self.Industry = str(res["Industry"])[2:].replace(" - NEC'","").replace("'","")
        except Exception:
            self.Exceptions["assignSectorAndIndustry"] = traceback.format_exc()
    
    def assignKeyStatsAndRatios(self, soup):
        ksr = htmlExtractor.getKeyStatsAndRatios(soup)
        if ksr:
            if Period.Quarter in ksr:
                self.KeyStats[Period.Quarter] = KeyStats( ksr[Period.Quarter])
            if Period.Year in ksr:
                self.KeyStats[Period.Year] = KeyStats( ksr[Period.Year])
        """
        try:
            ksr = htmlExtractor.getKeyStatsAndRatios(soup)
            if ksr:
                self.KeyStats[Extract.Period.quarter] = KeyStats( ksr[Extract.Period.quarter])
                self.KeyStats[Extract.Period.year] = KeyStats( ksr[Extract.Period.year])
        except Exception:
            self.Exceptions["KeyStats"] = traceback.format_exc()
        """
    def assignAddress(self, soup):
        try:
            add = htmlExtractor.getAddress(soup)
            self.Address = Address(add)
        except Exception:
            self.Exceptions["Address"] = traceback.format_exc()

    def assignRelatedPeople( self, soup ):
        try:
            if not self.RelatedPeople:
                self.RelatedPeople = []
            rp = htmlExtractor.getRelatedPeople(soup)
            for p in rp:
                i = RelatedPerson(p)
                self.RelatedPeople.append(i)
        except Exception:
             self.Exceptions["RelatedPeople"] = traceback.format_exc()


    def assignFinancialStatements(self, soup):
        L = []

        """
        try:
            L = htmlExtractor.getFinancialStatements(soup) 
        except Exception:
            self.Exceptions["getFinancialStatements"] = traceback.format_exc()

        if not L or len(L) == 0:
            return
        try:
            if len(L[0]) > 0:
                self.isQ = htmlExtractor.createIncomeStatements(L[0][0])
        except Exception:
            self.Exceptions["isQ"] = traceback.format_exc()
         
        try:
            if len(L[0]) > 0:
                self.isA = htmlExtractor.createIncomeStatements(L[0][1])
        except Exception:
            self.Exceptions["isA"] = traceback.format_exc()
        
        try:
            if len(L) > 1:
                self.bsQ = htmlExtractor.createBalanceSheets(L[1][0], Extract.Period.quarter)
        except Exception:
            self.Exceptions["bsQ"] = traceback.format_exc()
        
        try:
            if len(L[1]) > 0:
                self.bsA = htmlExtractor.createBalanceSheets(L[1][1], Extract.Period.year)
        except Exception:
            self.Exceptions["bsA"] = traceback.format_exc()
        
        try:
            if len(L) > 1:
                self.cfQ = htmlExtractor.createCashFlowStatements(L[2][0])
        except Exception:
            self.Exceptions["cfQ"] = traceback.format_exc()
        
        try:
            if len(L) > 1 and len(L[1]) > 1:
                self.cfA = htmlExtractor.createCashFlowStatements(L[2][1])
        except Exception:
            self.Exceptions["cfA"] = traceback.format_exc()

        """ 
        L = htmlExtractor.getFinancialStatements(soup)
        self.isQ = htmlExtractor.createIncomeStatements(L[0][0])
        self.isA = htmlExtractor.createIncomeStatements(L[0][1])
        self.bsQ = htmlExtractor.createBalanceSheets(L[1][0], Period.Quarter)
        self.bsA = htmlExtractor.createBalanceSheets(L[1][1], Period.Year)
        self.cfQ = htmlExtractor.createCashFlowStatements(L[2][0])
        self.cfA = htmlExtractor.createCashFlowStatements(L[2][1])
        
        if self.isQ:
            for i in self.isQ:
                self.IncomeStatements.append(i)
        if self.isA:
            for i in self.isA:
                self.IncomeStatements.append(i)
        
        if self.bsQ:
            for b in self.bsQ:
                self.BalanceSheets.append(b)

        if self.bsA:            
            for b in self.bsA:
                self.BalanceSheets.append(b)
        
        if self.cfQ:
            for c in self.cfQ:
                self.CashFlowStatements.append(c)
      
        if self.cfA:
            for c in self.cfA:
                self.CashFlowStatements.append(c)


    # invokes Extract.Extractor to create and return a BeautifulSoup soup object
    def queryHTML(self,text):
        try:
            return htmlExtractor.QueryHTML(text)
        except Exception:
            self.Exceptions["queryHTML"] = traceback.format_exc()
            return None

    # defines the default values for a given Company
    def declarations(self):
        self.QueryDate = datetime.now()
        self.QueryText = None
        self.Close = None
        self.Name = None
        self.Ticker = None
        self.Exchange = None
        self.URL = None
        self.Currency = None
        self.Open = None
        self.MarketCap = None
        self.PriceEarnings = None
        self.EarningsPerShare = None
        self.Shares = None
        self.Beta = None
        self.Ownership = None
        self.Sector = None
        self.Industry = None
        self.DailyRange = []
        self.Dividends = []
        self.YearRange  = []
        self.Volume     = []
        self.KeyStats = {}
        self.Address = None
        self.RelatedPeople = []
        self.IncomeStatements = []
        self.BalanceSheets = []
        self.CashFlowStatements = []
        self.Range = []
        self.CompanySummary = None
        # auxiliary temp storage for financial statements functions
        self.isQ = None
        self.isA = None
        self.bsQ = None
        self.bsA = None
        self.cfQ = None
        self.cfA = None
        # for debugging
        self.Exceptions = {}

