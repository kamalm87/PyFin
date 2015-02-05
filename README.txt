This is a HTML scraper to extract publically accessible information from www.google.com/finance.

Querying:
	- company names
	- tickers
	- metadata URLs
Storage:
	- The data is intended to be stored in a PostgreSQL database.
	- refer to PyFin/ModelDB.py for the detailed schema, which uses
	  the sqlAlchemy as the ORM.
Dependencies:
	- Python3
	- BeautifulSoup4
	- PsycoPG2
	- SqlAlchemy
	- VirtualEnv

Example:
	- Notes: 
		* PostgreSQL assumptions (alter in tPyFin.py if necessary):
			- DataBase: testDB
			- Port: 5432 
			- Host: localhost
			- User: postgres
			- Password for User: postgres 
		* An internet connection is assumed.
          	* The web scraper is subject to break at any time, which will necessitate
		  code adjustment. 
	- From this folder, assuming that the Python3 and virtualenv are satisfied:
		1) $ virtualenv env -p python3
		2) $ source env/bin/activate
		3) $ pip3 install -r requirements.txt
		4) $ create a database named testDB using pSQL
		5) $ python3 tPyFin.py 
	- The above should create a database containing finanical information of the 
 	  30 companies that belong to the Dow Jones Industrial Average. 
