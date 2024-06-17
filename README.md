# Image Conversion and Compression
This script allows you to convert an RGBA image into a compressed binary format and vice versa using Python with multithreading for faster processing.

## Requirements
- Python 3.x
= Pillow (Python Imaging Library, PIL)

## Usage
1. Convert RGBA Image to Binary

To convert an RGBA image (input_image.png) to a binary file (output.bin):
```
from convert import convertTR
input_image = "input_image.png"
output_binary = "output.bin"
convertTR(input_image, output_binary)`
```

This function utilizes multithreading (num_threads threads) to process the image in chunks for efficient conversion.

2. Convert Binary File back to RGBA Image

To convert a binary file (input.bin) back to an RGBA image (output_image.png):

```
from convert import image_from_file

input_binary = "input.bin"
output_image = "output_image.png"
image_from_file(input_binary, output_image)
```

This function reconstructs the original image from the compressed binary file.

## Parameters
- convertTR(image_path, output_path, num_threads=8): Converts an RGBA image to a binary file.

- image_path: Path to the input RGBA image.
- output_path: Path to save the output binary file.
- num_threads: Number of threads to use for processing (default is 8).
- image_from_file(file_path, output_image_path): Converts a binary file back to an RGBA image.

- file_path: Path to the input binary file.
- output_image_path: Path to save the output RGBA image.
### Notes
The conversion process utilizes multithreading to enhance performance on multi-core systems.
 Debugging (DEBUG=True) prints RGBA values during the conversion process.
