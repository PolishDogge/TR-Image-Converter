# THIS BRANCH HAS WAY GREATER COMPRESSION AT THE COST OF SPEED
# AVERAGE IMAGE CONVERSION TIME INCRAESED BY 10x (92 seconds -> 929 seconds)
# The final size has been decreased from 200 MB to 81 MB

import struct
from PIL import Image
import numpy as np
import zlib
import time
import logging
from joblib import Parallel, delayed

DEBUG = False
BATCH_SIZE = 100000  # Define a batch size for processing

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def rgba_to_hex(rgba):
    r, g, b, a = rgba
    return f"{r:02X}{g:02X}{b:02X}{a:02X}"

def process_chunk(image, start_y, end_y):
    width = image.shape[1]
    rgba_values = []
    for y in range(start_y, end_y):
        for x in range(width):
            rgba = tuple(image[y, x])
            if DEBUG:
                logging.debug(f'{x},{y}: {rgba}')
            rgba_values.append((x, y, rgba))
    logging.info(f'Processed chunk from {start_y} to {end_y}')
    return start_y, rgba_values

def pack_data(compressed_rgba_values):
    packed_data = b''
    for count, (x, y, rgba) in compressed_rgba_values:
        packed_data += struct.pack('IHHBBBB', count, x, y, *rgba)
    return packed_data

def convertTR(image_path, output_path, num_threads=8):
    logging.info(f'Starting conversion of {image_path}')
    
    image = Image.open(image_path).convert('RGBA')
    width, height = image.size
    np_image = np.array(image)

    # Calculate chunk size for each thread
    chunk_size = height // num_threads
    futures = []

    start_time = time.time()
    results = Parallel(n_jobs=num_threads)(delayed(process_chunk)(np_image, i * chunk_size, height if i == num_threads - 1 else (i + 1) * chunk_size) for i in range(num_threads))

    processing_time = time.time() - start_time
    logging.info(f"Image processing completed in {processing_time:.2f} seconds")

    # Flatten the list of results
    ordered_rgba_values = [pixel for sublist in results for pixel in sublist[1]]

    # Group consecutive pixels with the same RGBA value within the same row
    compressed_rgba_values = []
    current_run_length = 1
    start_pixel = ordered_rgba_values[0]

    for i in range(1, len(ordered_rgba_values)):
        previous_pixel = ordered_rgba_values[i - 1]
        current_pixel = ordered_rgba_values[i]

        if (previous_pixel[2] == current_pixel[2] and
            previous_pixel[1] == current_pixel[1] and
            current_pixel[0] == previous_pixel[0] + 1):
            current_run_length += 1
        else:
            compressed_rgba_values.append((current_run_length, start_pixel))
            current_run_length = 1
            start_pixel = current_pixel

    # Add the last group of pixels
    compressed_rgba_values.append((current_run_length, start_pixel))

    packing_start_time = time.time()
    # Pack and compress the data in batches
    packed_data = b''
    for i in range(0, len(compressed_rgba_values), BATCH_SIZE):
        batch = compressed_rgba_values[i:i + BATCH_SIZE]
        packed_data += pack_data(batch)
        logging.info(f'Packed batch {i // BATCH_SIZE + 1}')

    compressed_data = zlib.compress(packed_data)
    compression_time = time.time() - packing_start_time
    logging.info(f"Packing and compression completed in {compression_time:.2f} seconds")

    # Save compressed data to file
    with open(output_path, 'wb') as f:
        f.write(compressed_data)
    logging.info(f'Saved compressed data to {output_path}')

def image_from_file(file_path, output_image_path):
    logging.info(f'Reconstructing image from {file_path}')
    
    with open(file_path, 'rb') as f:
        compressed_data = f.read()

    packed_data = zlib.decompress(compressed_data)

    pixels = []
    max_x, max_y = 0, 0
    offset = 0
    data_size = struct.calcsize('IHHBBBB')
    while offset < len(packed_data):
        unpacked_data = struct.unpack('IHHBBBB', packed_data[offset:offset + data_size])
        offset += data_size
        count, x, y, r, g, b, a = unpacked_data
        for i in range(count):
            pixels.append((x + i, y, (r, g, b, a)))
            if x + i > max_x:
                max_x = x + i
            if y > max_y:
                max_y = y

    width = max_x + 1
    height = max_y + 1

    # Create a new image
    image = Image.new('RGBA', (width, height))

    # Set the pixel values
    for (x, y, rgba) in pixels:
        image.putpixel((x, y), rgba)

    # Save the image
    image.save(output_image_path)
    logging.info(f'Saved reconstructed image to {output_image_path}')

if __name__ == "__main__":
    image_path = 'img.jpeg'
    output_path = 'file.tr'
    output_image_path = 'reconstructed_image.png'
    
    startTime = time.time()
    convertTR(image_path, output_path, num_threads=12)
    logging.info(f'Conversion finished in {time.time()-startTime:.2f} seconds')
