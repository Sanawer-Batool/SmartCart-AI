"""
Simple script to create .env file with correct format
"""
import os

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(script_dir, '.env')

# Content for .env file
env_content = """GOOGLE_API_KEY=YOUR_KEY
HOST=0.0.0.0
PORT=8000
DEBUG=True
HEADLESS=True
BROWSER_TIMEOUT=30000
"""

# Write the file with UTF-8 encoding, no BOM
with open(env_path, 'w', encoding='utf-8', newline='\n') as f:
    f.write(env_content.strip() + '\n')

print(f"✅ Created .env file at: {env_path}")
print(f"\n📄 Contents:")
print("-" * 50)
with open(env_path, 'r', encoding='utf-8') as f:
    print(f.read())
print("-" * 50)
print(f"\n✅ Done! Now restart the server with: python app.py")

