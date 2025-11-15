#!/usr/bin/env python
"""
Setup script for Online Interview Platform
Run this script to set up the application for the first time
"""

import os
import sys
import subprocess
import django
from django.core.management import execute_from_command_line

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False

def setup_environment():
    """Set up the environment"""
    print("🚀 Setting up Online Meeting Platform...")
    
    # Check if virtual environment exists
    if not os.path.exists('venv'):
        print("📦 Creating virtual environment...")
        if not run_command('python -m venv venv', 'Creating virtual environment'):
            return False
    
    # Activate virtual environment and install dependencies
    if os.name == 'nt':  # Windows
        activate_cmd = 'venv\\Scripts\\activate'
        pip_cmd = 'venv\\Scripts\\pip'
    else:  # Unix/Linux/MacOS
        activate_cmd = 'source venv/bin/activate'
        pip_cmd = 'venv/bin/pip'
    
    # Install dependencies
    if not run_command(f'{pip_cmd} install -r requirements.txt', 'Installing dependencies'):
        return False
    
    return True

def setup_database():
    """Set up the database"""
    print("🗄️ Setting up database...")
    
    # Set Django settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'onlinemeet.settings')
    django.setup()
    
    # Run migrations
    if not run_command('python manage.py migrate', 'Running database migrations'):
        return False
    
    # Create superuser
    print("👤 Creating superuser...")
    try:
        from accounts.models import User
        if not User.objects.filter(username='admin').exists():
            user = User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123',
                first_name='Admin',
                last_name='User'
            )
            print("✅ Superuser created: admin/admin123")
        else:
            print("ℹ️ Superuser already exists")
    except Exception as e:
        print(f"❌ Error creating superuser: {e}")
        return False
    
    return True

def collect_static():
    """Collect static files"""
    print("📁 Collecting static files...")
    return run_command('python manage.py collectstatic --noinput', 'Collecting static files')

def main():
    """Main setup function"""
    print("=" * 50)
    print("🎥 Online Meeting Platform Setup")
    print("=" * 50)
    
    # Setup environment
    if not setup_environment():
        print("❌ Environment setup failed")
        sys.exit(1)
    
    # Setup database
    if not setup_database():
        print("❌ Database setup failed")
        sys.exit(1)
    
    # Collect static files
    if not collect_static():
        print("❌ Static files collection failed")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("🎉 Setup completed successfully!")
    print("=" * 50)
    print("\n📋 Next steps:")
    print("1. Start Redis server (required for WebSocket functionality)")
    print("2. Run: python manage.py runserver")
    print("3. Open: http://127.0.0.1:8000")
    print("4. Login with: admin / admin123")
    print("\n🔧 For production deployment:")
    print("- Set DEBUG=False in settings.py")
    print("- Configure proper database (PostgreSQL/MySQL)")
    print("- Set up Redis for production")
    print("- Configure HTTPS for video calls")
    print("\n📚 For more information, see README.md")

if __name__ == '__main__':
    main()



