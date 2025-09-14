# English Sign Language Video Testing

This document explains how to use the new English version of the video testing feature.

## Overview

The English version (`test_video_clean_en.html`) is a modified version of the Arabic video testing page that supports:

1. **English UI**: All interface elements are in English with LTR text direction
2. **English Text-to-Sign Video**: Convert English text into sign language videos
3. **English Sign Language Recognition**: Real-time recognition of American Sign Language (ASL)
4. **WebRTC Video Calling**: Same video calling features as the Arabic version

## Key Differences from Arabic Version

### UI Changes
- Language switched from Arabic to English
- Text direction changed from RTL to LTR
- All labels, buttons, and messages are in English
- Home redirect goes to `/ENhome` instead of `/ARhome`

### Functionality Changes
- Uses English sign language vocabulary instead of Arabic
- Generates English sign language videos instead of Arabic GIFs
- Socket events use `english_` prefixes to distinguish from Arabic handlers

## Routes

- **Arabic Version**: `/test-video` → `test_video_clean.html`
- **English Version**: `/ENtest-video` → `test_video_clean_en.html`

Both routes use the same user validation (TEST_USER_1_UID and TEST_USER_2_UID) but separate rooms (`test_room_fixed` vs `test_room_fixed_en`).

## Socket Events

### English-Specific Events
- `english_text_to_sign_video`: Converts English text to sign language video
- `english_video_frame`: Processes video frames for English ASL recognition
- `english_sign_video_response`: Returns generated sign language video

### Shared Events
- `sign_language_translation`: Used for both languages (differentiated by language field)
- Standard WebRTC events: `offer`, `answer`, `ice_candidate`

## Backend Implementation

### Files Modified
- `app.py`: Added `/ENtest-video` route and English socket handlers
- `templates/test_video_clean_en.html`: New English version of the interface

### Key Functions
- `create_english_sign_video(text)`: Helper function for video generation (placeholder)
- `handle_english_text_to_sign_video()`: Socket handler for text-to-video requests
- `handle_english_video_frame()`: Socket handler for ASL recognition

## Integration Points

To fully implement the English sign language features, you need to:

### 1. Text-to-Video Generation
Replace the placeholder in `create_english_sign_video()` with actual video generation logic:

```python
def create_english_sign_video(text):
    # 1. Parse English text into words
    words = text.split()
    
    # 2. Find ASL video files for each word
    video_clips = []
    for word in words:
        video_path = find_asl_video_for_word(word)
        if video_path:
            video_clips.append(video_path)
    
    # 3. Concatenate videos
    final_video = concatenate_videos(video_clips)
    
    # 4. Save and return path
    return save_video(final_video)
```

### 2. ASL Recognition
Replace the placeholder recognition in `handle_english_video_frame()` with actual ASL model:

```python
# Load your ASL recognition model
asl_model = load_asl_model()

# Process frame
prediction = asl_model.predict(frame)
word = prediction.get_word()
confidence = prediction.get_confidence()
```

### 3. Video Storage
Create the directory structure:
```
static/
├── gif/                    # Arabic GIFs
├── english_sign_videos/    # English sign videos
```

## Testing

1. **Setup Test Users**: Use the same TEST_USER_1_UID and TEST_USER_2_UID as Arabic version
2. **Access English Version**: Go to `/ENtest-video` (requires English login `/ENlogin`)
3. **Test Features**:
   - Video calling (same as Arabic)
   - Type English text → generates sign video
   - Sign ASL → gets English text translation

## Language Detection

The system automatically detects which version is being used based on:
- Route accessed (`/test-video` vs `/ENtest-video`)
- Socket event prefixes (`english_` events)
- Session language preference

## Future Enhancements

1. **Automatic Language Detection**: Detect user's preferred language and route accordingly
2. **Bilingual Support**: Allow switching between Arabic and English in the same session
3. **Advanced ASL Models**: Integrate with state-of-the-art ASL recognition models
4. **Video Quality**: Improve sign language video generation quality and smoothness

## Dependencies

Same as the Arabic version, plus any additional dependencies for:
- English ASL recognition models
- English sign language video generation
- Video processing libraries (if different from Arabic implementation) 