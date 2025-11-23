"""
Setup script for SmartCart AI backend.
Run this script to set up the environment and install dependencies.
"""
import subprocess
import sys
import os


def run_command(cmd, description):
    """Run a command and print status"""
    print(f"\n{'='*60}")
    print(f"📦 {description}")
    print(f"{'='*60}\n")
    
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"\n❌ Failed: {description}")
        return False
    print(f"\n✅ Success: {description}")
    return True


def main():
    print("""
    ╔═══════════════════════════════════════════════════════╗
    ║         SmartCart AI - Backend Setup Script          ║
    ║                                                       ║
    ║  This will install all required dependencies          ║
    ╚═══════════════════════════════════════════════════════╝
    """)
    
    # Check Python version
    if sys.version_info < (3, 10):
        print("❌ Python 3.10 or higher is required")
        print(f"   Current version: {sys.version}")
        sys.exit(1)
    
    print(f"✅ Python version: {sys.version.split()[0]}")
    
    # Install requirements
    if not run_command(
        f"{sys.executable} -m pip install -r requirements.txt",
        "Installing Python dependencies"
    ):
        sys.exit(1)
    
    # Install Playwright browsers
    if not run_command(
        f"{sys.executable} -m playwright install chromium",
        "Installing Playwright Chromium browser"
    ):
        sys.exit(1)
    
    # Install Playwright system dependencies (Linux only)
    if sys.platform.startswith('linux'):
        run_command(
            f"{sys.executable} -m playwright install-deps",
            "Installing Playwright system dependencies"
        )
    
    # Check for .env file
    if not os.path.exists('.env'):
        print("\n⚠️  Warning: .env file not found")
        print("   Please create .env file with your GOOGLE_API_KEY")
        print("   You can copy .env.example and fill in your key")
    else:
        print("\n✅ .env file found")
    
    print("""
    ╔═══════════════════════════════════════════════════════╗
    ║                   Setup Complete! 🎉                  ║
    ╚═══════════════════════════════════════════════════════╝
    
    Next steps:
    1. Make sure your .env file has GOOGLE_API_KEY set
    2. Run the server with: python app.py
       Or: uvicorn app:app --reload
    
    3. Access the API at: http://localhost:8000
       Swagger docs: http://localhost:8000/docs
    """)


if __name__ == "__main__":
    main()

