import datetime
from sqlalchemy import create_engine, ForeignKey, Float, Boolean, DateTime, BigInteger
from sqlalchemy import Column, Integer, Sequence, String, Table, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, backref




Base = declarative_base()

class Query(Base):
    __tablename__ = 'Query'
    id      = Column(Integer, primary_key=True)
    Term    = Column(String,nullable=False,unique=True)
    info_id = Column(Integer,ForeignKey("Info.id"))
    info    = relationship("Info",backref=backref("Query"))
    
    def __repr__(self):
        return "<Query( id='%s', 'Term='%s', info_id='%s'" % (self.id, self.Term, self.info_id)
    
    def __str__(self):
        return "<Query( id='%s', 'Term='%s', info_id='%s'" % (self.id, self.Term, self.info_id)

class Info(Base):
    __tablename__ = 'Info'

    id = Column(Integer, primary_key=True)
    Name    = Column(String, nullable=False)
    Ticker  = Column(String)
    def __repr__(self):
        return "<Info( id = '%s', Name='%s', Ticker='%s')>" % ( self.id, self.Name, self.Ticker)


class ExceptionsCompany(Base):
    # table name
    __tablename__ = "ExceptionsCompany"
    # PK
    id = Column(Integer, primary_key=True)
    # FK
    info_id = Column(Integer,ForeignKey("Info.id"))
    info    = relationship("Info", backref=backref("ExceptionsCompany"))
    # Data
    Type    = Column(String)
    Message = Column(String)

class ExceptionsQuery(Base):
    # table name
    __tablename__ = "ExceptionsQuery"
    # PK
    id = Column(Integer, primary_key=True)
    # FK
    query_id = Column(Integer,ForeignKey("Query.id"))
    info    = relationship("Query", backref=backref("ExceptionsQuery"))
    # Data
    Type    = Column(String)
    Message = Column(String)

class Description(Base):
    __tablename__ = "Description"
    # PK
    id = Column(Integer, primary_key=True)
    # FK
    info_id = Column(Integer,ForeignKey("Info.id"))
    info    = relationship("Info", backref=backref("Description"))
    # Data
    Description = Column(String)


class MetaData(Base):
    __tablename__ = "MetaData"
    # PK
    id = Column(Integer, primary_key=True)
    # FK
    info_id = Column(Integer,ForeignKey("Info.id"))
    info    = relationship("Info", backref=backref("MetaData"))
    # data
    URL         = Column(String)
    Currency    = Column(String)
    def __repr__(self):
        return "<MetaData( id='%s', info_id='%s', URL='%s', Currency='%s'" % \
                ( self.id, self.info_id, self.URL, self.Currency ) 
    """        
    def __str__(self):
        return "<MetaData( id='%s', info_id='%s', URL='%s', Currency='%s'" % \
                ( self.id, self.info_id, self.URL, self.Currency ) 
    """


class Return(Base):
    __tablename__ = "Return"
    # PK
    id = Column(Integer,primary_key=True)
    # FK 
    info_id = Column(Integer, ForeignKey("Info.id"))         
    info = relationship("Info", backref=backref("Return", order_by=id))
    # Data
    ReturnDate = Column(DateTime)
    Close = Column(Float)
    AdjClose = Column(Float)
    Volumne = Column(BigInteger)

# Schema: Company
class Summary(Base):
    __tablename__ = 'Summary'

    id = Column(Integer, primary_key=True)
    RangeLow                = Column(Float)
    RangeHigh               = Column(Float)
    _52WeekLow              = Column(Float)
    _52WeekHigh             = Column(Float)
    Open                    = Column(Float)
    Close                   = Column(Float)
    VolDay                  = Column(Float)
    VolAvg                  = Column(Float)
    PriceEarnings           = Column(Float)
    Div                     = Column(Float)
    DivYield                = Column(Float)
    EPS                     = Column(Float)
    Shares                  = Column(BigInteger)
    Beta                    = Column(Float)
    QueryDate               = Column(DateTime)
    MarketCap               = Column(Float)
    InstitutionalOwnership  = Column(Float)
    # FK
    info_id = Column(Integer, ForeignKey("Info.id"))         
    info = relationship("Info", backref=backref("Summary", order_by=id))

    def __str__(self):
        return "<Summary ( PE='%s', EPS='%s', Beta='%s'  )>" % ( self.PriceEarnings, self.EPS, self.Beta )
#    def __str__(self):
#        return "<Summary(RangeLow='%s', RangeHigh='%s', _52WeekLow='%s', _52WeekHigh='%s', Open='%s', Close='%s', VolDay='%', VolAvg='%s', PriceEarnings='%s', Div='%s', DivYield='%s', EPS='%s', Shares='%s', Beta='%s')>" % \
 #                ( self.RangeLow, self.RangeHigh, self._52WeekLow, self._52WeekHigh, self.Open, self.Close, self.VolDay, self.VolAvg, self.PriceEarnings, self.Div, self.DivYield, self.EPS, self.Shares, self.Beta  )

    def __repr__(self):
        return "<Summary(RangeLow='%s', RangeHigh='%s', _52WeekLow='%s', _52WeekHigh='%s', Open='%s', Close='%s', VolDay='%', VolAvg='%s', PriceEarnings='%s', Div='%s', DivYield='%s', EPS='%s', Shares='%s', Beta='%s')>" % \
                 ( self.RangeLow, self.RangeHigh, self._52WeekLow, self._52WeekHigh, self.Open, self.Close, self.VolDay, self.VolAvg, self.PriceEarnings, self.Div, self.DivYield, self.EPS, self.Shares, self.Beta  )

# Schema: Company
class KeyStats(Base):
    __tablename__ = "KeyStats"

    # PK
    id = Column(Integer, primary_key=True)
    # nullables
    Annual                  = Column(Boolean)
    NetProfitMargin         = Column(Float)
    EBITDMargin             = Column(Float)
    OperatingMargin         = Column(Float)
    ReturnOnAverageAssets   = Column(Float)
    ReturnOnAverageEquity   = Column(Float)
    Employees               = Column(Integer)
    CDPScore                = Column(String)
    Period                  = Column(DateTime)
    QueryDate               = Column(DateTime)
    # FK
    info_id = Column(Integer, ForeignKey("Info.id"))
    info = relationship("Info", backref=backref("KeyStats", order_by=id))

    def __repr__(self):
        return "<KeyStats(Annual='%s', NetProfitMargin='%s', OperatingMargin='%s', ReturnOnAverageAssets='%s', ReturnOnAverageEquity='%s', Employees='%s',  CDPScore='%s')>" \
                % (self.Annual, self.NetProfitMargin, self.OperatingMargin, self.ReturnOnAverageAssets, self.ReturnOnAverageEquity, self.Employees, self.CDPScore )


class Industries(Base):
    __tablename__ = "Industries"
    id = Column(Integer, primary_key=True)
    Name = Column(String)

# Schema:
class IndustryLink(Base):
    __tablename__ =  "IndustryLink"
    #PK
    id = Column(Integer, primary_key=True)
    
    info_id = Column(Integer, ForeignKey("Info.id"))
    info = relationship("Info", backref=backref("IndustryLink", order_by=id))
    
    industries_id = Column(Integer, ForeignKey("Industries.id"))
    industry = relationship("Industries", backref=backref("IndustryLink", order_by=id))


class Sectors(Base):
    __tablename__ = "Sectors"
    id = Column(Integer, primary_key=True)
    Name = Column(String)

# Schema:
class SectorLink(Base):
    __tablename__ =  "SectorLink"
    #PK
    id = Column(Integer, primary_key=True)
    
    info_id = Column(Integer, ForeignKey("Info.id"))
    info = relationship("Info", backref=backref("SectorLink", order_by=id))
    
    sectors_id = Column(Integer, ForeignKey("Sectors.id"))
    sector = relationship("Sectors", backref=backref("SectorLink", order_by=id))

class SectorIndustryLink(Base):
    __tablename__ = "SectorIndustryLink"
    # PK
    id = Column(Integer, primary_key=True)

    sectors_id = Column(Integer, ForeignKey("Sectors.id"))
    sector = relationship("Sectors", backref=backref("SectorIndustryLink", order_by=id))

    industries_id = Column(Integer, ForeignKey("Industries.id"))
    industry = relationship("Industries", backref=backref("SectorIndustryLink", order_by=id))

class Exchanges(Base):
    __tablename__ = "Exchanges"
    id = Column(Integer, primary_key=True)
    Name = Column(String)

class ExchangeLink(Base):    
    __tablename__ =  "ExchangeLink"
    #PK
    id = Column(Integer, primary_key=True)
    
    info_id = Column(Integer, ForeignKey("Info.id"))
    info = relationship("Info", backref=backref("ExchangeLink", order_by=id))
    
    exchange_id = Column(Integer, ForeignKey("Exchanges.id"))
    exchange    = relationship("Exchanges", backref=backref("ExchangeLink", order_by=id))

class RelatedPersonRole(Base):
    __tablename__ = "RelatedPersonRole"
    # PK
    id = Column(Integer,primary_key=True)

    # data
    Role = Column(String, nullable=True)
    
    # FK
    relatedperson_id = Column(Integer,ForeignKey("RelatedPeople.id"))
    relatedperson    = relationship("RelatedPeople", backref=backref("RelatedPersonRole"))

    info_id = Column(Integer,ForeignKey("Info.id"))
    info    = relationship("Info", backref=backref("RelatedPersonRole")) 

class RelatedPeople(Base):
    __tablename__ = "RelatedPeople"
    # PK
    id = Column(Integer,primary_key=True)
    # data
    URL  = Column(String, nullable=True)
    Name = Column(String, nullable=True)

class RelatedPersonLink(Base):
    __tablename__ = "RelatedPersonLink"
    
    # PK
    id = Column(Integer,primary_key=True)
    
    # FK
    info_id = Column(Integer, ForeignKey("Info.id"))
    info    = relationship("Info",backref=backref("RelatedPersonLink",order_by=id))
   
    person_id = Column(Integer, ForeignKey("RelatedPeople.id"))
    person    = relationship("RelatedPeople", backref=backref("RelatedPersonLink",order_by=id))  



class IncomeStatements(Base):
    __tablename__ = "IncomeStatements"
    # PK
    id = Column(Integer,primary_key=True)
    # FK
    info    = relationship("Info", backref=backref("IncomeStatements"))
    info_id = Column(Integer,ForeignKey("Info.id"))
    # data - headers
    Annual      = Column(Boolean)
    Period      = Column(DateTime,nullable=False)
    QueryDate   = Column(DateTime,nullable=False)
    # data
    # 1 - Revenue
    Revenue                                     = Column(Float)
    # 2
    OtherRevenueTotal                           = Column(Float)
    # 3
    TotalRevenue                                = Column(Float)
    # 4
    CostOfRevenueTotal                          = Column(Float)
    # 5 
    GrossProfit                                 = Column(Float)
    # 6
    Selling_General_AdminExpenseTotal           = Column(Float)
    # 7
    ResearchAndDevelopment                      = Column(Float)
    # 8
    Depreciation_Amortization                   = Column(Float)
    # 9
    InterestExpense_Income_LessNetOperating     = Column(Float)
    # 10
    UnusualExpense_Income_                      = Column(Float)
    # 11
    OtherOperatingExpenses_Total                = Column(Float)
    # 12
    TotalOperatingExpenses_Total                = Column(Float)
    # 13
    OperatingIncome                             = Column(Float)
    # 14
    InterestIncome_Expense_NetNonOperating      = Column(Float)
    # 15
    Gain_Loss_onSaleOfAssets                    = Column(Float)
    # 16
    Other_Net                                   = Column(Float)
    # 17
    IncomeBeforeTax                             = Column(Float)
    # 18
    IncomeAfterTax                              = Column(Float)
    # 19
    MinorityInterest                            = Column(Float)
    # 20
    EquityInAffiliates                          = Column(Float)
    # 21
    NetIncomeBeforeExtraItems                   = Column(Float)
    # 22
    AccountingChange                            = Column(Float)
    # 23
    DiscontinuedOperations                      = Column(Float)
    # 24
    ExtraordinaryItem                           = Column(Float)
    # 25
    NetIncome                                   = Column(Float)
    # 26
    PreferredDividends                          = Column(Float)
    # 27
    IncomeAvailableToCommonExclItems            = Column(Float)
    # 28
    IncomeAvailableToCommonInclExtraItems       = Column(Float)
    # 29
    BasicWeightedAverageShares                   = Column(Float)
    # 30
    BasicEPSExcludingExtraordinaryItems          = Column(Float)
    # 31
    BasicEPSIncludingExtraordinaryItems          = Column(Float)
    # 32
    DilutionAdjustment                           = Column(Float)
    # 33
    DilutedWeightedAverageShares                 = Column(Float)
    # 34
    DilutedEPSExcludingExtraordinaryItems        = Column(Float)
    # 35
    DilutedEPSIncludingExtraordinaryItems        = Column(Float)
    # 36
    DividendsPerShareLessCommonStockPrimaryIssue = Column(Float)
    # 37
    GrossDividendsLessCommonStock                = Column(Float)
    # 38
    NetIncomeAfterStockBasedCompExpense          = Column(Float)
    # 39
    BasicEPSAfterStockBasedCompExpense           = Column(Float)
    # 40
    DilutedEPSAfterStockBasedCompExpense         = Column(Float)
    # 41
    Depreciation_Supplemental                    = Column(Float)
    # 42
    TotalSpecialItems                            = Column(Float)
    # 43
    NormalizedIncomeBeforeTaxes                  = Column(Float)
    # 44
    EffectOfSpecialItemsOnIncomeTaxes            = Column(Float)
    # 45
    IncomeTaxesExImpactOfSpecialItems           = Column(Float)
    # 46
    NormalizedIncomeAfterTaxes                  = Column(Float)
    # 47
    NormalizedIncomeAvailToCommon               = Column(Float)
    # 48
    BasicNormalizedEPS                          = Column(Float)
    # 49
    DilutedNormalizedEPS                        = Column(Float)
    def __str__(self):
        return "<IncomeStatement( id='%s', 'info_id='%s', Revenue='%s, CoGS='%s''" % (self.id, self.info_id, self.Revenue, self.CostOfRevenueTotal)

class BalanceSheets(Base):
    __tablename__ = "BalanceSheets"
    # PK
    id = Column(Integer,primary_key=True)
    # FK
    info_id = Column(Integer,ForeignKey("Info.id"))
    info    = relationship("Info", backref=backref("BalanceSheets"))
    # data - headers
    Annual      = Column(Boolean)
    Period      = Column(DateTime,nullable=False)
    QueryDate   = Column(DateTime,nullable=False)
    # 1
    CashAndEquivalents                               = Column(Float)
    # 2
    ShortTermInvestments                             = Column(Float)
    # 3
    CashAndShortTermInvestments                      = Column(Float)
    # 4
    AccountsReceivableLessTrade_Net                  = Column(Float)
    # 5
    Receivables_Other                                = Column(Float)
    # 6
    TotalReceivables_Net                             = Column(Float)
    # 7
    TotalInventory                                   = Column(Float)
    # 8
    PrepaidExpenses                                  = Column(Float)
    # 9
    OtherCurrentAssets_Total                         = Column(Float)
    # 10
    TotalCurrentAssets                               = Column(Float)
    # 11
    Property_Plant_Equipment_Total                   = Column(Float)
    # 12
    AccumulatedDepreciation_Total                     = Column(Float)
    # 13
    Goodwill_Net                                     = Column(Float)
    # 14
    Intangibles_Net                                  = Column(Float)
    # 15
    LongTermInvestments                              = Column(Float)
    # 16
    OtherLongTermAssets_Total                        = Column(Float)
    # 17
    TotalAssets                                      = Column(Float)
    # 18
    AccountsPayable                                  = Column(Float)
    # 19
    AccruedExpenses                                  = Column(Float)
    # 20
    NotesPayable_ShortTermDebt                       = Column(Float)
    # 21
    CurrentPortOfLongTermDebt_CapitalLeases          = Column(Float)
    # 22
    OtherCurrentLiabilities_Total                    = Column(Float)
    # 23
    TotalCurrentLiabilities                          = Column(Float)
    # 24
    LongTermDebt                                     = Column(Float)
    # 25
    CapitalLeaseObligations                          = Column(Float)
    # 26
    LongTermDebt                                     = Column(Float)
    # 27
    TotalDebt                                        = Column(Float)
    # 28
    DeferredIncomeTax                                = Column(Float)
    # 29
    MinorityInterest                                 = Column(Float)
    # 30
    OtherCurrentLiabilities_Total                    = Column(Float)
    # 31
    TotalLiabilities                                 = Column(Float)
    # 32
    RedeemablePreferredStock_Total                   = Column(Float)
    # 33
    PreferredStockLessNonRedeemable_Net              = Column(Float)
    # 34
    CommonStock_Total                                = Column(Float)
    # 35
    AdditionalPaidInCapital                          = Column(Float)
    # 36
    RetainedEarnings_AccumulationDeficit_           = Column(Float)
    # 37
    TreasuryStockLessCommon                          = Column(Float)
    # 38
    OtherEquity_Total                                = Column(Float)
    # 39
    TotalEquity                                      = Column(Float)
    # 40
    TotalLiabilitiesAndShareholdersEquity            = Column(Float)
    # 41
    SharesOutsLessCommonStockPrimaryIssue            = Column(Float)
    # 42
    TotalCommonSharesOutstanding                     = Column(Float)


class CashFlowStatements(Base):
    __tablename__ = "CashFlowStatements"
    # PK
    id = Column(Integer,primary_key=True)
    # FK
    info_id = Column(Integer,ForeignKey("Info.id"))
    info    = relationship("Info", backref=backref("CashFlowStatements"))
    # data - headers
    Annual      = Column(Boolean)
    Period      = Column(DateTime,nullable=False)
    QueryDate   = Column(DateTime,nullable=False)
    # 1
    NetIncome                                = Column(Float)
    # 2
    Depreciation_Depletion                   = Column(Float)
    # 3
    Amortization                             = Column(Float)
    # 4
    DeferredTaxes                            = Column(Float)
    # 5
    NonCashItems                             = Column(Float)
    # 6
    ChangesInWorkingcapital                  = Column(Float)
    # 7
    CashFromOperatingActivities              = Column(Float)
    # 8
    CapitalExpenditures                      = Column(Float)
    # 9
    OtherInvestingCashFlowItems_Total        = Column(Float)
    # 10
    CashFromInvestingActivities              = Column(Float)
    # 11
    FinancingCashFlowItems                   = Column(Float)
    # 12
    TotalCashDividendsPaid                   = Column(Float)
    # 13
    Issuance_Retirement_ofStock_Net          = Column(Float)
    # 14
    Issuance_Retirement_ofDebt_Net           = Column(Float)
    # 15
    CashFromFinancingActivities              = Column(Float)
    # 16
    ForeignExchangeEffects                   = Column(Float)
    # 17
    NetChangeInCash                          = Column(Float)
    # 18
    CashInterestPaid_Supplemental            = Column(Float)
    # 19
    CashTaxesPaid_Supplemental               = Column(Float)

class Addresses(Base):
    __tablename__ = "Addresses"
    # PK
    id = Column(Integer,primary_key=True)
    # data
    Street  = Column(String, nullable=True)
    Zip     = Column(String, nullable=True)
    City    = Column(String, nullable=True)
    State   = Column(String, nullable=True)
    Country = Column(String, nullable=True)
    Phone   = Column(String, nullable=True)
    Fax     = Column(String, nullable=True)
    # FK
    info_id = Column(Integer, ForeignKey("Info.id"))
    info    = relationship("Info", backref=backref("Addresses"))

    def __repr__(self):
        return "<Addresses ( id ='%s', Street='%s', Zip='%s', City='%s',       \
                             State='%s', Country='%s', Phone='%s', Fax='%s' )" \
                % ( self.id, self.Street, self.Zip, self.City, \
                    self.State, self.Country, self.Phone, self.Fax )
