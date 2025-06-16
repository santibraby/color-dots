#!/bin/bash

# Color Dots - GitHub Setup Helper

echo "🎨 Color Dots - GitHub Setup Helper"
echo "==================================="
echo ""

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed. Please install git first."
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "streamlit_app.py" ]; then
    echo "❌ Error: streamlit_app.py not found."
    echo "Please run this script from the color-dots directory."
    exit 1
fi

# Get GitHub username
read -p "Enter your GitHub username: " github_username

# Initialize git if needed
if [ ! -d ".git" ]; then
    echo "📁 Initializing git repository..."
    git init
fi

# Add all files
echo "📝 Adding files to git..."
git add .

# Create initial commit
echo "💾 Creating initial commit..."
git commit -m "Initial commit: Color Dots Streamlit app" 2>/dev/null || echo "Already committed!"

# Set main branch
git branch -M main

# Add remote
echo "🔗 Adding GitHub remote..."
git remote add origin "https://github.com/${github_username}/color-dots.git" 2>/dev/null || echo "Remote already exists!"

echo ""
echo "==================================="
echo "✅ Git setup complete!"
echo ""
echo "Next steps:"
echo "1. Create a new repository on GitHub:"
echo "   https://github.com/new"
echo "   - Name: color-dots"
echo "   - Keep it PUBLIC (required for free Streamlit hosting)"
echo "   - DON'T initialize with README"
echo ""
echo "2. Push your code:"
echo "   git push -u origin main"
echo ""
echo "3. Deploy on Streamlit Cloud:"
echo "   https://share.streamlit.io"
echo ""
echo "Happy coding! 🚀"