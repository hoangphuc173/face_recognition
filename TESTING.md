# Face Recognition System - Testing Guide

## Quick Tests

### 1. Test Database Manager
```powershell
python manage_database.py
```

### 2. Test GUI Application
```powershell
python gui_app.py
```

### 3. Test Launcher
```powershell
python launcher.py
```

## Manual Testing Checklist

### ✅ Enrollment Tests
- [ ] Enroll from image file
- [ ] Enroll from video file
- [ ] Enroll from webcam (photo)
- [ ] Enroll from webcam (video)
- [ ] Duplicate detection works
- [ ] 3-option dialog appears correctly
- [ ] All 5 personal info fields save correctly

### ✅ Recognition Tests
- [ ] Recognize from image file
- [ ] Recognize from video file
- [ ] Recognize from webcam
- [ ] Display shows all 5 info lines
- [ ] Emoji display works correctly
- [ ] Unknown faces show "Unknown"

### ✅ Management Tests
- [ ] List shows all people
- [ ] Auto-refresh works (2s interval)
- [ ] View images opens folder
- [ ] Edit person info works
- [ ] Delete person works
- [ ] Info displays correctly

### ✅ Video Recording Tests
- [ ] Enrollment video saves all frames
- [ ] Recognition video saves all frames
- [ ] FPS = 20 for smooth playback
- [ ] Video codec MP4V works
- [ ] temp/ folder auto-deletes

### ✅ Database Tests
- [ ] Auto-numbering works (name, name_1, name_2)
- [ ] info.json saves correctly
- [ ] embeddings.npy saves correctly
- [ ] Folder structure is correct
- [ ] Update person info works

## Common Issues & Solutions

### Issue: Webcam not opening
**Solution**: Close other apps using webcam (Zoom, Teams, etc.)

### Issue: Face not detected
**Solution**: Ensure good lighting, face visible, not too far

### Issue: Duplicate not detected
**Solution**: Threshold too high, try lowering to 0.5

### Issue: Video not saving
**Solution**: Check temp/ folder permissions

### Issue: Unicode/emoji not showing
**Solution**: Should work with PIL, check font installation

## Performance Tests

### Test with different image sizes:
- Small (640x480)
- Medium (1280x720)
- Large (1920x1080)

### Test with multiple faces:
- 1 person
- 2-3 people
- 5+ people

### Test video lengths:
- Short (5-10 seconds)
- Medium (30-60 seconds)
- Long (2-5 minutes)

## Debug Mode

Run with Python debugger in VS Code:
1. Press F5
2. Select "Python: GUI App"
3. Set breakpoints as needed

## Log Files

Check for errors in:
- Terminal output
- VS Code Debug Console

## Database Verification

```powershell
# Check database structure
dir face_database

# View person info
python -c "import json; print(json.load(open('face_database/person_name/info.json')))"

# Check embeddings
python -c "import numpy as np; print(np.load('face_database/person_name/embeddings.npy').shape)"
```

## Clean Test Environment

```powershell
# Backup current database
Copy-Item face_database face_database_backup -Recurse

# Delete test data
Remove-Item -Recurse face_database/*
Remove-Item -Recurse faces/*
Remove-Item -Recurse recognized/*
Remove-Item -Recurse temp/*
```

## Automated Tests (Future)

TODO: Add unit tests for:
- [ ] Database operations
- [ ] Face enrollment
- [ ] Face recognition
- [ ] Video processing
- [ ] GUI functions
