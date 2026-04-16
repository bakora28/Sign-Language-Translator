# ASL Video Setup Guide

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
