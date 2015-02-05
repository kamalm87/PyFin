from PyFin import CompanyDB

user     = 'postgres'
password = 'postgres'
port     = '5432'
host = 'localhost'
db       = 'testDB'
dbc = 'postgresql://' + user + ':' + password + '@' + host + ':' + port + '/' + db
#dbc = 'postgresql://postgres:postgres@localhost:5432/testDB'
cDB = CompanyDB.CompanyDB(dbc)
djia30 = 'djia30.csv'
ff = tuple(open(djia30,'r'))
lines = []
for f in ff:
    lines.append(f.replace("\n",""))

results = []
for l in lines:
    print(l)
    results.append(cDB.CreateAndWriteCompany(l,True,True,True))


for r in results:
    print(r)
print(cDB)
