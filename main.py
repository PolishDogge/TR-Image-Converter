import struct
from PIL import Image
import concurrent.futures
import numpy as np
from zlib import compress, decompress
import time

DEBUG = False

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
                print(f'{x},{y}: {rgba}')
            rgba_values.append((x, y, rgba))
    return start_y, rgba_values

def convertTR(image_path, output_path, num_threads=8):
    image = Image.open(image_path).convert('RGBA')
    width, height = image.size
    np_image = np.array(image)

    # Calculate chunk size for each thread
    chunk_size = height // num_threads
    futures = []

    start_time = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        for i in range(num_threads):
            start_y = i * chunk_size
            end_y = height if i == num_threads - 1 else (i + 1) * chunk_size
            futures.append(executor.submit(process_chunk, np_image, start_y, end_y))

    # Collect results
    results = [None] * num_threads
    for future in concurrent.futures.as_completed(futures):
        start_y, rgba_values = future.result()
        index = start_y // chunk_size
        results[index] = rgba_values

    processing_time = time.time() - start_time
    print(f"Image processing time: {processing_time:.2f} seconds")

    # Flatten the list of results
    ordered_rgba_values = [pixel for sublist in results for pixel in sublist]

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
    # Pack and compress the data
    packed_data = b''
    for count, (x, y, rgba) in compressed_rgba_values:
        packed_data += struct.pack('IHHBBBB', count, x, y, *rgba)

    compressed_data = compress(packed_data)

    compression_time = time.time() - packing_start_time
    print(f"Packing and compression time: {compression_time:.2f} seconds")

    # Save compressed data to file
    with open(output_path, 'wb') as f:
        f.write(compressed_data)

def image_from_file(file_path, output_image_path):
    with open(file_path, 'rb') as f:
        compressed_data = f.read()

    packed_data = decompress(compressed_data)

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

if __name__ == "__main__":
    image_path = 'img.jpeg'
    output_path = 'file.tr'
    output_image_path = 'reconstructed_image.png'

    startTime = time.time()
    convertTR(image_path, output_path, num_threads=12)
    print(f'Finished in {time.time()-startTime:.2f} seconds')
