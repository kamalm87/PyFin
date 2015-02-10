import PyFin.Company
from traceback import format_exc
from PyFin.ModelDB import *
from PyFin.Extract import *
from sqlalchemy import func

class WriteDB(object):
    """ To enforce singleton pattern--there should only be one DBWriteable object """
    def _new_(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(WriteDB, cls).__new__(cls, *args, **kwargs)
            return cls._instance

    def __init__(self,session):
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
        # 
        self.queries = self.initQueries()
        self.update = None
    
    def initCurrencyMap(self):
        currencyMap = { PyFin.Extract.Currency.USD:"United States Dollar", PyFin.Extract.Currency.EUR:"Euro", PyFin.Extract.Currency.GBX:"British Pound",    \
                        PyFin.Extract.Currency.JPY:"Yen", PyFin.Extract.Currency.CAD:"Canadian Dollar", PyFin.Extract.Currency.AUS:"Australian Dollar",      \
                        PyFin.Extract.Currency.CNY:"Chinese Yuan", PyFin.Extract.Currency.SWS:"Swiss Franc", PyFin.Extract.Currency.SIG: "Signapore Dollar", \
                        PyFin.Extract.Currency.HKD: "Hong Kong Dollar"  
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
        if c.URL and c.Currency and c.Name in self.companies:
            md = MetaData(URL=c.URL,Currency=self.currencyMap[c.Currency], \
                          info_id=self.companies[c.Name])
            self.session.add(md)
            return True
        else:
            return False

    def recordCompanyException(self,c,t,m,commit=False):
        if c.Name in self.companies:
            ec = ExceptionsCompany(info_id=self.companies[c.Name],Message=m,Type=t)
            self.session.add(ec)
            if commit:
                self.session.commit()
            return True                
        elif c.Ticker in self.tickers:
            ec = ExceptionsCompany(info_id=self.tickers[c.Ticker],Message=m,Type=t)
            self.session.add(ec)
            if commit:
                self.session.commit()
            return True
        else:
            return False

    def recordExceptionsQuery(self,q_id,t,m,commit=False):
        eq = ExceptionsQuery(query_id=q_id,Message=m,Type=t)
        self.session.add(eq)
        if commit:
            self.session.commit()


    # returns whether company info was successfully written to the "cache"
    def assignCompany(self,c,commit=False):
        print("assignCompany( ",c.Name," )")
        if not c or not c.Name or c.Name == "":
            return (None,False,None) 
        
        innerResult = {}
        
        i = self.session.query(Info).filter(Info.Ticker==c.Ticker).all()
        j = None
        for x in range(0,len(i)):
            if i[x].Name == c.Name:
                j = i
                break

        exists = False
        if not j and c.Ticker not in self.tickers:
            j = Info(Name=c.Name,Ticker=c.Ticker)
            self.session.add(j)
            self.session.commit()
            self.tickers[c.Ticker]   = j.id 
            self.companies[c.Name] = j.id
            if c.Ticker not in self.tickers:
                self.tickers[c.Ticker] = j.id
            if c.Name not in self.companies:                 
                self.companies[c.Name] = j.id
        else:
            # TODO: Better way to select which info is most likely to be
            #       the relevant info
            j = i[0]
            exists = True
            # TODO: Fix DB's data, then remove, hopefully
            # provisional for some data sanitzation
            if c.Ticker not in self.tickers:
                self.tickers[c.Ticker] = j.id
            if c.Name not in self.companies:                 
                self.companies[c.Name] = j.id

        j.Summary = [self.createCompanySummary(c,exists)]
        
        # assign summary, keyStatRatios, Address, MetaData
        innerResult["Key Stats"] = self.createKeyStats(c) 
        innerResult["Address"] = self.createAddress(c)
        innerResult["MetaData"] = self.createMetaData(c)
        # create links
        innerResult["Exchange"] = self.createExchangeLink(c)
        innerResult["Industry"] = self.createIndustryLink(c)
        innerResult["Sector"]   = self.createSectorLink(c)
        self.session.commit()
        self.createSectorIndustryLink(c)
        # TODO: Related People is BROKEN, need to fix!!!!
        # innerResult["Related People"] = self.createRelatedPersonLinks(c)
        innerResult["BalanceSheets"] = self.assignBalanceSheets(c)
        innerResult["CashFlowStatements"] = self.assignCashFlowStatements(c)
        innerResult["IncomeStatements"] = self.assignIncomeStatements(c)
        innerResult["Description"] = self.assignDescription(c)
        if commit:
            self.session.commit() 
            return (c.Name,True,innerResult)
        else:
            return (c.Name,False,innerResult)
    
    def assignDescription(self,c):
        if c.CompanySummary:
            fk = self.tickers[c.Ticker]
            q = self.session.query(Description).filter(Description.info_id==fk).all()
            #r = Description(info_id=self.tickers[c.Ticker], Description=x)
            if len(q) == 0:
                self.session.add(Description(info_id=fk,Description=c.CompanySummary))
            elif len(q) >= 1:
                q[0].Description = c.CompanySummary
                self.session.add(q[0])
                if len(q) > 1:
                    res = self.update.RemoveDuplicates("Description",fk)
            return True
        else:
            return False

    def createAddress(self,c):
        # create ORM address item and assign columns
        if c.Address:
            a = self.session.query(Addresses).filter(Addresses.info_id==self.tickers[c.Ticker]).first()
            if not a:
                a = Addresses()
            a.Street= c.Address.Street
            a.Zip = c.Address.Zip
            a.City = c.Address.City
            a.State= c.Address.State
            a.Country = c.Address.Country
            a.Phone= c.Address.Phone
            a.Fax = c.Address.Fax
            
             # TODO(?): add check for existence of the mapping (?)
            # map FK to the id mapped to this company
            if c.Ticker in self.tickers:
                a.info_id = self.tickers[c.Ticker]
            # add ORM address item to session for future commit
            self.session.add(a)
            return True
        else:
            return False

    def createKeyStats(self,c):
        i = 0
        if not c.KeyStats:
            return False
        else:
            ksis = self.session.query(KeyStats).filter(KeyStats.info_id==self.tickers[c.Ticker]).all()   

        if c.KeyStats and c.KeyStats[Period.Quarter]:
            # asssign column values
            ksr = c.KeyStats[Period.Quarter]
            ksi = None
            # if an existing KeyStatsItem object exists with the same Date exists,
            # then update it, otherwise create a new object to insert into the database
            for k in ksis:
                if k.Period == ksr.PeriodDate:
                    ksi = k
            if not ksi:
                ksi = KeyStats()
            
            ksi.Annual = False
            if c.Ticker in self.tickers:
                ksi.info_id = self.tickers[c.Ticker]
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

        if c.KeyStats and Period.Year in c.KeyStats and c.KeyStats[Period.Year]:
            # asssign column values
            ksr = c.KeyStats[Period.Year]
            ksi = None
            # if an existing KeyStatsItem object exists with the same Date exists,
            # then update it, otherwise create a new object to insert into the database
            for k in ksis:
                if k.Period == ksr.PeriodDate:
                    ksi = k
            if not ksi:
                ksi = KeyStats()
            
            ksi.Annual = False
            if c.Ticker in self.tickers:
                ksi.info_id = self.tickers[c.Ticker]
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
    def createCompanySummary(self,c,exists):
        print(c.Name, " -> ", c.Ticker, " -> ", self.tickers[c.Ticker])
        s = self.session.query(Summary).filter(Summary.info_id==self.tickers[c.Ticker]).first()
        if s:
            print("Query result:", s)
        else:
            print("NO RESULT, WUT")
        if not s:
            s = Summary()
        s.Close                     = self.get(c.Close)
        s.EPS                       = self.get(c.EarningsPerShare)
        s.Open                      = self.get(c.Open)
        s.PriceEarnings             = self.get(c.PriceEarnings)
        s.QueryDate                 = self.get(c.QueryDate)
        s.Shares                    = self.get(c.Shares)
        s.MarketCap                 = self.get(c.MarketCap)
        s.InstitutionalOwnership    = self.get(c.Ownership)
        s.Beta                      = self.get(c.Beta) 
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
        self.session.add(s)            
        return s
    
    def digitCount(self,x):
        if x:
            digs = 0
            for i in x:
                if i.isdigit():
                    digs += 1
            return digs
        else:
            return 0


    def get(self,x,numeric=False):
        if numeric:
            if self.digitCount(x) == 0:
                return None
        if not x or x == "-":
            return None
        else:
            return x

    def getUSDValue(self,x,y):
        if not x or not y:
            return None
        else:
            return x * y

    # TODO: Add more logic if a one company to potentially many sector links assignment is desired
    def createSectorLink(self,c):
        # If the sector link already exists, then do nothing, otherwise create an industry link
        sl = self.session.query(SectorLink).filter(SectorLink.info_id==self.tickers[c.Ticker]).first()
        if sl:
            return False
        else:            
            sl = SectorLink()
    
        if c.Sector and c.Sector not in self.sectors:
            s  = Sectors()
            s.Name = c.Sector
            self.sectors[s.Name] = len(self.sectors) + 1
            sl.info_id = self.tickers[c.Ticker]
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


    # TODO: Add more logic if a one company to potentially many industry links assignment is desired
    def createIndustryLink(self,c):
        # If the industry link already exists, then do nothing, otherwise create an industry link
        il = self.session.query(IndustryLink).filter(IndustryLink.info_id==self.tickers[c.Ticker]).first()
        if il:
            return False
        else:
            il = IndustryLink()

        if c.Industry and c.Industry not in self.industries:
            ind = Industries()
            # it's chosen to add and commit an industry to get an automatically generated
            # sequential id  for instead of creating a set of methods to find the lowest 
            # free ID to handle cases that may be encountered when deleting industries 
            ind.Name = c.Industry
            self.session.add(ind)
            self.session.commit()
            il.industries_id = ind.id
            if c.Ticker in self.companies:
                il.info_id = self.tickers[c.Ticker]
            
            self.session.add(il)
            self.session.commit()
            
            if c.Industry not in self.industries:
                self.industries = self.initIndustries()
            return True
        elif c.Industry and c.Industry != "":
            il.info_id = self.companies[c.Name]
            il.industries_id = self.industries[c.Industry]
            self.session.add(il)
            return True 
        else:
            return False 

    # TODO: Add more logic if a one company to potentially many secotr links assignment is desired
    def createSectorIndustryLink(self,c):
        if (c.Industry and c.Sector) and (c.Industry != "ne" and c.Sector != "ne"):
            industry_id = self.industries[c.Industry]
            sector_id   = self.sectors[c.Sector]
            
            q = self.session.query(SectorIndustryLink)      \
                    .filter(SectorIndustryLink.industries_id == industry_id).all()
            # if there exist SectorIndustLinks with the company's sector id, check them all
            # NOTE: since q queries industries_id, it is expected that there is only one result
            #       the loop is just in case the database becomes corrupted somehow
            if q:
                for s in q:
                    if s.sectors_id == sector_id:
                        return (False,q,"Exists")
            # if a matching SectorindustryLink relative to the company's sector and link 
            # was not found, one is created
            sli = SectorIndustryLink()
            sli.sectors_id = sector_id
            sli.industries_id = industry_id
            self.session.add(sli)
            self.session.commit()
            return (True, sli, "Created")  
        else: # Nothing to do, return false
            return (False,None,"No data")

    # TODO: Add more logic if a one company to potentially many exchange links assignment is desired
    # NOTE: From a business logic sense, this TODO should never be applicable 
    def createExchangeLink(self,c):
        el = self.session.query(ExchangeLink).filter(ExchangeLink.info_id==self.tickers[c.Ticker]).first()
        if el:
            return False
        else:
            el = ExchangeLink()

        if c.Exchange and c.Exchange not in self.exchanges:
            self.exchanges[c.Exchange] = len(self.exchanges) + 1
            e = Exchanges(Name=c.Exchange)
            self.session.add(e)
            self.session.commit()
            el.info_id = self.companies[c.Name]
            el.exchange_id = self.exchanges[c.Exchange]
            self.session.add(el)
            self.session.commit()
            return True
        elif c.Exchange and c.Exchange in self.exchanges:
            el.info_id = self.companies[c.Name]
            el.exchange_id = self.exchanges[c.Exchange]
            self.session.add(el)
            self.session.commit()
            return True
        else:
            return False 
    # TODO:
    # THIS IS BROKEN, FIX EVENTUALLY 
    def createRelatedPersonLinks(self,c):
        try:
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
        except Exception:
           # print("exception: ", c.Name,"(",c.Ticker,")")
            return False
    
    def initQueries(self):
        d = {}
        q = self.session.query(Query).all()
        for s in q:
            if s.info_id:
                d[s.Term] = True
            else:
                d[s.Term] = False
        return d                

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

    def getCurrencyMultipler(self,currency):
        if currency == Currency.USD:
            return 1.0
        else:
            # TODO: implement alternative currency cases
            print("TODO: ADD OTHER CASES: getCurrencyMultipler(",currency,")")

    def assignIncomeStatements(self,c):
        print("assignIncomeStatements: ",len(c.IncomeStatements))
        existing = self.session.query(IncomeStatements).filter(IncomeStatements.info_id==self.tickers[c.Ticker]).all()
        periods = set()
        for i in existing:
            if i.Period not in periods:
                periods.add(i.Period)
        for i in c.IncomeStatements:
            if i.Date not in periods:
                self.assignIncomeStatement(i,c)
        self.session.commit()                    


    def assignIncomeStatement(self,i,c):
        iDB = IncomeStatements()
        if i.Period == Period.Year:
            iDB.Annual = True
        else:
            iDB.Annual = False

        m = self.getCurrencyMultipler(c.Currency)
        
        # assign CashFlows' ORM FK to the PK of Info
        # , i.e.: maps the item to the associated company
        iDB.info_id = self.tickers[c.Ticker]

        # assign column data to the IncomeStatements ORM
        iDB.Period = i.Date
        iDB.QueryDate = c.QueryDate
        iDB.Revenue = self.getUSDValue(i.Revenue,m)
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
        existing = self.session.query(BalanceSheets).filter(BalanceSheets.info_id==self.tickers[c.Ticker]).all()
        periods = set() 
        for i in existing:
            if i.Period not in periods:
                x = str(i.Period)
                y = x.index(' ')
                z = x[0:y]
                periods.add(str(z))
        wut = set()
        for bs in c.BalanceSheets:
            wut.add(bs.Date)
        for bs in c.BalanceSheets:
            x = str(bs.Date)
            if x not in periods:
                self.assignBalanceSheet(bs,c)
        
        self.session.commit()
    
    def assignBalanceSheet(self,b,c):
        bs = BalanceSheets()

        if b.Period == Period.Year:
            bs.Annual = True
        else:
            bs.Annual= False

        m = self.getCurrencyMultipler(c.Currency)

        # assign BalanceSheets' ORM FK to the PK of Info
        # , i.e.: maps the item to the associated company
        bs.info_id = self.tickers[c.Ticker] 

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
        existing = self.session.query(CashFlowStatements).filter(CashFlowStatements.info_id==self.tickers[c.Ticker]).all()
        periods = set() 
        for i in existing:
            if i.Period not in periods:
                periods.add(i.Period)
        for cfs in c.CashFlowStatements:
            if cfs.Date not in periods:
                self.assignCashFlowStatement(cfs,c)
        
        self.session.commit()

    def assignCashFlowStatement(self,cf,c):
        cfs = CashFlowStatements()

        if cf.Period == Period.Year:
            cfs.Annual = True
        else:
            cfs.Annual = False

        m = self.getCurrencyMultipler(c.Currency)
        
        # assign CashFlows' ORM FK to the PK of Info
        # , i.e.: maps the item to the associated company
        cfs.info_id = self.tickers[c.Ticker] 

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
        cfs.OtherInvestingCashFlowItems_Total = self.getUSDValue(cf.OtherInvestingCashFlowItems_Total,m)
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
