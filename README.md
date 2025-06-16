# Color Dots 🎨

A beautiful Streamlit app that searches Google Images and displays results in a 10×10 circular grid.

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io)

## Features

- 🔍 Google image search using Selenium
- ⭕ 10×10 grid of circular thumbnails
- 🎨 Clean, minimal interface with Karla font
- 💫 Smooth hover animations
- 📱 Responsive design

## Demo

Try it live: [color-dots.streamlit.app](https://share.streamlit.io) *(Update with your URL after deployment)*

## Local Installation

1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/color-dots.git
cd color-dots
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the app:
```bash
streamlit run streamlit_app.py
```

## Deployment on Streamlit Cloud

1. Push this repository to GitHub (must be public)
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub account
4. Deploy with these settings:
   - Repository: `YOUR_USERNAME/color-dots`
   - Branch: `main`
   - Main file: `streamlit_app.py`

## Project Structure

```
color-dots/
├── streamlit_app.py      # Main application
├── requirements.txt      # Python dependencies
├── packages.txt         # System dependencies (Chrome)
├── .streamlit/
│   └── config.toml      # Streamlit configuration
├── README.md            # This file
├── LICENSE              # MIT license
└── .gitignore           # Git ignore file
```

## Important Notes

- `packages.txt` is required for Streamlit Cloud to install Chrome
- Repository must be public for free hosting
- First deployment may take 5-10 minutes

## Usage

1. Enter a search term in the sidebar
2. Click "Search"
3. View your results in the circular grid
4. Hover over images to see them enlarge

## Technologies

- **Streamlit** - Web app framework
- **Selenium** - Web automation for Google Images
- **Pillow** - Image processing
- **Chrome/Chromium** - Browser engine

## Troubleshooting

### Chrome Driver Issues
- Ensure `packages.txt` exists with chromium packages
- Check deployment logs on Streamlit Cloud

### No Images Found
- Try different search terms
- Check internet connectivity
- Google may have updated their HTML structure

## License

MIT License - see LICENSE file for details

## Contributing

Pull requests are welcome! For major changes, please open an issue first.

## Author

Your Name - [@yourusername](https://github.com/yourusername)

---

Made with ❤️ using Streamlit