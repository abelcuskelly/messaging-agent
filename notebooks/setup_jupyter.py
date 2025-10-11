#!/usr/bin/env python3
"""
Jupyter Notebook Setup Script for Qwen Messaging Agent

This script sets up the Jupyter environment for the messaging agent project.
"""

import os
import subprocess
import sys
from pathlib import Path

def install_requirements():
    """Install Jupyter requirements"""
    print("📦 Installing Jupyter requirements...")
    
    requirements_file = Path(__file__).parent / "requirements.txt"
    
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
        ], check=True)
        print("✅ Requirements installed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing requirements: {e}")
        return False
    
    return True

def setup_jupyter_kernel():
    """Set up Jupyter kernel for the project"""
    print("🔧 Setting up Jupyter kernel...")
    
    try:
        # Install ipykernel
        subprocess.run([
            sys.executable, "-m", "pip", "install", "ipykernel"
        ], check=True)
        
        # Add kernel
        subprocess.run([
            sys.executable, "-m", "ipykernel", "install", 
            "--user", "--name", "qwen-messaging-agent", 
            "--display-name", "Qwen Messaging Agent"
        ], check=True)
        
        print("✅ Jupyter kernel set up successfully!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error setting up kernel: {e}")
        return False
    
    return True

def create_env_template():
    """Create environment template file"""
    print("📝 Creating environment template...")
    
    env_template = """# Environment Variables for Jupyter Notebooks
# Copy this file to .env and fill in your values

# Google Cloud Configuration
PROJECT_ID=your-project-id
REGION=us-central1
ENDPOINT_ID=your-endpoint-id

# BigQuery Configuration
DATASET_ID=messaging_agent
TABLE_ID=conversations

# Storage Configuration
BUCKET_NAME=your-bucket-name

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# Authentication
API_KEY=your-api-key
JWT_SECRET_KEY=your-jwt-secret

# Monitoring
WANDB_PROJECT=qwen-messaging-agent
WANDB_API_KEY=your-wandb-key
"""
    
    env_file = Path(__file__).parent / ".env.template"
    with open(env_file, "w") as f:
        f.write(env_template)
    
    print(f"✅ Environment template created: {env_file}")

def main():
    """Main setup function"""
    print("🚀 Setting up Jupyter environment for Qwen Messaging Agent...")
    
    # Change to notebooks directory
    notebooks_dir = Path(__file__).parent
    os.chdir(notebooks_dir)
    
    # Install requirements
    if not install_requirements():
        print("❌ Failed to install requirements")
        return False
    
    # Set up kernel
    if not setup_jupyter_kernel():
        print("❌ Failed to set up kernel")
        return False
    
    # Create environment template
    create_env_template()
    
    print("\n🎉 Jupyter setup complete!")
    print("\nNext steps:")
    print("1. Copy .env.template to .env and fill in your values")
    print("2. Start Jupyter Lab: jupyter lab")
    print("3. Select the 'Qwen Messaging Agent' kernel")
    print("4. Open the notebooks in the templates/ directory")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
