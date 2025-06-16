#!/usr/bin/env python3
"""
Color Dots Streamlit App - Google Image Search with Circular Grid Display
"""

import os
import time
import requests
import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import base64
from PIL import Image
import io
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Page config
st.set_page_config(
    page_title="Color Dots",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Karla:wght@400;700&display=swap');
    
    /* Global styles */
    .stApp {
        background-color: white;
    }
    
    * {
        font-family: 'Karla', sans-serif !important;
        color: #2a2a2a !important;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #f8f8f8;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Title styling */
    h1 {
        color: #1a1a1a !important;
        font-weight: 700 !important;
        letter-spacing: -0.5px;
    }
    
    /* Button styling */
    .stButton > button {
        background-color: #2a2a2a;
        color: white !important;
        border: none;
        padding: 0.5rem 2rem;
        font-weight: 600;
        border-radius: 8px;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background-color: #1a1a1a;
        transform: translateY(-2px);
    }
    
    /* Input field styling */
    .stTextInput > div > div > input {
        border: 2px solid #e0e0e0;
        border-radius: 8px;
        padding: 0.5rem;
        font-size: 16px;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #2a2a2a;
        box-shadow: 0 0 0 1px #2a2a2a;
    }
    
    /* Progress bar */
    .stProgress > div > div > div > div {
        background-color: #2a2a2a;
    }
    
    /* Image grid container */
    .image-grid {
        display: grid;
        grid-template-columns: repeat(10, 1fr);
        gap: 12px;
        padding: 20px;
        max-width: 1200px;
        margin: 0 auto;
    }
    
    /* Circular image styling */
    .image-container {
        position: relative;
        width: 100%;
        padding-bottom: 100%;
        overflow: hidden;
        border-radius: 50%;
        background-color: #f0f0f0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .image-container:hover {
        transform: scale(1.05);
        box-shadow: 0 4px 16px rgba(0,0,0,0.15);
    }
    
    .image-container img {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 100%;
        height: 100%;
        object-fit: cover;
    }
    
    /* Loading animation */
    .loading-text {
        color: #666 !important;
        font-size: 14px;
        text-align: center;
        padding: 20px;
    }
</style>
""", unsafe_allow_html=True)

class ColorDotsStreamlit:
    def __init__(self):
        self.thumbnails = []
        
    def setup_driver(self):
        """Setup Chrome driver with appropriate options"""
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-features=dbus')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # For Streamlit Cloud deployment
        if 'STREAMLIT_SHARING_MODE' in os.environ:
            options.binary_location = '/usr/bin/chromium'
            return webdriver.Chrome(options=options)
        else:
            # Local development - use webdriver-manager
            service = Service(ChromeDriverManager().install())
            return webdriver.Chrome(service=service, options=options)
    
    def search_images(self, query, max_images=100, progress_callback=None):
        """Perform Google image search and collect thumbnail URLs"""
        driver = self.setup_driver()
        self.thumbnails = []
        
        try:
            # Navigate to Google Images
            driver.get("https://www.google.com/imghp")
            
            # Find search box and enter query
            search_box = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "q"))
            )
            search_box.send_keys(query)
            search_box.send_keys(Keys.RETURN)
            
            # Wait for images to load
            time.sleep(2)
            
            # Scroll to load more images
            last_height = driver.execute_script("return document.body.scrollHeight")
            images_collected = 0
            
            while images_collected < max_images:
                # Get all image elements
                images = driver.find_elements(By.CSS_SELECTOR, "img.YQ4gaf")
                
                for img in images[images_collected:]:
                    if images_collected >= max_images:
                        break
                        
                    try:
                        # Get thumbnail URL
                        src = img.get_attribute("src")
                        if src and (src.startswith("http") or src.startswith("data:")):
                            self.thumbnails.append(src)
                            images_collected += 1
                            
                            # Update progress
                            if progress_callback:
                                progress_callback(images_collected / max_images)
                    except:
                        continue
                
                # Scroll down
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)
                
                # Check if we've reached the bottom
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    # Try to click "Show more results" button if available
                    try:
                        show_more = driver.find_element(By.CSS_SELECTOR, "input.mye4qd")
                        show_more.click()
                        time.sleep(2)
                    except:
                        break
                last_height = new_height
                
        finally:
            driver.quit()
            
        return self.thumbnails[:max_images]
    
    def get_image_from_url(self, url):
        """Convert URL or base64 string to PIL Image"""
        try:
            if url.startswith("data:"):
                # Handle base64 encoded images
                header, data = url.split(",", 1)
                image_data = base64.b64decode(data)
                return Image.open(io.BytesIO(image_data))
            else:
                # Download from URL
                response = requests.get(url, timeout=5)
                return Image.open(io.BytesIO(response.content))
        except:
            # Return a placeholder image
            img = Image.new('RGB', (100, 100), color='#f0f0f0')
            return img

# Initialize session state
if 'search_results' not in st.session_state:
    st.session_state.search_results = []
if 'last_query' not in st.session_state:
    st.session_state.last_query = ""

# Sidebar
with st.sidebar:
    st.markdown("# 🎨 Color Dots")
    st.markdown("---")
    
    # Search input
    query = st.text_input(
        "Search for images",
        placeholder="Enter your search query...",
        help="Type anything you want to search for on Google Images"
    )
    
    # Search button
    search_button = st.button("Search", type="primary", use_container_width=True)
    
    # Info section
    st.markdown("---")
    st.markdown("""
    ### How it works
    1. Enter a search term
    2. Click **Search**
    3. View your results in a beautiful circular grid
    
    The app will fetch the first 100 images from Google Images and display them as color dots.
    """)
    
    # Stats
    if st.session_state.search_results:
        st.markdown("---")
        st.metric("Images found", len(st.session_state.search_results))
        st.caption(f"Query: {st.session_state.last_query}")

# Main content area
main_container = st.container()

with main_container:
    if search_button and query:
        # Clear previous results
        st.session_state.search_results = []
        st.session_state.last_query = query
        
        # Create progress indicators
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Create ColorDots instance
        color_dots = ColorDotsStreamlit()
        
        # Search for images
        status_text.markdown('<p class="loading-text">🔍 Searching for images...</p>', unsafe_allow_html=True)
        
        def update_progress(value):
            progress_bar.progress(value)
            status_text.markdown(f'<p class="loading-text">📸 Collecting images: {int(value * 100)}%</p>', unsafe_allow_html=True)
        
        try:
            thumbnails = color_dots.search_images(query, max_images=100, progress_callback=update_progress)
            
            if thumbnails:
                status_text.markdown('<p class="loading-text">🎨 Processing images...</p>', unsafe_allow_html=True)
                
                # Convert URLs to images
                images = []
                for i, url in enumerate(thumbnails):
                    img = color_dots.get_image_from_url(url)
                    images.append(img)
                    progress_bar.progress((i + 1) / len(thumbnails))
                
                st.session_state.search_results = images
                
                # Clear progress indicators
                progress_bar.empty()
                status_text.empty()
                
                # Success message
                st.success(f"Found {len(images)} images for '{query}'!")
                
            else:
                st.error("No images found. Please try a different search term.")
                progress_bar.empty()
                status_text.empty()
                
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            progress_bar.empty()
            status_text.empty()
    
    # Display results
    if st.session_state.search_results:
        st.markdown("---")
        
        # Create HTML for grid
        grid_html = '<div class="image-grid">'
        
        for i, img in enumerate(st.session_state.search_results[:100]):
            # Convert PIL image to base64
            buffered = io.BytesIO()
            img.save(buffered, format="JPEG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            
            grid_html += f'''
            <div class="image-container">
                <img src="data:image/jpeg;base64,{img_str}" alt="Image {i+1}">
            </div>
            '''
        
        # Fill remaining spots with placeholders if less than 100
        for i in range(len(st.session_state.search_results), 100):
            grid_html += '''
            <div class="image-container" style="background-color: #f5f5f5;">
            </div>
            '''
        
        grid_html += '</div>'
        
        # Display grid
        st.markdown(grid_html, unsafe_allow_html=True)
        
    else:
        # Welcome message
        st.markdown("""
        <div style="text-align: center; padding: 50px; color: #666;">
            <h1 style="font-size: 48px; margin-bottom: 20px;">Welcome to Color Dots</h1>
            <p style="font-size: 18px; color: #888;">
                Enter a search term in the sidebar to create your circular image grid.
            </p>
        </div>
        """, unsafe_allow_html=True)
