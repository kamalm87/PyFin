import PyFin.DataBase.WriteDB
import PyFin.ModelDB

# Note: object construction requires existing references to:
#       * SQLAlchemy.Session
#       * DBWriteable
class UpdateDB(object):
    def _new_(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(UpdateDB, cls).__new__(cls, *args, **kwargs)
            return cls._instance
    
    # notes: session := SQLAlchemy.Session, w := DBWriteable
    def __init__(self,w):
        self.w = w
        self.tbu = TableUpdate(self.w)
        self.dupes = DuplicateChecker(self.w)

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
    
    def RemoveDuplicates(self,table,fk, t = "def" ):
        if table in self.dupes.fsm:
            if t == "def": 
                return self.dupes.RemoveMappingDupeFS(self.dupes.fsm[table],fk)
            else:
                return self.dupes.RemoveMappingDupeFS(self.dupes.fsm[table],fk,t)
        if table in self.dupes.tm:
            return self.dupes.RemoveMappingDupe(self.dupes.tm[table],fk)
        if table == "Description":
            return self.dupes.RemoveDuplicateDescriptions(fk)
        if table == "MetaData":
            print("RemoveDuplicates")
            return self.dupes.RemoveMappingDupe("MetaData",fk)


class DuplicateChecker(object):
    
    def _new_(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(DuplicateChecker,cls).__new__(cls,*args,**kwargs)
            return cls._instance

    def __init__(self,w):
        self.w = w
        self.tm = { "MetaData" : PyFin.ModelDB.MetaData, "Description" : PyFin.ModelDB.Description, "Addresses" : PyFin.ModelDB.Addresses,        \
                "SectorLink" : PyFin.ModelDB.SectorLink, "IndustryLink" : PyFin.ModelDB.IndustryLink, "ExchangeLink" : PyFin.ModelDB.ExchangeLink \
                  }
        self.fsm = { "BalanceSheets" : PyFin.ModelDB.BalanceSheets, "CashFlowStatements" : PyFin.ModelDB.CashFlowStatements, \
                     "IncomeStatements" : PyFin.ModelDB.IncomeStatements 
                   }
    # For duplicate finanical statements
    # Duplicates here for a given info_id are expected to be
    # distinct based on periods
    def RemoveMappingDupeFS(self,table,fk, t = None):
        s = self.w.session
        if t == None: 
            q1 = s.query(table).filter(table.info_id==fk).all()
        else:
            tq = s.query(table).filter(table.info_id==fk).all()
            q1 = []
            for x in tq:
                if x.Annual == t:
                    q1.append(x)
        q2 = {} 
        for q in q1:
            if q.Period not in q2:
                q2[q.Period] = []
                q2[q.Period].append(q)
            else:
                q2[q.Period].append(q)
        delete = False
        res = []
        for q in q2:
            y = len(q2[q])
            if y > 1:
                if not delete:
                    delete = True
                for i in range(1,y):
                    s.delete(q2[q][i])                        
                res.append((q,y-1))
        return (delete,res)                

    def RemoveMappingDupe(self,table,fk):
        s = self.w.session
        q = s.query(table).filter(table.info_id==fk).all()
        y = len(q)
        if y == 0 or y == 1:
            return (False,0)
        else:
            for i in range(1,y):
                s.delete(q[i])
            return (True,y-1)            

    def RemoveDuplicateMetaData(self,fk):
        s = self.w.session
        q = s.query(MetaData).filter(MetaData.info_id==fk).all()
        y = len(q)
        if y == 0 or y == 1:
            return (False,0)
        else:
            for i in range(1,y):
                s.delete(q[i])
            return (True,y-1)    

    def RemoveDuplicateDescriptions(self,fk):
        s = self.w.session
        q = s.query(Description).filter(Description.info_id==fk).all()
        y = len(q)
        if y == 0 or y == 1:
            return (False,0)
        else:
            for i in range(1,y):
                s.delete(q[i])
            return (True,y-1)                    

# this class contains updates methods for the following tables:    
# * Info
# * Summary
# * MetaData
# * Addresses
class TableUpdate(object):
    def _new_(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(TableUpdate, cls).__new__(cls, *args, **kwargs)
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

