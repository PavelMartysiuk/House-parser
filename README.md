# House parser.


Script parses advertisemnts about house for sale with cost below 80 000$ and area below 200 м2 in Kiev-Svyatoshinsky district from sites:
 1)https://blagovist.ua
 2)https://100realty.ua
 3)https://www.country.ua
 4)https://meget.kiev.ua
 5)https://bn.ua
 6)https://rieltor.ua
 7)https://prostodom.ua
 8)https://address.ua
 
Script saves advertisemnts in database House_advertisements in table houses.


# Structure of table "houses":

Column id is column for number of record.(autoadd)
Column link is column for advertisemnt link.(Type is String)
Column cost is column for house cost.(Type is Float)
Colunm area is column for house area.(Type is float)
Column date saves a date of advertisemnt parsing.(autoadd)


