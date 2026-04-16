# MP4 to GIF Conversion Tool

This tool converts all MP4 videos in the `mp4` folder to GIF format while preserving the directory structure.

## Features

- **Recursive Processing**: Automatically finds all .mp4 files in subdirectories
- **Size Optimization**: Reduces GIF file size by resizing videos to 70% of original size
- **Smart Skipping**: Skips files that have already been converted
- **Detailed Logging**: Provides comprehensive logs of the conversion process
- **Error Handling**: Gracefully handles conversion errors and continues processing

## Prerequisites

Make sure you have Python 3.6+ installed on your system.

## Installation

1. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

   Or install manually:
   ```bash
   pip install moviepy imageio imageio-ffmpeg
   ```

## Usage

1. Navigate to the `sign-language-translator` directory
2. Run the conversion script:
   ```bash
   python convert_mp4_to_gif.py
   ```

## Configuration

You can modify the following parameters in the `convert_mp4_to_gif.py` file:

- **`resize_factor`**: Controls the output size (default: 0.7 = 70% of original)
- **`fps`**: Frames per second for the output GIF (default: 15)
- **`mp4_folder`**: Source folder containing MP4 files (default: "mp4")
- **`gif_folder`**: Destination folder for GIF files (default: "gif_ASL")

## Output

- **GIF files**: Created in a separate `gif_ASL` folder with the same directory structure as `mp4`
- **Log file**: `conversion_log.txt` contains detailed conversion logs
- **Console output**: Real-time progress updates

## File Structure

```
mp4/                          gif_ASL/
├── word1/                    ├── word1/
│   └── word1.mp4            │   └── word1.gif  ← Generated
├── word2/                    ├── word2/
│   └── word2.mp4            │   └── word2.gif  ← Generated
└── ...                       └── ...
```

## Troubleshooting

### Common Issues

1. **ModuleNotFoundError**: Install missing dependencies with `pip install -r requirements.txt`
2. **Permission errors**: Ensure you have write permissions to the mp4 directory
3. **FFmpeg not found**: Install FFmpeg on your system:
   - Windows: Download from https://ffmpeg.org/
   - Mac: `brew install ffmpeg`
   - Linux: `sudo apt-get install ffmpeg`

### Performance Tips

- **Large files**: Consider increasing the `resize_factor` if GIFs are too small
- **Slow conversion**: Lower the `fps` value to speed up processing
- **Disk space**: Monitor available space as GIFs can be large

## Technical Details

- Uses MoviePy library for video processing
- Optimizes GIFs using FFmpeg
- Processes files in alphabetical order
- Skips existing GIF files to avoid redundant processing
- Logs all operations for debugging purposes

## Example Output

```
2024-01-15 10:30:00 - INFO - Starting MP4 to GIF conversion process
2024-01-15 10:30:00 - INFO - Resize factor: 0.7
2024-01-15 10:30:00 - INFO - Output FPS: 15
2024-01-15 10:30:01 - INFO - Found 1500 MP4 files
2024-01-15 10:30:02 - INFO - Converting mp4/a/a.mp4 to mp4/a/a.gif
2024-01-15 10:30:05 - INFO - Successfully converted mp4/a/a.mp4 to GIF
...
2024-01-15 11:45:30 - INFO - ==================================================
2024-01-15 11:45:30 - INFO - CONVERSION SUMMARY
2024-01-15 11:45:30 - INFO - ==================================================
2024-01-15 11:45:30 - INFO - Total MP4 files found: 1500
2024-01-15 11:45:30 - INFO - Successful conversions: 1495
2024-01-15 11:45:30 - INFO - Failed conversions: 5
2024-01-15 11:45:30 - INFO - Conversion complete! Check 'conversion_log.txt' for detailed logs. 