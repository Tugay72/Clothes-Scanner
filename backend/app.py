from flask import Flask, request, jsonify, send_file
import cv2
import numpy as np
import os
import webcolors
from math import sqrt

CSS3_NAMES_TO_HEX = {
    'black': '#000000',
    'white': '#FFFFFF',
    'red': '#FF0000',
    'green': '#008000',
    'blue': '#0000FF',
    'yellow': '#FFFF00',
    'orange': '#FFA500',
    'purple': '#800080',
    'cyan': '#00FFFF',
    'magenta': '#FF00FF',
    'gray': '#808080',
    'brown': '#A52A2A',
    'pink': '#FFC0CB',
    'lime': '#00FF00',
    'teal': '#008080',
    'navy': '#000080',
    'lightgray': '#D3D3D3',
    'darkgray': '#A9A9A9',
    'chartreuse': '#7FFF00',
    'coral': '#FF7F50',
    'salmon': '#FA8072',
    'violet': '#EE82EE',
    'indigo': '#4B0082',
    'gold': '#FFD700',
    'silver': '#C0C0C0',
    'bronze': '#CD7F32',
    'crimson': '#DC143C',
    'orchid': '#DA70D6',
    'mintcream': '#F5FFFA',
    'lavender': '#E6E6FA',
    'beige': '#F5F5DC',
    'antiquewhite': '#FAEBD7',
    'aliceblue': '#F0F8FF',
    'azure': '#F0FFFF',
    'honeydew': '#F0FFF0',
    'seashell': '#FFF5EE',
    'ghostwhite': '#F8F8FF',
    'snow': '#FFFAFA',
    'oldlace': '#FDF5E6',
    'linen': '#FAF0E6',
    'papayawhip': '#FFEFD5',
    'blanchedalmond': '#FFEBCD',
    'bisque': '#FFE4C4',
    'peachpuff': '#FFDAB9',
    'moccasin': '#FFE4B5',
    'navajowhite': '#FFDEAD',
    'wheat': '#F5DEB3',
    'burlywood': '#DEB887',
    'tan': '#D2B48C',
    'rosybrown': '#BC8F8F',
    'saddlebrown': '#8B4513',
    'sienna': '#A0522D',
    'chocolate': '#D2691E',
    'peru': '#CD853F',
    'darkorange': '#FF8C00',
    'lightsalmon': '#FFA07A',
    'darksalmon': '#E9967A',
    'lightpink': '#FFB6C1',
    'deeppink': '#FF1493',
    'hotpink': '#FF69B4',
    'fuchsia': '#FF00FF',
    'mediumvioletred': '#C71585',
    'darkviolet': '#9400D3',
    'blueviolet': '#8A2BE2',
    'mediumorchid': '#BA55D3',
    'darkorchid': '#9932CC',
    'darkblue': '#00008B',
    'mediumblue': '#0000CD',
    'royalblue': '#4169E1',
    'steelblue': '#4682B4',
    'dodgerblue': '#1E90FF',
    'cornflowerblue': '#6495ED',
    'lightskyblue': '#87CEFA',
    'skyblue': '#87CEEB',
    'lightblue': '#ADD8E6',
    'powderblue': '#B0E0E6',
    'paleturquoise': '#AFEEEE',
    'turquoise': '#40E0D0',
    'mediumturquoise': '#48D1CC',
    'darkturquoise': '#00CED1',
    'lightseagreen': '#20B2AA',
    'darkseagreen': '#8FBC8F',
    'mediumseagreen': '#3CB371',
    'seagreen': '#2E8B57',
    'forestgreen': '#228B22',
    'greenyellow': '#ADFF2F',
    'yellowgreen': '#9ACD32',
    'olive': '#808000',
    'olivedrab': '#6B8E23',
    'darkolivegreen': '#556B2F',
    'lawngreen': '#7CFC00',
    'chartreuse': '#7FFF00',
    'limegreen': '#32CD32',
    'mediumspringgreen': '#00FA9A',
    'springgreen': '#00FF7F',
    'lightgreen': '#90EE90',
    'darkgreen': '#006400',
    'mediumaquamarine': '#66CDAA',
    'aquamarine': '#7FFFD4',
    'darkcyan': '#008B8B',
    'lightcyan': '#E0FFFF',
    'cadetblue': '#5F9EA0',
    'mediumslateblue': '#7B68EE',
    'slateblue': '#6A5ACD',
    'darkslateblue': '#483D8B',
    'mediumpurple': '#9370DB',
    'blue': '#0000FF'
}

app = Flask(__name__)

PROCESSED_IMAGE_DIR = 'images'
os.makedirs(PROCESSED_IMAGE_DIR, exist_ok=True)

@app.route('/')
def home():
    return 'Welcome!'


def get_closest_color_name(rgb_color):
    # Threshold to avoid misclassifying near-black or near-white colors
    if all(val < 30 for val in rgb_color):
        return "black"
    if all(val > 225 for val in rgb_color):
        return "white"
    
    try:
        # Check for an exact match first
        color_name = webcolors.rgb_to_name(rgb_color)
    except ValueError:
        # If no exact match, find the closest color
        closest_name = None
        min_distance = float('inf')
        for name, hex_value in CSS3_NAMES_TO_HEX.items():
            r, g, b = webcolors.hex_to_rgb(hex_value)
            distance = sqrt((r - rgb_color[0]) ** 2 + (g - rgb_color[1]) ** 2 + (b - rgb_color[2]) ** 2)
            if distance < min_distance:
                min_distance = distance
                closest_name = name
        color_name = closest_name
    return color_name





@app.route('/process-image', methods=['POST'])
def process_image_route():
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400

    image_file = request.files['image']
    
    # Save the original image temporarily
    original_image_path = os.path.join(PROCESSED_IMAGE_DIR, 'original_image.jpg')
    image_file.save(original_image_path)

    # Resets the file pointer to the beginning of the file
    image_file.seek(0)

    # Read the image
    img_array = np.frombuffer(image_file.read(), np.uint8)
    
    # Check if the buffer is empty
    if img_array.size == 0:
        return jsonify({'error': 'Empty image buffer'}), 400

    # Decode the image
    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

    # Check if the image was loaded correctly
    if img is None:
        return jsonify({'error': 'Failed to decode image'}), 400

    # Resize the image
    img_resized = cv2.resize(img, (480, 640))  # Resize for faster processing

    # Find the dominant color using K-means clustering
    pixels = img_resized.reshape(-1, 3)  # Reshape the image to be a list of pixels
    k = 5  # Number of clusters
    _, labels, centers = cv2.kmeans(pixels.astype(np.float32), k, None, 
                                     (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0), 
                                     10, cv2.KMEANS_RANDOM_CENTERS)

    # Get the dominant color
    dominant_color = centers[np.argmax(np.bincount(labels.flatten()))]
    dominant_color_name = get_closest_color_name(tuple(dominant_color))

    # Calculate center of the image
    h, w, _ = img_resized.shape
    center_x, center_y = w // 2, h // 2
    size = 100
    cropped_center = img[center_y - size // 2:center_y + size // 2,
                        center_x - size // 2:center_x + size // 2]

    # Average color of the cropped center
    average_color = cropped_center.mean(axis=(0, 1)).astype(int)
    average_color_name = get_closest_color_name(tuple(average_color))

    # Save the dominant & average color to a text file
    dominant_color_path = os.path.join(PROCESSED_IMAGE_DIR, 'dominant_color.txt')
    
    with open(dominant_color_path, 'w') as f:
        f.write(f'Dominant Color (RGB): {dominant_color.astype(int).tolist()}\n')
        f.write(f'Dom Name (Eng): {dominant_color_name}\n')
        f.write(f'Avg Color (Eng): {average_color.tolist()}\n')
        f.write(f'Avg Name (Eng): {average_color_name}\n')

    # Save the processed image
    processed_image_path = os.path.join(PROCESSED_IMAGE_DIR, 'processed_image.jpg')
    cv2.imwrite(processed_image_path, img_resized)

    # Return the URL of the processed image
    return jsonify({
        'processed_image_url': f'/processed-image',
        'dominant_color': dominant_color.tolist(),
        'dominant_color_name': dominant_color_name,
        'average_color': average_color.tolist(),
        'average_color_name': average_color_name,
    })


@app.route('/processed-image', methods=['GET'])
def get_processed_image():
    processed_image_path = os.path.join(PROCESSED_IMAGE_DIR, 'processed_image.jpg')
    
    # Check if the processed image exists
    if os.path.exists(processed_image_path):
        return send_file(processed_image_path, mimetype='image/jpeg')
    else:
        return jsonify({'error': 'Processed image not found'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)



