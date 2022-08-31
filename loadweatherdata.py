import urllib.request
import json
import mysql.connector
from datetime import date, datetime, timedelta

# This is the core of our weather query URL
BaseURL = 'https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/weatherdata/'

ApiKey = 'V9DMTC7MX6AXKXZNARMP5JL8K'
# UnitGroup sets the units of the output - us or metric
UnitGroup = 'us'

# Locations for the weather data. Multiple locations separated by pipe (|)
Locations = 'SanMarcos,TX'

# FORECAST or HISTORY
QueryType = 'FORECAST'

# 1=hourly, 24=daily
AggregateHours = '24'

# Params for history only
StartDate = ''
EndDate = ''


# Set up the specific parameters based on the type of query
class DateParam:
    pass


if QueryType == 'FORECAST':
    print(' - Fetching forecast data')
    QueryParams = 'forecast?aggregateHours=' + AggregateHours + '&unitGroup=' + UnitGroup + '&shortColumnNames=true'
else:
    print(' - Fetching history for date: ', DateParam)

    # History requests require a date.  We use the same date for start and end since we only want to query a single
    # date in this example
    QueryParams = 'history?aggregateHours=' + AggregateHours + '&unitGroup=' + UnitGroup + '&startDateTime=' + StartDate + 'T00%3A00%3A00&endDateTime=' + EndDate + 'T00%3A00%3A00'

Locations = '&locations=' + Locations

ApiKey = '&key=' + ApiKey

# Build the entire query
URL = BaseURL + QueryParams + Locations + ApiKey + "&contentType=json"

print(' - Running query URL: ', URL)
print()

response = urllib.request.urlopen(URL)
data = response.read()
weatherData = json.loads(data.decode('utf-8'))

print("Connecting to mysql database")
# connect to the database. Enter your host, username and password
cnx = mysql.connector.connect(host='34.134.150.30',
                              user='root',
                              passwd='instance2',
                              database='mccoy_energy')

cursor = cnx.cursor()

# In this simple example, clear out the existing data in the table

delete_weather_data = ("TRUNCATE TABLE `mccoy_energy`.`weather_data`")
cursor.execute(delete_weather_data)
cnx.commit()

# Create an insert statement for inserting rows of data
insert_weather_data = ("INSERT INTO `mccoy_energy`.`weather_data`"
                       "(`address`,`latitude`,`longitude`,`datetime`,`maxt`,`mint`,`temp`,`precip`,`wspd`,`wdir`,`wgust`,`pressure`)"
                       "VALUES (%(address)s, %(latitude)s, %(longitude)s, %(datetime)s, %(maxt)s,%(mint)s, %(temp)s, %(precip)s, %(wspd)s, %(wdir)s, %(wgust)s, %(pressure)s)")

# Iterate through the locations
locations = weatherData["locations"]
for locationid in locations:
    location = locations[locationid]
    # Iterate through the values (values are the time periods in the weather data)
    for value in location["values"]:
        data_wx = {
            'address': location["address"],
            'latitude': location["latitude"],
            'longitude': location["longitude"],
            'datetime': datetime.utcfromtimestamp(value["datetime"] / 1000.),
            'maxt': value["maxt"] if 'maxt' in value else 0,
            'mint': value["mint"] if 'mint' in value else 0,
            'temp': value["temp"],
            'precip': value["precip"],
            'wspd': value["wspd"],
            'wdir': value["wdir"],
            'wgust': value["wgust"],
            'pressure': value["sealevelpressure"]
        }
        cursor.execute(insert_weather_data, data_wx)
        cnx.commit()

cursor.close()
cnx.close()
print("Database connection closed")

print("Done")
