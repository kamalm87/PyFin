from PyFin import Company
from traceback import format_exc
from PyFin.DataBase.ConnectionDB  import ConnectionDB
from PyFin.DataBase.WriteDB import WriteDB
from PyFin.DataBase.QueryDB       import QueryDB 
from PyFin.DataBase.UpdateDB      import UpdateDB 
from PyFin.ModelDB import Query

class CompanyDB(object):
    def __init__(self,connectionstring):
        print(connectionstring)
        self.dbc = ConnectionDB(connectionstring)
        self.dbw = WriteDB(self.dbc.session) 
        self.dbq = QueryDB(self.dbc.session)
        self.dbu = UpdateDB(self.dbw)
        self.aux = _companyDBAux(self.dbc.session,self.dbw)
        self.dbw.update = self.dbu 

    def CreateAndWriteCompany(self,term,commit=False,updateIfExists=False,recordExceptions=False):
        # checks if a record of the company exists in the database
        query = Query()
        
        # cache the original search term, which may potentially have its
        # certain values converted into special html characters
        # e.g.: ' ' -> '%20'
        # NOTE: important for mapping unique search terms, t will be used
        #       for the database, while a potentially altered value of term
        #       may be produced 
        t = term

        if not updateIfExists and t in self.dbw.queries: 
            print(t, " exists already, skipping")
            q = self.dbw.queries[t]
            return (term, "Exists", q)
        else:
            print("*****QUERYING: ", t)
            term = term.replace(" ", "%20")
            c = Company.Company()
            c.extractHTML(term)
            print("$$$$$$$$EXTRACTED: ", c.Name)
            if c.Name:
                res = self.dbw.assignCompany(c,commit)
                self.aux.queryAux(t,self.dbw.queries,True,c,self.dbw.companies,self.dbw.tickers,recordExceptions)
                return ( "\""+t+"\"", "Written", "\""+ c.Name + "(" + c.Ticker + ")\"", c, res)
            else:
                self.aux.queryAux(t, self.dbw.queries, False, c, None, None, recordExceptions)
                return ( "\""+t+"\"", "Does not exist", "N\A") 

        def UpdateCompany(self,term,commit=False):
            self.dbu.CompanyUpdate(term)

class _companyDBAux(object):
    def __init__(self,session,dbw):
        self.session = session
        self.dbw = dbw

    def queryAux(self,t,queries,hasCompany,c,companies,tickers,recordExceptions):
        query = Query()
        result = None
        if t in queries:
            result = True
            query = self.session.query(Query).filter(Query.Term==t).one()
            if hasCompany:
                if c.Name in companies:
                    query.info_id = companies[c.Name] 
                elif c.Ticker in tickers:
                    query.info_id = tickers[c.Ticker]
            self.session.commit()
            if recordExceptions and c.Exceptions:
                for e in c.Exceptions:
                    mt = c.Exceptions[e]
                    m = str(mt).replace("\n","||")
                    self.dbw.recordCompanyException(c,e,m,True)     
            queries[t] = hasCompany
        else:
            result = False
            query.Term = t
            if hasCompany:
                query.info_id = companies[c.Name]
                queries[t] = hasCompany
            else:
                queries[t] = hasCompany
            self.session.add(query)
            self.session.commit()
            if recordExceptions and c and c.Exceptions:
                q_id = query.id
                for e in c.Exceptions:
                    mt = c.Exceptions[e]
                    m = str(mt)
                    m = str(mt).replace("\n","||")
                    self.dbw.recordExceptionsQuery(q_id,e,m,True)     
        return result            

            
        
            

                                
    

        
"""
        if term in self.dbw.companies or term in self.dbw.tickers:
            print(term)
            if updateIfExists:
                return (False, "Exists", UpdateCompany(term))
            else:
                return (False, "Exists", None)
            
            c = Company.Company()
            c.extractHTML(term)
            print(c.Name)
            # if company data extraction appears to retrieve an insignificent 
            # amount of data from the query 
            if not c.Name or c.Name == "":
                return (False,(term,c))
            # otherwise: write the result to the database, and commit if the 
            # parameter is set to True
        else:
            print("ELSE --> Querying: ", term)
            c = Company.Company()
            c.extractHTML(term)
            print("got it: ",c.Name)
            self.dbw.assignCompany(c,commit)
            return (True, term, "Session Write",(term,c.Name,c.Ticker))

    def UpdateCompany(self,term,commit=False):
        self.dbu.CompanyUpdate(term)
"""
