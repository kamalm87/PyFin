
class QueryDB(object):
    """" For singleton pattern """
    _instance = None
    def _new_(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(QueryDB, cls).__new__(cls, *args, **kwargs)
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
