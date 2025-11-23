from PIL import Image
import os

src = r"C:/Users/ADMIN/.gemini/antigravity/brain/0b7cfa41-4420-42c7-9b97-c90c55377030/app_icon_1763732075555.png"
dst = r"c:\Users\ADMIN\Downloads\facerecog\frontend\desktop\src-tauri\icons\icon.ico"

try:
    img = Image.open(src)
    img.save(dst, format='ICO', sizes=[(256, 256)])
    print(f"Successfully converted {src} to {dst}")
except Exception as e:
    print(f"Error converting icon: {e}")
