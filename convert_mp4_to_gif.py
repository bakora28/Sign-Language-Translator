#!/usr/bin/env python3
"""
Script to convert all MP4 videos in the mp4 folder to GIF format.
This script recursively searches through all subdirectories in the mp4 folder,
finds MP4 files, and converts them to GIF format while preserving the directory structure.
"""

import os
import sys
from pathlib import Path
import logging
from moviepy.editor import VideoFileClip

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('conversion_log.txt'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def convert_mp4_to_gif(mp4_path, gif_path, resize_factor=0.5, fps=10):
    """
    Convert an MP4 file to GIF format.
    
    Args:
        mp4_path (str): Path to the input MP4 file
        gif_path (str): Path to the output GIF file
        resize_factor (float): Factor to resize the video (0.5 = 50% of original size)
        fps (int): Frames per second for the output GIF
    
    Returns:
        bool: True if conversion successful, False otherwise
    """
    try:
        logger.info(f"Converting {mp4_path} to {gif_path}")
        
        # Load the video clip
        with VideoFileClip(mp4_path) as clip:
            # Resize the clip to reduce file size
            if resize_factor != 1.0:
                clip = clip.resize(resize_factor)
            
            # Convert to GIF
            clip.write_gif(
                gif_path,
                fps=fps,
                program='ffmpeg',  # Use ffmpeg for better quality
                opt='optimizeplus',  # Optimize for smaller file size
                verbose=False,
                logger=None
            )
        
        logger.info(f"Successfully converted {mp4_path} to GIF")
        return True
        
    except Exception as e:
        logger.error(f"Error converting {mp4_path}: {str(e)}")
        return False

def find_mp4_files(root_dir):
    """
    Recursively find all MP4 files in the given directory.
    
    Args:
        root_dir (str): Root directory to search
    
    Returns:
        list: List of paths to MP4 files
    """
    mp4_files = []
    root_path = Path(root_dir)
    
    if not root_path.exists():
        logger.error(f"Directory {root_dir} does not exist")
        return mp4_files
    
    # Search for MP4 files recursively
    for mp4_file in root_path.rglob("*.mp4"):
        mp4_files.append(str(mp4_file))
    
    logger.info(f"Found {len(mp4_files)} MP4 files")
    return mp4_files

def main():
    """Main function to convert all MP4 files to GIF."""
    
    # Configuration
    mp4_folder = "mp4"
    gif_folder = "gif_ASL"  # New parent folder for GIF files
    resize_factor = 0.7  # Resize to 70% of original size to reduce file size
    fps = 15  # Frames per second for GIF
    
    logger.info("Starting MP4 to GIF conversion process")
    logger.info(f"Source folder: {mp4_folder}")
    logger.info(f"Destination folder: {gif_folder}")
    logger.info(f"Resize factor: {resize_factor}")
    logger.info(f"Output FPS: {fps}")
    
    # Check if mp4 folder exists
    if not os.path.exists(mp4_folder):
        logger.error(f"MP4 folder '{mp4_folder}' not found!")
        return
    
    # Create gif_ASL folder if it doesn't exist
    if not os.path.exists(gif_folder):
        os.makedirs(gif_folder)
        logger.info(f"Created destination folder: {gif_folder}")
    
    # Find all MP4 files
    mp4_files = find_mp4_files(mp4_folder)
    
    if not mp4_files:
        logger.warning("No MP4 files found!")
        return
    
    # Convert each MP4 file to GIF
    successful_conversions = 0
    failed_conversions = 0
    
    for mp4_file in mp4_files:
        # Create corresponding GIF path in gif_ASL folder
        # Replace 'mp4' with 'gif_ASL' in the path and change extension
        relative_path = os.path.relpath(mp4_file, mp4_folder)
        gif_file = os.path.join(gif_folder, relative_path).rsplit('.', 1)[0] + '.gif'
        
        # Create subdirectory in gif_ASL if it doesn't exist
        gif_dir = os.path.dirname(gif_file)
        if not os.path.exists(gif_dir):
            os.makedirs(gif_dir)
            logger.info(f"Created directory: {gif_dir}")
        
        # Skip if GIF already exists (optional)
        if os.path.exists(gif_file):
            logger.info(f"GIF already exists, skipping: {gif_file}")
            continue
        
        # Convert MP4 to GIF
        if convert_mp4_to_gif(mp4_file, gif_file, resize_factor, fps):
            successful_conversions += 1
        else:
            failed_conversions += 1
    
    # Summary
    logger.info("=" * 50)
    logger.info("CONVERSION SUMMARY")
    logger.info("=" * 50)
    logger.info(f"Total MP4 files found: {len(mp4_files)}")
    logger.info(f"Successful conversions: {successful_conversions}")
    logger.info(f"Failed conversions: {failed_conversions}")
    logger.info(f"Conversion complete! Check 'conversion_log.txt' for detailed logs.")

if __name__ == "__main__":
    main()