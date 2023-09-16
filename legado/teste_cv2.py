import cv2
import numpy as np

# Load the image
image = cv2.imread('ship_show.jpg')

# Get the image dimensions
image_height, image_width = image.shape[:2]

# Ship heading in degrees (example value)
ship_heading_degrees = 45.0

# Convert the ship heading to radians
ship_heading_radians = np.radians(ship_heading_degrees)

# Define the length and color of the heading indicator
indicator_length = min(image_width, image_height) * 0.4
indicator_color = (0, 0, 255)  # Red

# Calculate the endpoint of the heading indicator
center_x = image_width // 2
center_y = image_height // 2
end_x = int(center_x + indicator_length * np.sin(ship_heading_radians))
end_y = int(center_y - indicator_length * np.cos(ship_heading_radians))

# Draw the heading indicator on the image
cv2.arrowedLine(image, (center_x, center_y), (end_x, end_y), indicator_color, thickness=2, tipLength=0.2)

# Display the image with the heading indicator
cv2.imshow('Image with Heading Indicator', image)
cv2.waitKey(0)
cv2.destroyAllWindows()