import streamlit as st
import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
import base64
from PIL import Image
import io
import subprocess

# Page configuration
st.set_page_config(
    page_title="Color Dots",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Karla:wght@400;700&display=swap');

    /* Global styles */
    .stApp {
        background-color: #ffffff;
    }

    * {
        font-family: 'Karla', sans-serif !important;
    }

    /* Dark grey text */
    h1, h2, h3, p, div {
        color: #2a2a2a !important;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #f8f8f8;
    }

    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Button styling */
    .stButton > button {
        background-color: #2a2a2a;
        color: white !important;
        border: none;
        padding: 0.5rem 2rem;
        font-weight: 600;
        border-radius: 8px;
        transition: all 0.3s ease;
        width: 100%;
    }

    .stButton > button:hover {
        background-color: #1a1a1a;
        transform: translateY(-2px);
    }

    /* Input styling */
    .stTextInput > div > div > input {
        border: 2px solid #e0e0e0;
        border-radius: 8px;
        padding: 0.5rem;
    }

    /* Image grid */
    .image-grid {
        display: grid;
        grid-template-columns: repeat(10, 1fr);
        gap: 12px;
        padding: 20px;
        max-width: 1000px;
        margin: 0 auto;
    }

    /* Circle images */
    .circle-image {
        position: relative;
        width: 100%;
        padding-bottom: 100%;
        overflow: hidden;
        border-radius: 50%;
        background-color: #f0f0f0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        transition: transform 0.3s ease;
    }

    .circle-image:hover {
        transform: scale(1.05);
        box-shadow: 0 4px 16px rgba(0,0,0,0.2);
    }

    .circle-image img {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        object-fit: cover;
    }

    /* Loading text */
    .status-text {
        text-align: center;
        color: #666;
        padding: 20px;
    }
</style>
""", unsafe_allow_html=True)


class ColorDotsApp:
    def __init__(self):
        self.setup_session_state()

    def setup_session_state(self):
        """Initialize session state variables"""
        if 'images' not in st.session_state:
            st.session_state.images = []
        if 'last_search' not in st.session_state:
            st.session_state.last_search = ""

    def create_driver(self):
        """Create Chrome driver with appropriate settings"""
        options = webdriver.ChromeOptions()
        options.add_argument('--headless=new')  # Use new headless mode
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-features=VizDisplayCompositor')
        options.add_argument('--disable-software-rasterizer')

        # Additional stability options
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        # Memory optimization
        options.add_argument('--memory-pressure-off')
        options.add_argument('--max_old_space_size=4096')

        try:
            # Check for Chrome/Chromium binaries
            chrome_paths = [
                '/usr/bin/chromium',
                '/usr/bin/chromium-browser',
                '/usr/bin/google-chrome',
                '/usr/local/bin/chromium',
                '/usr/local/bin/google-chrome'
            ]

            chrome_binary = None
            for path in chrome_paths:
                if os.path.exists(path):
                    chrome_binary = path
                    break

            if chrome_binary:
                options.binary_location = chrome_binary

            # Check for ChromeDriver
            chromedriver_paths = [
                '/usr/bin/chromedriver',
                '/usr/local/bin/chromedriver',
                '/opt/chromedriver/chromedriver'
            ]

            chromedriver_path = None
            for path in chromedriver_paths:
                if os.path.exists(path):
                    chromedriver_path = path
                    break

            # Try to initialize driver
            if chromedriver_path:
                service = Service(executable_path=chromedriver_path)
                driver = webdriver.Chrome(service=service, options=options)
            else:
                # Let Selenium find ChromeDriver in PATH
                driver = webdriver.Chrome(options=options)

            return driver

        except Exception as e:
            st.error(f"Failed to initialize Chrome driver: {str(e)}")

            # Debug information
            st.info("Debug Information:")

            # Check Chrome installation
            chrome_check = subprocess.run(['which', 'chromium'], capture_output=True, text=True)
            st.code(f"Chromium location: {chrome_check.stdout.strip() or 'Not found'}")

            # Check ChromeDriver installation
            driver_check = subprocess.run(['which', 'chromedriver'], capture_output=True, text=True)
            st.code(f"ChromeDriver location: {driver_check.stdout.strip() or 'Not found'}")

            # Check versions
            try:
                chrome_version = subprocess.run(['chromium', '--version'], capture_output=True, text=True)
                st.code(f"Chromium version: {chrome_version.stdout.strip()}")
            except:
                st.code("Could not get Chromium version")

            try:
                driver_version = subprocess.run(['chromedriver', '--version'], capture_output=True, text=True)
                st.code(f"ChromeDriver version: {driver_version.stdout.strip()}")
            except:
                st.code("Could not get ChromeDriver version")

            raise

    def search_google_images(self, query, num_images=100):
        """Perform Google image search and return thumbnail URLs"""
        driver = None
        thumbnails = []

        try:
            driver = self.create_driver()

            # Navigate to Google Images
            driver.get("https://www.google.com/imghp")

            # Search for query
            search_box = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "q"))
            )
            search_box.send_keys(query)
            search_box.send_keys(Keys.RETURN)

            # Wait for results
            time.sleep(2)

            # Collect thumbnails
            collected = 0
            last_height = driver.execute_script("return document.body.scrollHeight")

            while collected < num_images:
                # Find all thumbnail images
                images = driver.find_elements(By.CSS_SELECTOR, "img.YQ4gaf")

                for img in images[collected:]:
                    if collected >= num_images:
                        break

                    try:
                        src = img.get_attribute("src")
                        if src and (src.startswith("http") or src.startswith("data:")):
                            thumbnails.append(src)
                            collected += 1
                    except:
                        continue

                # Scroll down to load more
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)

                # Check if reached bottom
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height

        finally:
            if driver:
                driver.quit()

        return thumbnails[:num_images]

    def url_to_image(self, url):
        """Convert URL or base64 to PIL Image"""
        try:
            if url.startswith("data:"):
                # Handle base64
                header, data = url.split(",", 1)
                img_data = base64.b64decode(data)
                return Image.open(io.BytesIO(img_data))
            else:
                # Handle URL
                response = requests.get(url, timeout=5)
                return Image.open(io.BytesIO(response.content))
        except:
            # Return placeholder
            return Image.new('RGB', (100, 100), color='#e0e0e0')

    def create_image_grid(self, images):
        """Create HTML grid of circular images"""
        html = '<div class="image-grid">'

        # Add images
        for i, img in enumerate(images[:100]):
            # Convert to base64 for embedding
            buffered = io.BytesIO()

            # Convert image to RGB if it's in palette mode or has transparency
            if img.mode in ('P', 'RGBA', 'LA'):
                # Convert to RGB
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                # Paste the image on white background
                if img.mode == 'RGBA' or 'transparency' in img.info:
                    rgb_img.paste(img, mask=img.split()[-1])  # Use alpha channel as mask
                else:
                    rgb_img.paste(img)
                img = rgb_img
            elif img.mode != 'RGB':
                # Convert any other mode to RGB
                img = img.convert('RGB')

            # Now save as JPEG
            img.save(buffered, format="JPEG", quality=85)
            img_str = base64.b64encode(buffered.getvalue()).decode()

            html += f'''
            <div class="circle-image">
                <img src="data:image/jpeg;base64,{img_str}" alt="Result {i + 1}">
            </div>
            '''

        # Fill empty spots
        for i in range(len(images), 100):
            html += '<div class="circle-image"></div>'

        html += '</div>'
        return html

    def run(self):
        """Main app logic"""
        # Sidebar
        with st.sidebar:
            st.title("🎨 Color Dots")
            st.markdown("---")

            # Search input
            search_query = st.text_input(
                "Search for images",
                placeholder="Enter a word or phrase...",
                help="This will search Google Images"
            )

            # Search button
            search_clicked = st.button("Search", type="primary")

            # Info
            st.markdown("---")
            st.markdown("""
            ### How it works
            1. Enter a search term
            2. Click Search
            3. View results in a 10×10 grid

            Each image is displayed as a circle with hover effects.
            """)

            # Stats
            if st.session_state.images:
                st.markdown("---")
                st.metric("Images found", len(st.session_state.images))
                st.caption(f"Last search: {st.session_state.last_search}")

        # Main area
        if search_clicked and search_query:
            st.session_state.images = []
            st.session_state.last_search = search_query

            # Progress indicators
            progress = st.progress(0)
            status = st.empty()

            try:
                # Search images
                status.markdown('<p class="status-text">🔍 Searching Google Images...</p>',
                                unsafe_allow_html=True)

                thumbnails = self.search_google_images(search_query)

                if thumbnails:
                    # Process images
                    status.markdown('<p class="status-text">🎨 Processing images...</p>',
                                    unsafe_allow_html=True)

                    images = []
                    for i, url in enumerate(thumbnails):
                        img = self.url_to_image(url)
                        images.append(img)
                        progress.progress((i + 1) / len(thumbnails))

                    st.session_state.images = images

                    # Clear progress
                    progress.empty()
                    status.empty()

                    st.success(f"✅ Found {len(images)} images for '{search_query}'")
                else:
                    st.warning("No images found. Try a different search term.")
                    progress.empty()
                    status.empty()

            except Exception as e:
                st.error(f"Error: {str(e)}")
                progress.empty()
                status.empty()

        # Display results
        if st.session_state.images:
            st.markdown("---")
            grid_html = self.create_image_grid(st.session_state.images)
            st.markdown(grid_html, unsafe_allow_html=True)
        else:
            # Welcome message
            st.markdown("""
            <div style="text-align: center; padding: 60px 20px;">
                <h1 style="font-size: 48px; margin-bottom: 20px;">Welcome to Color Dots</h1>
                <p style="font-size: 18px; color: #666;">
                    Search for any topic to create a beautiful circular image grid
                </p>
            </div>
            """, unsafe_allow_html=True)


# Run the app
if __name__ == "__main__":
    app = ColorDotsApp()
    app.run()