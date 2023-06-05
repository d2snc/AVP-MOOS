import pyproj

LatOrigin = -22.93335
LongOrigin = -43.136666665

# Create the projection objects
projection_local = pyproj.Proj(proj='aeqd', ellps='WGS84',
                              datum='WGS84', lat_0=LatOrigin, lon_0=LongOrigin)
projection_global = pyproj.Proj(proj='latlong', ellps='WGS84', datum='WGS84')

longitude = -43.15975520  # Example longitude coordinate
latitude = -22.91222853  # Example latitude coordinate

# Perform the forward transformation from global to local coordinates
x, y = pyproj.transform(projection_global, projection_local, longitude, latitude)

print("Local x-coordinate: " + str(x))
print("Local y-coordinate: " + str(y))

# Perform the inverse transformation from local to global coordinates
inv_longitude, inv_latitude = pyproj.transform(projection_local, projection_global, x, y)

print("Inverse Longitude: " + str(inv_longitude))
print("Inverse Latitude: " + str(inv_latitude))
