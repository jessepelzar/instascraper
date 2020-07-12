import xml.etree.ElementTree as ET

import requests
from geopy.geocoders import Nominatim


def get_cities(entry):
    geolocator = Nominatim(user_agent="attreya")
    location = geolocator.geocode(entry)
    lat = location.latitude
    long = location.longitude
    print((location.latitude, location.longitude))

    referer = "https://www.freemaptools.com/find-cities-and-towns-inside-radius.htm"
    url = "https://www.freemaptools.com/ajax/get-all-cities-inside.php?lat=" + str(lat) + "&lng=" + str(
        long) + "&radius=30"

    response = requests.get(url, headers={"Referer": referer})
    root = ET.fromstring(response.content)

    cities_list = []
    dist_list = []
    for city in reversed(root):

        city_name = city.attrib["name"]
        if entry.lower() != city_name.lower():
            name = city.attrib["name"]
            dist = city.attrib["dist"]
            cities_list.append(name)
            dist_list.append(dist)
    return cities_list, dist_list
