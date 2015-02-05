from PyFin.ModelDB import *

class ConnectionDB(object): 
    """" For singleton pattern """
    _instance = None
    def _new_(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ConnectionDB, cls).__new__(cls, *args, **kwargs)
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

