# 🚀 Deployment Guide for Streamlit Cloud

This guide will help you deploy the Color Dots app to Streamlit Cloud for free hosting.

## Prerequisites

- GitHub account
- Streamlit Cloud account (free)
- Your code pushed to a public GitHub repository

## Step-by-Step Deployment

### 1. Prepare Your Repository

Ensure your GitHub repository has these files:
```
color-dots/
├── streamlit_app.py      # Main application
├── requirements.txt      # Python dependencies
├── packages.txt         # System dependencies (Chrome)
├── .streamlit/
│   └── config.toml      # Streamlit configuration
├── README.md
├── LICENSE
└── .gitignore
```

### 2. Sign Up for Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click "Sign up with GitHub"
3. Authorize Streamlit to access your GitHub account

### 3. Deploy Your App

1. Click "New app" on your Streamlit Cloud dashboard
2. Fill in the deployment form:
   - **Repository:** `YOUR_GITHUB_USERNAME/color-dots`
   - **Branch:** `main`
   - **Main file path:** `streamlit_app.py`
3. Click "Deploy!"

### 4. Monitor Deployment

- Watch the deployment logs in real-time
- First deployment may take 5-10 minutes
- Subsequent updates are faster

### 5. Your App URL

Once deployed, your app will be available at:
```
https://YOUR_APP_NAME.streamlit.app
```

## Important Notes

### System Dependencies

The `packages.txt` file is **crucial** for Streamlit Cloud. It installs:
- `chromium` - The Chrome browser
- `chromium-driver` - WebDriver for Selenium

Without this file, Selenium won't work on Streamlit Cloud!

### Environment Detection

The app automatically detects if it's running on Streamlit Cloud:
```python
if 'STREAMLIT_SHARING_MODE' in os.environ:
    # Streamlit Cloud settings
else:
    # Local development settings
```

### Resource Limits

Streamlit Cloud free tier has limits:
- 1 GB of RAM
- 1 CPU
- 800 MB of storage

The app is optimized to work within these limits.

## Troubleshooting

### "ChromeDriver not found" Error
- Ensure `packages.txt` exists with chromium packages
- Check that Chrome binary location is set correctly

### Slow Performance
- First search may be slower due to Chrome startup
- Consider reducing max images from 100 to 50

### App Won't Deploy
- Check logs for specific errors
- Ensure repository is public
- Verify all required files are present

## Updating Your App

To update your deployed app:
1. Make changes locally
2. Commit and push to GitHub
3. Streamlit Cloud automatically redeploys

```bash
git add .
git commit -m "Update: description of changes"
git push origin main
```

## Advanced Settings

In Streamlit Cloud dashboard, you can:
- Set custom subdomain
- Configure secrets (not needed for this app)
- View analytics
- Manage app settings

## Local Testing

Always test locally before deploying:
```bash
streamlit run streamlit_app.py
```

## Support

- [Streamlit Documentation](https://docs.streamlit.io)
- [Streamlit Community Forum](https://discuss.streamlit.io)
- [GitHub Issues](https://github.com/YOUR_USERNAME/color-dots/issues)