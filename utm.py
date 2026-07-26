from pyproj import Transformer

# Conversion functionalities 
# the function are based in the south hemisphere, just for peru 

BASE_EPSG = 32700
DESTINATION_EPSG = 4326

def utm_to_geodetic(east, north, utm_zone):

    source_epsg = BASE_EPSG + utm_zone

    transformer = Transformer.from_crs(source_epsg, DESTINATION_EPSG, always_xy=True) #function calling from pyproj

    longitude, latitude = transformer.transform(east, north) # transform the utm coordinates to geodetic coordinates

    return latitude, longitude

    






    


