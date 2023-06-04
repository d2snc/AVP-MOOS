from pyproj import Proj

LatOrigin = -22.93335 
LongOrigin = -43.136666665 

# Create the projection object
projection = Proj(proj='aeqd', ellps='WGS84',
                  datum='WGS84', lat_0=LatOrigin, lon_0=LongOrigin)

longitude = -43.15975520  # Example longitude coordinate
latitude = -22.91222853  # Example latitude coordinate

x, y = projection(longitude, latitude)

print("Longitude :"+str(x))
print("Latitude : "+str(y))