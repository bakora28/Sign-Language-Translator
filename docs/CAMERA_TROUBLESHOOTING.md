# Camera Access Troubleshooting Guide

## Problem: "لم يتم العثور على كاميرا - NotFoundError: Requested device not found"

This error occurs when the browser cannot find any camera devices on your system.

## Quick Solutions

### 1. **Check Physical Camera Connection**
- **Desktop PC**: Ensure USB webcam is properly connected
- **Laptop**: Check if built-in camera is enabled
- **Look for camera indicator lights** when accessing the site

### 2. **Windows System Settings**
1. Go to **Settings** → **Privacy** → **Camera**
2. Enable "Allow apps to access your camera"
3. Enable "Allow desktop apps to access your camera"
4. Check individual app permissions

### 3. **Device Manager Check**
1. Right-click "This PC" → **Properties** → **Device Manager**
2. Look for **"Cameras"** or **"Imaging devices"**
3. If you see warning icons:
   - Right-click the camera device
   - Select **"Update driver"** or **"Uninstall device"**
   - Restart computer to reinstall drivers

### 4. **Browser Settings**
1. Click the **lock icon** in the address bar
2. Set Camera to **"Allow"**
3. Refresh the page
4. For Chrome: Go to **Settings** → **Privacy and security** → **Site settings** → **Camera**

### 5. **Use HTTPS**
Camera access requires HTTPS in most browsers. Run the server with:
```bash
python app.py --https
```
Or use the `run_server.bat` file and choose option 2.

## Advanced Troubleshooting

### Test Camera in Other Applications
1. Open **Camera app** (Windows 10/11)
2. Try **Skype**, **Zoom**, or **Teams**
3. If camera doesn't work in other apps, it's a system/hardware issue

### Check Camera Drivers
1. Visit your laptop manufacturer's website
2. Download latest camera drivers
3. For USB webcams, try different USB ports

### Registry Fix (Windows - Advanced Users)
If camera was working before but suddenly stopped:
1. Press `Win + R`, type `regedit`
2. Navigate to: `HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows Media Foundation\Platform`
3. Create new DWORD: `EnableFrameServerMode` = `0`
4. Restart computer

### Multiple Applications Using Camera
- Close **Skype**, **Teams**, **Discord**, or other video apps
- Check **Task Manager** for apps using camera
- Restart browser

## Server Options

### HTTP Mode (Limited)
```bash
python app.py
```
- Works on localhost only
- Limited camera access

### HTTPS Mode (Recommended)
```bash
python app.py --https
```
- Full camera access
- Auto-creates SSL certificate
- Accept security warning in browser

### Custom Settings
```bash
python app.py --https --host 0.0.0.0 --port 8080
```

## Browser Compatibility

| Browser | Camera Support | Notes |
|---------|----------------|-------|
| Chrome | ✅ Excellent | Best compatibility |
| Firefox | ✅ Good | May need permissions reset |
| Edge | ✅ Good | Built-in Windows integration |
| Safari | ✅ Good | macOS only |
| Opera | ✅ Good | Chrome-based |

## Fallback Modes

The application automatically provides fallback options:

1. **Audio Only Mode**: If camera fails but microphone works
2. **Text Only Mode**: If both camera and microphone fail
3. **Manual Testing**: Built-in camera diagnostics

## Common Error Messages

| Error | Meaning | Solution |
|-------|---------|----------|
| `NotFoundError` | No camera found | Check connections and drivers |
| `NotAllowedError` | Permission denied | Allow camera access in browser |
| `NotReadableError` | Camera in use | Close other applications |
| `NotSupportedError` | Browser issue | Update browser or use Chrome |
| `OverconstrainedError` | Settings issue | Try basic camera settings |

## Getting Help

If problems persist:

1. **Use the built-in camera test** in the error dialog
2. **Check browser console** (F12) for detailed errors
3. **Try different browsers**
4. **Test with a different camera** (if available)

## Technical Details

The application uses:
- **WebRTC** for video streaming
- **MediaDevices API** for camera access
- **getUserMedia()** for permission requests

### System Requirements
- **Modern browser** (Chrome 60+, Firefox 60+, Safari 12+)
- **HTTPS connection** (for security)
- **Camera drivers** properly installed
- **System permissions** granted

---

**Note**: This is a comprehensive guide. Most issues are resolved by checking camera permissions and using HTTPS mode. 