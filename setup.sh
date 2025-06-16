#!/bin/bash

# Color Dots - Setup Script

echo "🎨 Color Dots Setup"
echo "=================="
echo ""

# Create .streamlit directory if it doesn't exist
if [ ! -d ".streamlit" ]; then
    echo "Creating .streamlit directory..."
    mkdir .streamlit
fi

# Check if all files exist
echo "Checking files..."
files=("streamlit_app.py" "requirements.txt" "packages.txt" "README.md" "LICENSE" ".gitignore" ".streamlit/config.toml")

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file is missing!"
    fi
done

echo ""
echo "=================="
echo "Next steps:"
echo ""
echo "1. Initialize Git repository:"
echo "   git init"
echo "   git add ."
echo "   git commit -m 'Initial commit'"
echo ""
echo "2. Create GitHub repository:"
echo "   - Go to https://github.com/new"
echo "   - Name: color-dots"
echo "   - Make it PUBLIC"
echo "   - Don't initialize with README"
echo ""
echo "3. Push to GitHub:"
echo "   git remote add origin https://github.com/YOUR_USERNAME/color-dots.git"
echo "   git branch -M main"
echo "   git push -u origin main"
echo ""
echo "4. Deploy on Streamlit Cloud:"
echo "   - Go to https://share.streamlit.io"
echo "   - Connect GitHub"
echo "   - Deploy your app!"
echo ""
echo "Happy coding! 🚀"