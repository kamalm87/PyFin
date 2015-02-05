import datetime
from enum import Enum
from ModelDB import *
from sqlalchemy import update
import Company, Extract
# TO NOTE: May cause dependency import issues
# for error reporting
from traceback import format_exc

class CompanyDB(object):
    def __init__(self, connectionString):
        self.dbc = DBConnection(connectionString)
        self.dbw = DBWriteable(self.dbc.session)
        self.dbq = DBQuery(self.dbc.session)
        self.dbu = DBUpdater(self.dbw)
    
    def CreateAndWriteCompany(self,searchTerm,commit=False):
        c = Company.Company()
        try:
            c.extractHTML(searchTerm)
            if not c.Name or c.Name == "":
                return (False,searchTerm)
            
            # TODO: Must handle the cache mapping either here or in the DBWriter
            self.dbw.assignCompany(c,commit)                                
            return (True,(c.Name,c.Ticker))

        except Exception:
            return (False,format_exc().split("\n"))

    def QueryCompany(self,searchTerm):
        if searchTerm in self.dbc.companyNames:
            return self.QueryCompanyFromDB(searchTerm,CompanyIdentifier.name)            
        elif searchTerm in self.dbc.companyTickers:            
            return self.QueryCompanyFromDB(searchTerm, CompanyIdentifier.ticker) 
        else:
            return None

    def QueryCompanyFromDB(self,text, companyIdentifier):
        info = None
        if companyIdentifier == CompanyIdentifier.name:
            info = self.dbc.session.query(Info).filter(Info.Name == text).one()
        elif companyIdentifier == CompanyIdentifier.ticker:
            info = self.dbc.nd
            session.query(Info).filter(Info.Ticker == text).one()
        elif companyIdentifier == CompanyIdentifier.url:
            print("wut")
        else:
            print("Something went wrong in: createCompanyFromDB(self,text,companyIdentifier)\n", \
                  companyIdentifier)  
            return

        metadata = self.dbc.session.query(MetaData).filter(MetaData.info_id == info.id).one()
        summary = self.dbc.session.query(Summary).filter(Summary.info_id == info.id).one()
        
        # more than 1
        keystats = self.dbc.session.query(KeyStats).filter(KeyStats.info_id == info.id) # ADD
        
        # industry-link: Industries, IndustryLink
        industrylinks = self.dbc.session.query(IndustryLink).filter(IndustryLink.info_id == info.id).one() # multi?
        industry = self.dbc.session.query(Industries).filter(Industries.id == industrylinks.industries_id ).one()
        # exchange-link: Exchanges, ExchangeLink
        exchangelinks = self.dbc.session.query(ExchangeLink).filter(ExchangeLink.info_id == info.id).one()
        exchange = self.dbc.session.query(Exchanges).filter(Exchanges.id == exchangelinks.exchande_id).one()
        # sector-link: 
        sectorlinks = self.dbc.session.query(SectorLink).filter(SectorLink.info_id == info.id).one() # multi?
        sector = self.dbc.session.query(Sectors).filter(Sectors.id == sectorlinks.sectors_id).one()
       
        relatedpersonroles = self.dbc.session.query(RelatedPersonRole).filter(RelatedPersonRole.info_id == info.id).all()
        relatedpeople = []
        for r in relatedpersonroles:
            rp = self.dbc.session.query(RelatedPeople).filter(RelatedPeople.id == r.relatedperson_id).one()
            relatedpeople.append( (r, rp) )

        # TODO: add methods to convert DB financial statements to object financial statements
        incomestatements = self.dbc.session.query(IncomeStatements).filter(IncomeStatements.info_id == info.id).all()
        balancesheets = self.dbc.session.query(IncomeStatements).filter(IncomeStatements.info_id == info.id).all()
        cashflowstatements = self.dbc.session.query(IncomeStatements).filter(IncomeStatements.info_id == info.id).all()

        
        print("Creating some shit:",info.Name," ",  industry.Name, " ", exchange.Name, " ", sector.Name ) 
        c = Company.Company()

        return
    


    def updateCompanyDBInfo(self, companyIdentifier):
        if companyIdentifier in self.dbc.companyNames:
            companyInfo = self.dbc.session.query(Info).filter(Info.Name == companyIdentifier).one()            
            pk = companyInfo.id
            print("Found matching name: ", companyIdentifier, " PK: ", companyInfo.id) 
            self.UPDATE(companyIdentifier, pk)
        elif companyIdentifier in self.dbc.companyTickers:
            companyInfo = self.dbc.session.query(Info).filter(Info.Ticker == companyIdentifier).one()
            pk = companyInfo.id
            print("Found matching ticker: ", companyIdentifier, " PK: ", companyInfo.id)
            self.UPDATE(companyIdentifier, pk)
        else:
            print("found nothing for: ",companyIdentifier)
            return None

    # TODO: Full update method -- Info,Meta,Key,Address,RelatedPeople


class DBQuery(object):
    """" For singleton pattern """
    _instance = None
    def _new_(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(DBConnection, cls).__new__(cls, *args, **kwargs)
            return cls._instance

    def __init__(self,session):
        self.session = session
    
    def CompanyQuery(self,ticker=None,name=None):
        if name:
            info = self.InfoQuery(name=name)
            if info:
                return _createCompany(info)
        elif ticker:
            info = self.InfoQuery(ticker=ticker)
            if info:
                return _createCompany(info)
        else:
            return None

    def _createCompany(self,info):
        pk = info.id
        try:
            summary             = self.SummaryQuery(pk)
            metadata            = self.MetaDataQuery(pk)
            exchanges           = self.ExchangesQuery(pk)
            industries          = self.IndustriesQuery(pk)
            sectors             = self.SectorsQuery(pk)
            addresses           = self.AddressesQuery(pk)
            balancesheets       = self.BalanceSheetsQuery(pk)
            cashflowstatements  = self.CashFlowStatementsQuery(pk)
            incomestatements    = self.IncomeStatementsQuery(pk)
            relatedpeople       = self.RelatedPersonsQueryt(pk)

        except Exception:
            #TODO: stack_trace
            return (False,"ERORR")

    def InfoQuery(self,ticker=None,name=None):
        if name:
            return self.session.query(Info).filter(Name==name).one()
        elif ticker:        
            return self.session.query(Info).filter(Ticker==ticker).one()
        else:
            return None
    
    def SummaryQuery(self,pk):
        return self.session.query(Summary).filter(info_id==pk).one()
    
    def MetaDataQuery(self,pk):
        return self.session.query(MetaData).filter(info_id==pk).one()

    def ExchangesQuery(self,pk):
        exchanges = []
        links = self.session.query(ExchangeLink).filter(info_id==pk).all()
        for l in links:
            exchanges.append(self.session.query(Exchanges).filter(Exchanges.id == l.exchande_id).one())
        return exchanges
    
    def IndustriesQuery(self,pk):
        industries = []
        links = self.session.query(IndustryLink).filter(info_id==pk).all()
        for l in links:
            industries.append(self.session.query(Industries).filter(Industries.id == l.industries_id).one())
        return industries            

    def SectorsQuery(self,pk):
        sectors = []
        links = self.session.query(SectorLink).filter(info_id==pk).all()
        for l in links:
            sectors.append(self.session.query(Sectors).filter(Sectors.id == l.sectors_id).one())
        return sectors            
    
    def AddressesQuery(self,pk):
        return self.session.query(Addresses).filter(Addresses.info_id==pk).all()

    def BalanceSheetsQuery(self,pk):
        return self.session.query(BalanceSheets).filter(BalanceSheets.info_id==pk).all()

    def CashFlowStatementsQuery(self,pk):
        return self.session.query(CashFlowStatements).filter(CashFlowStatements.info_id==pk).all()

    def IncomeStatementsQuery(self,pk):
        return self.session.query(IncomeStatements).filter(IncomeStatements.info_id==pk).all()

    def RelatedPersonsQueryt(self,pk):
        relatedpersons = []
        links = self.session.query(RelatedPersonLink).filter(RelatedPersonLink.info_id==pk).all()
        relatedPeople = []
        for l in links:
            relatedpeople.append(self.session.query(RelatedPeople).filter(RelatedPeople.person_id==l.id).all())
        for p in relatedpeople:
            relatedpersons.append((p,self.session.query(RelatedPersonRole).filter(RelatedPersonRole.relatedperson_id==p.id).all()))
        return relatedpersons

class DBConnection(object): 
    """" For singleton pattern """
    _instance = None
    def _new_(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(DBConnection, cls).__new__(cls, *args, **kwargs)
            return cls._instance

    def __init__(self, connectionString):
        # Attempt to connect to the database with the connectionString parameter
        # if the attempt to connect fails, then the constructor will return without
        # further initialization
        try:
            self.engine = create_engine(connectionString)
        except:
            print("Failed to connect to the DB using: ",connectionString)
            return

        # Initialize connection dependent attributes
        self.Base = Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()
        self.cacheDB()
        
    def cacheDB(self):
        self.cacheInfo()
        self.cacheSector()
        self.cacheIndustry()
        self.cacheRelatedPeople()

    def cacheInfo(self):
        companiesQuery = self.session.query(Info)
        self.companyNames = set()
        self.companyTickers = set()
        for c in companiesQuery: 
           self.companyNames.add(c.Name) 
           self.companyTickers.add(c.Ticker)

    def cacheIndustry(self):
        industriesQuery = self.session.query(Industries)
        self.industries = set()
        for i in industriesQuery:
            self.industries.add(i.Name)

    def cacheSector(self):
        sectorsQuery = self.session.query(Sectors)
        self.sectors = set()
        for s in sectorsQuery:
            self.sectors.add(s.Name)

    def cacheRelatedPeople(self):
        relatedPeopleQuery = self.session.query(RelatedPeople)
        self.relatedpeople = set()
        for rp in relatedPeopleQuery:
            self.relatedpeople.add(rp.Name)

# Note: object construction requires existing references to:
#       * SQLAlchemy.Session
#       * DBWriteable
class DBUpdater(object):
    def _new_(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(DBUpdater, cls).__new__(cls, *args, **kwargs)
            return cls._instance
    
    # notes: session := SQLAlchemy.Session, w := DBWriteable
    def __init__(self,w):
        self.w = w
        self.tbu = TableUpdater(self.w)

    def UpdateCompany(self,c,updateInfo=True,updateSummary=True,updateAddress=True,updateFinancials=True):
        # prematurely end the method if the c parameter does not appear 
        # to reference a Company.Company object
        if not c or not c.Name or c.Name == "":
            return False 
        
        s = self.w.session
        
        company = s.query(Info).where(id==pk).one()
        # prematurely end the method if there is no record of the company in the database 
        if not company or ( company.Name == None or company.Name == ""):
            return False           
        if updateInfo:
            tbu.InfoUpdate(c,company.id)
        if updateSummary:
            tbu.SummaryUpdate(c,company.id)
        if updateAddress:
            tbu.AddressesUpdate(c.Address,company.id)

# this class contains updates methods for the following tables:    
# * Info
# * Summary
# * MetaData
# * Addresses
class TableUpdater(object):
    def _new_(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(TableUpdater, cls).__new__(cls, *args, **kwargs)
            return cls._instance
    
    def __init__(self,w):
        self.w = w
    
    # Method Ordering:
    # Info, Summary, KeyStats, MetaData
    def InfoUpdate(self,c,pk):
        # TODO:
        try:
            self.w.session.execute(update(Info).where(Info.id == pk).values(
                Name = c.Name, Ticker = c.Ticker
            ))
            return (True,("Summary",pk))
        except:    
            return (False,("Summary",pk))
    
    def InfoDelete(self):
        # TODO:
        return None

    def SummaryUpdate(self,c,pk):
        try:
            self.w.session.execute(update(Summary).where(Summary.info_id==pk).values(                               \
                    Close = c.Close, RangeLow = c.Range[0], RangeHigh = c.Range[1], _52WeekLow = c.YearRange[0],    \
                    _52WeekHigh = c.YearRange[1], Open = c.Open, VolDay = c.Volume[0], VolAvg = c.Volume[1],        \
                    PriceEarnings = c.PriceEarnings, Div = c.Dividends[0], DivYield = c.Dividends[1],               \
                    EPS = c.EarningsPerShare, Shares = c.Shares, Beta = c.Beta, QueryDate = datetime.datetime.now(),\
                    MarketCap = c.MarketCap, InstitutionalOwnership = c.Ownership                                   \
                    ))
            return (True,("Summary",pk))
        except:
            return (False,("Summary",pk))

    def SummaryDelete(self,pk):
        # TODO:
        return None

    # TODO: fully implement assignments
    # NOTE: from a business logic standpoint, it makes no sense to ever update field
    #       since updates will be new keystats with new periods, which should be new 
    #       table entries
    def KeyStatsUpdate(self,ksi,pk):
        try:
            self.w.session.execute(update(KeyStats).where(KeyStats.info_id==pk).values(
                Annual = ksi.Annual, NetProfitMargin = ksi.NetProfitMargin,EBITDMargin = ksi.EBITDMargin , \
                OperatingIncome = ksi.OperatingIncome, ReturnOnAverageAssets = ksi.ReturnOnAverageAssets, \
                ReturnOnAverageEquity = ksi.ReturnOnAverageEquity, Employees = ksi.Employees,
                CDPScore = ksi.CDPScore, Period = ksi.Period, QueryDate=datetime.datetime.now()
                ))
            return (True,("KeyStats",pk))
        except:
            return (False,("KeyStats",pk))

    def KeyStatsDelete(self):
        # TODO:
        return None
    
    def MetaDataUpdate(self,c,pk):
        try:
            self.w.session.execute(update(MetaData).where(MetaData.info_id==pk).values(
                  URL= c.URL, Currency = c.Currency 
                ))
            return (True,("MetaData",pk))
        except:
            return (False,("MetaData",pk))
    
    def MetaDataDelete(self):
        # TODO:
        return None
    
    # TODO: RelatedPeople related updating
    #       * Links
    #       * Roles
    #       * Info
    def RelatedPersonUpdate(self):
        return None
    
    def RelatedPersonDelete(self):
        return None

    def AddressesUpdate(self,a,pk):
        try:
            self.w.session.execute(update(Addresses).where(Addresses.info_id==pk).values(
                Street = a.Street, Zip = a.Zip, City = a.City, State = a.State, \
                Country = a.Country, Phone = a.Phone, Fax = a.Fax                        
                ))
            return (True,("Addresses",pk))
        except:
            return (False,("Addresses",pk))

class DBWriteable(object):
    """ To enforce singleton pattern--there should only be one DBWriteable object """
    def _new_(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(DBWriteable, cls).__new__(cls, *args, **kwargs)
            return cls._instance

    def __init__(self, session):
        self.session = session
        x = self.initCompanies() 
        # exchanges, industries, sectors
        self.exchanges  = self.initExchanges()
        self.industries = self.initIndustries()
        self.sectors    = self.initSectors()
        # companiesCache
        self.companies = x[0]
        self.tickers = x[1]
        # misc: related people, 
        self.relatedPeople = self.initRelatedPeople()
        # currencymap for MetaData object/multiplers
        self.currencyMap = self.initCurrencyMap()
        # 
        self.results = {}
    
    def initCurrencyMap(self):
        currencyMap = { Extract.Currency.USD:"United States Dollar", Extract.Currency.EUR:"Euro", Extract.Currency.GBX:"British Pound",    \
                        Extract.Currency.JPY:"Yen", Extract.Currency.CAD:"Canadian Dollar", Extract.Currency.AUS:"Australian Dollar",      \
                        Extract.Currency.CNY:"Chinese Yuan", Extract.Currency.SWS:"Swiss Franc", Extract.Currency.SIG: "Signapore Dollar", \
                        Extract.Currency.HKD: "Hong Kong Dollar"  
                      }
        return currencyMap
    
    def getMultipler(self,x):
        if "Millions" or "millions" in x:
            return 1000000
        elif "Billions" or "billions" in x:
            return 1000000000
        elif "Trillions" or "trillions" in x:
            return 1000000000000
        else:
            return 1
    
    def createMetaData(self,c):
        if c.URL and c.Currency and self.companies[c.Name]:
            md = MetaData(URL=c.URL,Currency=self.currencyMap[c.Currency], \
                          info_i=self.companies[c.Name])
            self.session.add(md)
            return True
        else:
            return False

    # returns whether company info was successfully written to the "cache"
    def assignCompany(self,c,commit=False):

        if not c or not c.Name or c.Name == "":
            return (None,False,None) 
        
        if c.Name not in self.companies and c.Ticker not in self.tickers:
            innerResult = {}
            self.companies[c.Name] =  len(self.companies) + 1
            self.tickers[c.Name]   =  len(self.tickers) + 1
            i = Info(Name=c.Name,Ticker=c.Ticker)
            # assign summary, keyStatRatios, Address, MetaData
            i.Summary = [self.createCompanySummary(c)]
            self.session.add(i)
            # TODO: Modularize these try/except's
            try:
                innerResult["Key Stats"] = self.createKeyStats(c) 
            except:
                innerResult["Key Stats"] = None 
            
            try:
                innerResult["Address"] = self.createAddress(c)
            except:
                innerResult["Address"] = None 
            
            try:
                innerResult["MetaData"] = self.createMetaData(c)
            except:
                innerResult["MetaData"] = None 
            # create links
            innerResult["Exchange"] = self.createExchangeLink(c)
            innerResult["Industry"] = self.createIndustryLink(c)
            innerResult["Sector"]   = self.createSectorLink(c)
        if commit:
            self.session.commit() 
            print("Writing ",c.Name,"(",c.Ticker,") to the DataBase!")
            return (c.Name,True,innerResult)
        else:
            return (c.Name,False,innerResult)

    def createAddress(self,c):
        # create ORM address item and assign columns
        if c.Address:
            a = Addresses()
            a.Street= c.Address.Street
            a.Zip = c.Address.Zip
            a.State= c.Address.State
            a.Country = c.Address.Country
            a.Phone= c.Address.Phone
            a.Fax = c.Address.Fax
            
            # TODO(?): add check for existence of the mapping (?)
            # map FK to the id mapped to this company
            a.info_id = self.companies[c.Name] 
            # add ORM address item to session for future commit
            self.session.add(a)
            return True
        else:
            return False

    def createKeyStats(self,c):
        i = 0
        if c.KeyStats and c.KeyStats[Extract.Period.quarter]:
            # asssign column values
            ksr = c.KeyStats[Extract.Period.quarter]
            ksi = KeyStats()
            ksi.Annual = False
            ksi.info_id = self.companies[c.Name] 
            ksi.CDPScore                = ksr.CDPScore
            ksi.NetProfitMargin         = ksr.NetProfitMargin
            ksi.EBITDMargin             = ksr.EBITDMargin
            ksi.ReturnOnAverageAssets   = ksr.ReturnOnAverageAssets
            ksi.ReturnOnAverageEquity   = ksr.ReturnOnAverageEquity
            ksi.Period                  = ksr.PeriodDate 
            ksi.QueryDate               = c.QueryDate
            ksi.Employees               = ksr.Employees
            # add item to session for future commit
            self.session.add(ksi)
            i += 1

        if c.KeyStats and c.KeyStats[Extract.Period.year]:
            # asssign column values
            ksr = c.KeyStats[Extract.Period.year]
            ksi = KeyStats()
            ksi.Annual = True 
            ksi.info_id = self.companies[c.Name] 
            ksi.CDPScore                = ksr.CDPScore
            ksi.NetProfitMargin         = ksr.NetProfitMargin
            ksi.EBITDMargin             = ksr.EBITDMargin
            ksi.ReturnOnAverageAssets   = ksr.ReturnOnAverageAssets
            ksi.ReturnOnAverageEquity   = ksr.ReturnOnAverageEquity
            ksi.Period                  = ksr.PeriodDate 
            ksi.QueryDate               = c.QueryDate
            ksi.Employees               = ksr.Employees
            # add item to session for future commit
            self.session.add(ksi)
            i += 1

        if i > 0:
            return True
        else:
            return False

    ## TODO: Comment and modularize
    def createCompanySummary(self,c):
        s = Summary()
        
        s.Beta                      = self.get(c.Beta)
        s.Close                     = self.get(c.Close)
        s.EPS                       = self.get(c.EarningsPerShare)
        s.Open                      = self.get(c.Open)
        s.PriceEarnings             = self.get(c.PriceEarnings)
        s.QueryDate                 = self.get(c.QueryDate)
        s.Shares                    = self.get(c.Shares)
        s.MarketCap                 = self.get(c.MarketCap)
        s.InstitutionalOwnership    = self.get(c.Ownership)
        
        if(len(c.Range)>1):
            s.RangeLow                  = self.get(c.Range[0])
            s.RangeHigh                 = self.get(c.Range[1])
        if(len(c.YearRange)>1):
            s._52WeekLow                = self.get(c.YearRange[0])
            s._52WeekHigh               = self.get(c.YearRange[1])
        if(len(c.Volume)>1):
            s.VolDay                    = self.get(c.Volume[0])
            s.VolAvg                    = self.get(c.Volume[1])
        if(len(c.Dividends)>1):
            s.Div                       = self.get(c.Dividends[1])
            s.DivYield                  = self.get(c.Dividends[0])
        if(len(c.Volume)>1):
            s.VolAvg                    = self.get(c.Volume[0])
            s.VolDay                    = self.get(c.Volume[1])
        
        return s

    def get(self,x):
        if not x or x == "-":
            return None
        else:
            return x

    def getUSDValue(x,y):
        if not x or not y:
            return None
        else:
            return x * y

    # NOTE: uses self.session 
    def createSectorLink(self,c):
        sl = SectorLink()
        if c.Sector and c.Sector not in self.sectors:
            s  = Sectors()
            s.Name = c.Sector
            self.sectors[s.Name] = len(self.sectors) + 1
            sl.info_id = self.companies[c.Name]
            sl.sectors_id = self.sectors[s.Name]
            self.session.add(sl)
            self.session.add(s)
            return True
        elif c.Sector and c.Sector != "":
            sl.info_id = self.companies[c.Name]
            sl.sectors_id = self.sectors[c.Sector]
            self.session.add(sl)
            return True 
        else:
            return False 


    def createIndustryLink(self,c):
        il = IndustryLink()
        if c.Industry and c.Industry not in self.industries:
            ind = Industries()
            ind.Name = c.Industry
            self.industries[ind.Name] = len(self.industries) + 1
            il.info_id = self.companies[c.Name]
            il.industries_id = self.industries[ind.Name]
            self.session.add(ind)
            self.session.add(il)
            return True
        elif c.Industry and c.Industry != "":
            il.info_id = self.companies[c.Name]
            il.industries_id = self.industries[c.Industry]
            self.session.add(il)
            return True 
        else:
            return False 

    def createExchangeLink(self,c):
        el = ExchangeLink()
        if c.Exchange and c.Exchange not in self.exchanges:
            e  = Exchanges()
            e.Name = c.Exchange
            self.exchanges[e.Name] = len(self.exchanges) + 1
            el.info_id = self.companies[c.Name]
            el.exchanges_id = self.exchanges[e.Name]
            self.session.add(el)
            self.session.add(e)
            return True
        elif c.Exchange and c.Sector != "":
            el.info_id = self.companies[c.Name]
            el.exchanges_id = self.exchanges[c.Exchange]
            self.session.add(el)
            return True 
        else:
            return False 

    def createRelatedPersonLinks(self,c):
        rp = c.RelatedPeople
        relatedPeopleAdded      = 0
        relatedPeopleRoleAdded  = 0
        for p in rp:
            rpd = RelatedPeople()
            if p.Name not in self.relatedPeople:
                rpd.Name = p.Name
                rpd.URL  = p.URL
                self.relatedPeople[p.Name] = rpd
                self.session.add(rpd)
                relatedPeopleAdded += 1
            else:
                rpd = self.relatedPeople[p.Name]
            
            if p.MultipleRoles:
                for r in p.Role:
                    rpr = RelatedPersonRole()
                    rpr.info_id = self.companies[c.Name]
                    rpr.relatedperson_id = rpd.id
                    rpr.Role = r
                    self.session.add(rpr)
                    relatedPeopleRoleAdded += 1
            else:                    
                rpr = RelatedPersonRole()
                rpr.info_id = self.companies[c.Name]
                rpr.relatedperson_id = rpd.id
                rpr.Role = p.Role
                self.session.add(rpr)
                relatedPeopleRoleAdded += 1

        if relatedPeopleAdded > 0 or relatedPeopleRoleAdded > 0:
            return True
        else:
            return False

    def initCompanies(self):
        d1 = {}
        d2 = {}
        q = self.session.query(Info).all()
        for s in q:
            d1[s.Name] = s.id
            d2[s.Ticker] = s.id
        return [d1, d2]

    def initExchanges(self):
        d = {}
        q = self.session.query(Exchanges).all()
        for s in q:
            d[s.Name] = s.id
        return d
                
    def initIndustries(self):
        d = {}
        q = self.session.query(Industries).all()
        for s in q:
            d[s.Name] = s.id
        return d

    def initSectors(self):
        d = {}
        q = self.session.query(Sectors).all()
        for s in q:
            d[s.Name] = s.id
        return d

    def initRelatedPeople(self):
        d = {}
        q = self.session.query(RelatedPeople).all()
        for s in q:
            d[s.Name] = s.id
        return d

    def getCurrencyMultipler(currency):
        if currency == Extract.Currency.USD:
            return 1.0
        else:
            # TODO: implement alternative currency cases
            print("TODO: ADD OTHER CASES")

    def assignIncomeStatements(self,c):
        for i in c.IncomeStatements:
            self.assignIncomeStatement(self,i,c)

    def assignIncomeStatement(self,i,c):
        iDB = IncomeStatements()

        if i.Period == Extract.Period.Year:
            iDB.Annual = True
        else:
            iDB.Annual = False

        m = self.getCurrencyMultipler(c.Currency)
        
        # assign CashFlows' ORM FK to the PK of Info
        # , i.e.: maps the item to the associated company
        iDB.info_id = self.companies[c.Name]

        # assign column data to the IncomeStatements ORM
        iDB.Period = i.Date
        iDB.QueryDate = c.QueryDate
        iDB.Revenue = self.self.getUSDValue(i.Revenue,m)
        iDB.OtherRevenueTotal= self.getUSDValue(i.OtherRevenueTotal ,m)
        iDB.TotalRevenue = self.getUSDValue(i.TotalRevenue, m)
        iDB.CostOfRevenueTotal = self.getUSDValue(i.CostOfRevenueTotal,m)
        iDB.GrossProfit = self.getUSDValue(i.GrossProfit,m)
        iDB.Selling_General_AdminExpenseTotal  = self.getUSDValue(i.Selling_General_AdminExpenseTotal,m)
        iDB.ResearchAndDevelopment = self.getUSDValue(i.ResearchAndDevelopment,m)
        iDB.Depreciation_Amortization = self.getUSDValue(i.Depreciation_Amortization,m)
        iDB.InterestIncome_Expense_NetNonOperating = self.getUSDValue(i.InterestIncome_Expense_NetNonOperating,m)
        iDB.UnusualExpense_Income_ = self.getUSDValue(i.UnusualExpense_Income_,m)
        iDB.OtherOperatingExpenses_Total = self.getUSDValue(i.OtherOperatingExpenses_Total,m)
        iDB.TotalOperatingExpense = self.getUSDValue(i.TotalOperatingExpense,m)
        iDB.OperatingIncome = self.getUSDValue(i.OperatingIncome,m)
        iDB.InterestIncome_Expense_NetNonOperating = self.getUSDValue(i.InterestIncome_Expense_NetNonOperating,m)
        iDB.Gain_Loss_onSaleOfAssets = self.getUSDValue(i.Gain_Loss_OnSaleOfAssets,m)
        iDB.Other_Net = self.getUSDValue(i.Other_Net, m)
        iDB.IncomeBeforeTax = self.getUSDValue(i.IncomeBeforeTax,m)
        iDB.IncomeAfterTax = self.getUSDValue(i.IncomeAfterTax,m)
        iDB.MinorityInterest = self.getUSDValue(i.MinorityInterest,m)
        iDB.EquityInAffiliates = self.getUSDValue(i.EquityInAffiliates,m)
        iDB.NetIncomeBeforeExtraItems = self.getUSDValue(i.NetIncomeBeforeExtraItems,m)
        iDB.AccountingChange = self.getUSDValue(i.AccountingChange,m)
        iDB.DiscontinuedOperations = self.getUSDValue(i.DiscontinuedOperations,m)
        iDB.ExtraordinaryItem = self.getUSDValue(i.ExtraordinaryItem,m)
        iDB.NetIncome = self.getUSDValue(i.NetIncome,m)
        iDB.PreferredDividends = self.getUSDValue(i.PreferredDividends, m)
        iDB.IncomeAvailableToCommonExclItems = self.getUSDValue(i.IncomeAvailableToCommonExclExtraItems, m)
        iDB.IncomeAvailableToCommonInclExtraItems = self.getUSDValue(i.IncomeAvailableToCommonExclExtraItems, m)
        iDB.BasicWeightedAverageShares = self.getUSDValue(i.BasicWeightedAverageShares, m)
        iDB.BasicEPSExcludingExtraordinaryItems = self.getUSDValue(i.BasicEPSExcludingExtraordinaryItems, m)
        iDB.BasicEPSIncludingExtraordinaryItems = self.getUSDValue(i.BasicEPSIncludingExtraordinaryItems, m)
        iDB.DilutionAdjustment = self.getUSDValue(i.DilutionAdjustment, m)
        iDB.DilutedWeightedAverageShares = self.getUSDValue(i.DilutedWeightedAverageShares,m)
        iDB.DilutedEPSExcludingExtraordinaryItems = self.getUSDValue(i.DilutedEPSExcludingExtraordinaryItems,m)
        iDB.DilutedEPSIncludingExtraordinaryItems = self.getUSDValue(i.DilutedEPSIncludingExtraordinaryItems,m)
        iDB.DividendsPerShareLessCommonStockPrimaryIssue  = self.getUSDValue(i.DividendsPerShareLessCommonStockPrimaryIssue,m)
        iDB.GrossDividendsLessCommonStock = self.getUSDValue(i.GrossDividendsLessCommonStock,m)
        iDB.NetIncomeAfterStockBasedCompExpense = self.getUSDValue(i.NetIncomeAfterStockBAsedCompExpense, m)
        iDB.BasicEPSAfterStockBasedCompExpense = self.getUSDValue(i.BasicEPSAfterStockBAsedCompExpense,m)
        iDB.DilutedEPSAfterStockBasedCompExpense = self.getUSDValue( i.DilutedEPSAfterSTockBasedCompExpense,m)
        iDB.Depreciation_Supplemental = self.getUSDValue(i.Depreciation_Supplemental,m)
        iDB.TotalSpecialItems = self.getUSDValue(i.TotalSpecialItems,m)
        iDB.NormalizedIncomeBeforeTaxes = self.getUSDValue(i.NormalizedIncomeBeforeTaxes,m)
        iDB.EffectOfSpecialItemsOnIncomeTaxes = self.getUSDValue(i.EffectOfSpecialItemsOnIncomeTaxes,m)
        iDB.IncomeTaxesExImpactOfSpecialItems = self.getUSDValue(i.IncomeTaxesExImpactOFSpecialItems,m)
        iDB.NormalizedIncomeAfterTaxes = self.getUSDValue(i.NormalizedIncomeAfterTaxes,m)
        iDB.NormalizedIncomeAvailToCommon = self.getUSDValue(i.NormalizedIncomeAvailToCommon,m)
        iDB.BasicNormalizedEPS = self.getUSDValue(i.NormalizedIncomeAfterTaxes,m)
        iDB.DilutedNormalizedEPS = self.getUSDValue(i.DilutedNormalizedEPS,m)

        # add the IncomeStatements ORM object to the session, for future commit
        self.session.add(iDB)

    def assignBalanceSheets(self,c):
        for bs in c.BalanceSheets:
            self.assignBalanceSheet(bs,c)
    
    def assignBalanceSheet(self,bs,c):
        bs = BalanceSheets()

        if b.Period == Extract.Period.year:
            b.Annual = True
        else:
            b.Annual= False

        m = self.getCurrencyMultipler(c.Currency)

        # assign BalanceSheets' ORM FK to the PK of Info
        # , i.e.: maps the item to the associated company
        bs.info_id = self.companies[c.Name] 

        # assign column data to the BalanceSheets ORM
        bs.Period = b.Date
        bs.QueryDate = c.QueryDate
        bs.CashAndEquivalents = self.getUSDValue(b.CashAndEquivalents,m)
        bs.ShortTermInvestments = self.getUSDValue(b.ShortTermInvestments,m)
        bs.CashAndShortTermInvestments = self.getUSDValue(b.CashAndShortTermInvestments,m)
        bs.AccountsReceivableLessTrade_Net = self.getUSDValue(b.AccountsReceivableLessTrade_Net, m)
        bs.Receivables_Other = self.getUSDValue(b.Receivables_Other, m)
        bs.TotalReceivables_Net = self.getUSDValue(b.TotalReceivables_Net, m)
        bs.TotalInventory = self.getUSDValue(b.TotalInventory, m)
        bs.PrepaidExpenses = self.getUSDValue(b.PrepaidExpenses, m)
        bs.OtherCurrentAssets_Total = self.getUSDValue(b.OtherCurrentAssets_Total, m)
        bs.TotalCurrentAssets = self.getUSDValue(b.TotalCurrentAssets, m)
        bs.Property_Plant_Equipment_Total = self.getUSDValue(b.Property_Plant_Equipment_Total, m)
        bs.AccumulatedDepreciation_Total = self.getUSDValue(b.AccumulatedDepreciation_Total, m)
        bs.Goodwill_Net = self.getUSDValue(b.Goodwill_Net, m)
        bs.Intangibles_Net = self.getUSDValue(b.Intangibles_Net, m)
        bs.LongTermInvestments = self.getUSDValue(b.LongTermInvestments, m)
        bs.OtherLongTermAssets_Total = self.getUSDValue(b.OtherLongTermAssets_Total, m)
        bs.TotalLiabilitiesAndShareholdersEquity = self.getUSDValue(b.TotalLiabilitiesAndShareholdersEquity, m)
        bs.AccountsPayable = self.getUSDValue( b.AccountsPayable, m)
        bs.AccruedExpenses = self.getUSDValue( b.AccruedExpenses, m)
        bs.NotesPayable_ShortTermDebt = self.getUSDValue( b.NotesPayable_ShortTermDebt, m)
        bs.CurrentPortOfLongTermDebt_CapitalLeases = self.getUSDValue(b.CurrentPortOfLongTermDebt_CapitalLeases, m)
        bs.OtherCurrentLiabilities_Total = self.getUSDValue(b.OtherCurrentLiabilities_Total, m)
        bs.TotalCurrentLiabilities = self.getUSDValue(b.TotalCurrentLiabilities, m)
        bs.LongTermDebt = self.getUSDValue(b.LongTermDebt, m)
        bs.CapitalLeaseObligations = self.getUSDValue(b.CapitalLeaseObligations, m)
        bs.LongTermDebt  = self.getUSDValue(b.LongTermDebt, m)
        bs.TotalDebt = self.getUSDValue( b.TotalDebt, m)
        bs.DeferredIncomeTax = self.getUSDValue( b.DeferredIncomeTax, m)
        bs.MinorityInterest = self.getUSDValue(b.MinorityInterest, m)
        bs.OtherCurrentLiabilities_Total = self.getUSDValue(b.OtherCurrentLiabilities_Total, m)
        bs.TotalLiabilities = self.getUSDValue(b.TotalLiabilities, m)
        bs.RedeemablePreferredStock_Total = self.getUSDValue(b.RedeemablePreferredStock_Total, m)
        bs.PreferredStockLessNonRedeemable_Net = self.getUSDValue(b.PreferredStockLessNonRedeemable_Net, m)
        bs.CommonStock_Total = self.getUSDValue( b.CommonStock_Total, m)
        bs.AdditionalPaidInCapital = self.getUSDValue( b.AdditionalPaidInCapital, m)
        bs.RetainedEarnings_AccumulationDeficit_ = self.getUSDValue( b.RetainedEarnings_AccumulationDeficit_, m)
        bs.TreasuryStockLessCommon = self.getUSDValue(b.TreasuryStockLessCommon, m)
        bs.OtherEquity_Total = self.getUSDValue(b.OtherEquity_Total, m)
        bs.TotalEquity = self.getUSDValue(b.TotalEquity, m)
        bs.TotalLiabilitiesAndShareholdersEquity = self.getUSDValue(b.TotalLiabilitiesAndShareholdersEquity, m)
        bs.SharesOutsLessCommonStockPrimaryIssue = self.getUSDValue(b.SharesOutsLessCommonStockPrimaryIssue, m)
        bs.TotalCommonSharesOutstanding = self.getUSDValue(b.TotalCommonSharesOutstanding, m)
        
        # add the BalanceSheets ORM item to the session, for future commit
        self.session.add(bs)

    def assignCashFlowStatements(self,c):
        for cf in c.assignCashFlowStatements:
            self.assignIncomeStatement(cf,c)

    def assignCashFlowStatement(self,cf,c):
        cfs = CashFlowStatements()

        if cf.Period == Extract.Period.year:
            cf.Annual = True
        else:
            cf.Annual = False

        m = self.getCurrencyMultipler(c.Currency)
        
        # assign CashFlows' ORM FK to the PK of Info
        # , i.e.: maps the item to the associated company
        cfs.info_id = self.companies[c.Name] 

        # assign column data to the CashFlows ORM
        cfs.Period = cf.Date
        cfs.QueryDate = c.QueryDate
        cfs.NetIncome = self.getUSDValue(cf.NetIncome,m)
        cfs.Depreciation_Depletion = self.getUSDValue(cf.Depreciation_Depletion,m)
        cfs.Amortization = self.getUSDValue(cf.Amortization,m)
        cfs.DeferredTaxes = self.getUSDValue(cf.DeferredTaxes,m)
        cfs.NonCashItems = self.getUSDValue(cf.NonCashItems,m)
        cfs.ChangesInWorkingcapital = self.getUSDValue(cf.ChangesInWorkingCapital,m)
        cfs.CashFromOperatingActivities = self.getUSDValue(cf.CashFromOperatingActivities,m)
        cfs.CapitalExpenditures = self.getUSDValue(cf.CapitalExpenditures,m)
        cfs.OtherInvestingCashFlowItems_Total = self.getUSDValue(cf.OtherInvestingFromCashFlowItems_Total,m)
        cfs.CashFromInvestingActivities = self.getUSDValue(cf.CashFromInvestingActivities,m)
        cfs.FinancingCashFlowItems = self.getUSDValue(cf.FinancingCashFlowItems,m)
        cfs.TotalCashDividendsPaid = self.getUSDValue(cf.TotalCashDividendsPaid, m)
        cfs.Issuance_Retirement_ofStock_Net = self.getUSDValue(cf.Issuance_Retirement_OfStock_Net, m)
        cfs.Issuance_Retirement_ofDebt_Net = self.getUSDValue(cf.Issuance_Retirement_OfDebt_Net,m)
        cfs.CashFromFinancingActivities = self.getUSDValue(cf.CashFromFinancingActivities,m)
        cfs.ForeignExchangeEffects = self.getUSDValue(cf.ForeignExchangeEffects,m)
        cfs.NetChangeInCash = self.getUSDValue(cf.NetChangeInCash, m)
        cfs.CashInterestPaid_Supplemental = self.getUSDValue(cf.CashInterestPaid_Supplemental,m)
        cfs.CashTaxesPaid_Supplemental = self.getUSDValue(cf.CashTaxesPaidSupplemental, m)
        
        # add the CashFlows ORM item to the session, for future commit
        self.session.add(cfs)
