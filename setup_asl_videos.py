#!/usr/bin/env python3
"""
Setup script for ASL (American Sign Language) video directories and structure
Run this script to create the necessary directories for English sign language videos
"""

import os
import json

def create_asl_directory_structure():
    """Create the directory structure for ASL videos"""
    
    # Base directories
    static_dir = 'static'
    asl_videos_dir = os.path.join(static_dir, 'asl_videos')
    english_sign_videos_dir = os.path.join(static_dir, 'english_sign_videos')
    
    # Create directories
    os.makedirs(asl_videos_dir, exist_ok=True)
    os.makedirs(english_sign_videos_dir, exist_ok=True)
    
    print(f"✅ Created directory: {asl_videos_dir}")
    print(f"✅ Created directory: {english_sign_videos_dir}")
    
    return asl_videos_dir, english_sign_videos_dir

def create_asl_video_mapping_file(asl_videos_dir):
    """Create a JSON file with the ASL video mapping"""
    
    asl_video_mapping = {
        'hello': 'asl_hello.mp4',
        'thank': 'asl_thank.mp4', 
        'you': 'asl_you.mp4',
        'please': 'asl_please.mp4',
        'yes': 'asl_yes.mp4',
        'no': 'asl_no.mp4',
        'good': 'asl_good.mp4',
        'bad': 'asl_bad.mp4',
        'help': 'asl_help.mp4',
        'sorry': 'asl_sorry.mp4',
        'welcome': 'asl_welcome.mp4',
        'goodbye': 'asl_goodbye.mp4',
        'bye': 'asl_goodbye.mp4',
        'morning': 'asl_morning.mp4',
        'night': 'asl_night.mp4',
        'eat': 'asl_eat.mp4',
        'drink': 'asl_drink.mp4',
        'water': 'asl_water.mp4',
        'food': 'asl_food.mp4',
        'love': 'asl_love.mp4',
        'like': 'asl_like.mp4',
        'want': 'asl_want.mp4',
        'need': 'asl_need.mp4',
        'go': 'asl_go.mp4',
        'come': 'asl_come.mp4',
        'stop': 'asl_stop.mp4',
        'wait': 'asl_wait.mp4',
        'time': 'asl_time.mp4',
        'money': 'asl_money.mp4',
        'work': 'asl_work.mp4',
        'home': 'asl_home.mp4',
        'family': 'asl_family.mp4',
        'friend': 'asl_friend.mp4',
        'happy': 'asl_happy.mp4',
        'sad': 'asl_sad.mp4',
        'angry': 'asl_angry.mp4',
        'beautiful': 'asl_beautiful.mp4',
        'ugly': 'asl_ugly.mp4',
        'big': 'asl_big.mp4',
        'small': 'asl_small.mp4',
        'hot': 'asl_hot.mp4',
        'cold': 'asl_cold.mp4'
    }
    
    # Save mapping to JSON file
    mapping_file = os.path.join(asl_videos_dir, 'asl_mapping.json')
    with open(mapping_file, 'w', encoding='utf-8') as f:
        json.dump(asl_video_mapping, f, indent=2)
    
    print(f"✅ Created ASL mapping file: {mapping_file}")
    return asl_video_mapping

def create_sample_video_list(asl_videos_dir, mapping):
    """Create a list of required video files"""
    
    required_files = list(set(mapping.values()))  # Remove duplicates
    required_files.sort()
    
    list_file = os.path.join(asl_videos_dir, 'required_videos.txt')
    with open(list_file, 'w', encoding='utf-8') as f:
        f.write("Required ASL Video Files\n")
        f.write("========================\n\n")
        f.write("Place these video files in the static/asl_videos/ directory:\n\n")
        
        for i, filename in enumerate(required_files, 1):
            f.write(f"{i:2d}. {filename}\n")
        
        f.write(f"\nTotal: {len(required_files)} video files needed\n")
        f.write("\nVideo Requirements:\n")
        f.write("- Format: MP4 (recommended)\n")
        f.write("- Resolution: 640x480 or 1280x720 (recommended)\n")
        f.write("- Duration: 2-5 seconds per word\n")
        f.write("- Quality: Clear ASL demonstration\n")
        f.write("- Background: Plain/neutral preferred\n")
    
    print(f"✅ Created required videos list: {list_file}")
    return required_files

def create_readme_file():
    """Create a comprehensive README for ASL setup"""
    
    readme_content = """# ASL Video Setup Guide

## Overview
This guide helps you set up American Sign Language (ASL) videos for the English sign language translator.

## Directory Structure
```
static/
├── asl_videos/              # Source ASL videos for individual words
│   ├── asl_hello.mp4
│   ├── asl_thank.mp4
│   ├── asl_you.mp4
│   └── ...
├── english_sign_videos/     # Generated concatenated videos
└── gif/                     # Arabic GIFs (existing)
```

## Setup Steps

### 1. Run Setup Script
```bash
python setup_asl_videos.py
```

### 2. Add ASL Videos
- Check `static/asl_videos/required_videos.txt` for the complete list
- Obtain or create ASL videos for each word
- Place them in the `static/asl_videos/` directory

### 3. Video Sources
You can obtain ASL videos from:
- **ASL Dictionary websites** (with permission)
- **Create your own** with ASL speakers
- **AI-generated ASL videos** (if available)
- **Stock video libraries** with ASL content

### 4. Video Requirements
- **Format**: MP4 (H.264 codec recommended)
- **Resolution**: 640x480 minimum, 1280x720 preferred
- **Duration**: 2-5 seconds per word
- **Quality**: Clear, well-lit ASL demonstration
- **Background**: Plain/neutral background preferred
- **Consistency**: Similar lighting and framing across videos

### 5. Testing
1. Add some basic ASL videos (hello, thank, you, etc.)
2. Access `/ENtest-video` in your application
3. Type "hello thank you" and test video generation
4. Check the console logs for detailed feedback

## Video Generation Process

### Text Input: "Hello thank you"
1. **Text Processing**: Split into words: ['hello', 'thank', 'you']
2. **Video Lookup**: Find ASL videos: `asl_hello.mp4`, `asl_thank.mp4`, `asl_you.mp4`
3. **Concatenation**: Combine videos using OpenCV
4. **Output**: Generate `english_sign_TIMESTAMP.mp4`

## Troubleshooting

### Common Issues
1. **"No ASL videos found"**: Check if video files exist in `static/asl_videos/`
2. **"Video concatenation failed"**: Ensure videos have compatible formats
3. **"ImportError: video_utils"**: This is expected - the system falls back to custom implementation

### Debug Mode
Enable detailed logging by checking the Flask console output:
```
📝 Processing English text: 'hello'
✅ Found ASL video for 'hello': asl_hello.mp4
✅ Generated English sign video: static/english_sign_videos/english_sign_1234567890.mp4
```

## Integration with video_utils

If you have an existing `video_utils.py` with `create_sentence_video()` function:
1. The system will try to use it first
2. If successful, videos will be copied to the English videos directory
3. If failed/unavailable, it falls back to the custom ASL video system

## Extending the System

### Adding New Words
1. Add the word mapping to `asl_video_mapping` in `app.py`
2. Add the corresponding video file to `static/asl_videos/`
3. Update the mapping JSON file if needed

### Custom Video Processing
- Replace `concatenate_videos_cv2()` with moviepy for better video quality
- Add transition effects between words
- Implement text overlays or captions

## Performance Considerations
- **Video Size**: Keep individual ASL videos under 5MB each
- **Caching**: Consider implementing video caching for repeated phrases
- **Compression**: Use appropriate video compression for web delivery
- **Load Time**: Optimize video loading for better user experience

## Legal Considerations
- Ensure you have proper rights/permissions for ASL videos
- Consider creating original content or using royalty-free sources
- Credit ASL performers if required
- Follow accessibility guidelines for deaf/hard-of-hearing users
"""
    
    with open('ASL_SETUP_README.md', 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print(f"✅ Created comprehensive README: ASL_SETUP_README.md")

def main():
    """Main setup function"""
    print("🚀 Setting up ASL Video Structure for English Sign Language")
    print("=" * 60)
    
    # Create directories
    asl_dir, english_dir = create_asl_directory_structure()
    
    # Create mapping file
    mapping = create_asl_video_mapping_file(asl_dir)
    
    # Create required files list
    required_files = create_sample_video_list(asl_dir, mapping)
    
    # Create comprehensive README
    create_readme_file()
    
    print("\n" + "=" * 60)
    print("✅ ASL Video Setup Complete!")
    print("=" * 60)
    
    print(f"\n📁 Directories created:")
    print(f"   - {asl_dir}")
    print(f"   - {english_dir}")
    
    print(f"\n📋 Next steps:")
    print(f"   1. Check: {os.path.join(asl_dir, 'required_videos.txt')}")
    print(f"   2. Add ASL video files to: {asl_dir}")
    print(f"   3. Read: ASL_SETUP_README.md for detailed instructions")
    print(f"   4. Test: Access /ENtest-video in your application")
    
    print(f"\n🎯 Priority videos to add first:")
    priority_words = ['hello', 'thank', 'you', 'please', 'yes', 'no', 'good', 'help']
    for word in priority_words:
        if word in mapping:
            print(f"   - {mapping[word]} (for word: '{word}')")
    
    print(f"\n📊 Total videos needed: {len(required_files)}")
    print("🎬 Start with the priority videos above for basic functionality!")

if __name__ == "__main__":
    main() 