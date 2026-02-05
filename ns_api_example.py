import requests
import json # used to visualize the json

# Most queries require station codes instead of station names
#                                                                    ES = Enschede    ZL = Zwolle
url = "https://gateway.apiportal.ns.nl/reisinformatie-api/api/v3/trips?fromStation=ES&toStation=ZL"
headers = {
    "Ocp-Apim-Subscription-Key": "THIS_IS_NOT_A_REAL_API_KEY" # <- get your own api key on https://apiportal.ns.nl/
}

response = requests.get(url, headers=headers)

# print(response.status_code, json.dumps(response.json(), indent=4)) # uncomment to see the json
data = response.json()
for trip in data["trips"]:
    print("\n----- Take the train")
    for leg in trip["legs"]:
        for stop in leg["stops"]:
            stop_name = stop["name"]
            platform = stop["plannedArrivalTrack"] # perron
            print(stop_name, platform)
        print(" -> exit the train")
print("\n")


# To get the station code you can use the following url
# https://gateway.apiportal.ns.nl/reisinformatie-api/api/v2/stations[?q][&countryCodes][&limit]

city_name = "Enschede"
url = f"https://gateway.apiportal.ns.nl/reisinformatie-api/api/v2/stations?q={city_name}&limit=1"
response = requests.get(url, headers=headers)

# print(response.status_code, json.dumps(response.json(), indent=4)) # uncomment to see the json
data = response.json()
payload = data["payload"]
for trip in payload:
    code = trip["code"]
    print(f"The code of {city_name} is: {code} with Tracks: ", end=" ")

    for spoor in trip["sporen"]:
        track_number = spoor["spoorNummer"]
        print(track_number, end=" ")

print("\n")
