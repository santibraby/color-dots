import streamlit as st
import os
import requests
from PIL import Image
import io
import base64

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
        # Google Custom Search API credentials from Streamlit secrets
        self.setup_api_credentials()
        self.setup_session_state()

    def setup_api_credentials(self):
        """Setup API credentials from Streamlit secrets or environment variables"""
        try:
            # Try to get from Streamlit secrets first
            self.API_KEY = st.secrets["GOOGLE_API_KEY"]
            self.SEARCH_ENGINE_ID = st.secrets["GOOGLE_CX"]
        except KeyError:
            # Fallback to environment variables
            self.API_KEY = os.getenv("GOOGLE_API_KEY", "")
            self.SEARCH_ENGINE_ID = os.getenv("GOOGLE_CX", "")

            if not self.API_KEY or not self.SEARCH_ENGINE_ID:
                st.error("""
                ⚠️ **API Credentials Not Found**

                Please set up your credentials in one of these ways:

                **Option 1: Streamlit Secrets (Recommended)**
                1. Create `.streamlit/secrets.toml` in your project root
                2. Add:
                ```
                GOOGLE_API_KEY = "your_api_key"
                GOOGLE_CX = "your_search_engine_id"
                ```

                **Option 2: Environment Variables**
                Set `GOOGLE_API_KEY` and `GOOGLE_CX` as environment variables.

                **Getting your credentials:**
                - API Key: [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
                - Search Engine ID: [Programmable Search Engine](https://programmablesearchengine.google.com/)
                """)
                st.stop()

    def setup_session_state(self):
        """Initialize session state variables"""
        if 'images' not in st.session_state:
            st.session_state.images = []
        if 'last_search' not in st.session_state:
            st.session_state.last_search = ""
        if 'api_calls_made' not in st.session_state:
            st.session_state.api_calls_made = 0

    def search_google_images(self, query, num_images=100):
        """Search for images using Google Custom Search API"""
        base_url = "https://www.googleapis.com/customsearch/v1"

        all_items = []
        images_collected = 0

        # Google Custom Search API returns max 10 results per call
        # We'll need to make multiple calls for 100 images
        max_calls = min(10, (num_images + 9) // 10)  # Max 10 calls (100 images)

        for start_index in range(0, max_calls * 10, 10):
            if images_collected >= num_images:
                break

            params = {
                "key": self.API_KEY,
                "cx": self.SEARCH_ENGINE_ID,
                "q": query,
                "searchType": "image",
                "num": 10,  # Max allowed per request
                "start": start_index + 1,  # API uses 1-based indexing
                "safe": "active",
                "imgSize": "medium"  # Get medium-sized images for better quality
            }

            try:
                response = requests.get(base_url, params=params)
                response.raise_for_status()
                data = response.json()

                if "items" in data:
                    all_items.extend(data["items"])
                    images_collected += len(data["items"])
                    st.session_state.api_calls_made += 1

                    # Update progress
                    if hasattr(self, 'progress'):
                        self.progress.progress(images_collected / num_images)

                else:
                    # No more results
                    break

            except requests.exceptions.RequestException as e:
                st.error(f"API request failed: {e}")
                if response.status_code == 429:
                    st.error("API quota exceeded. Please try again later.")
                break

        return all_items[:num_images]

    def load_image_from_url(self, url, timeout=5):
        """Load image from URL with error handling"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, timeout=timeout, headers=headers)
            response.raise_for_status()
            img = Image.open(io.BytesIO(response.content))

            # Convert to RGB if necessary
            if img.mode not in ('RGB', 'RGBA'):
                img = img.convert('RGB')

            # Resize if too large (for performance)
            max_size = 500
            if img.width > max_size or img.height > max_size:
                img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

            return img

        except Exception as e:
            # Return a placeholder image on error
            placeholder = Image.new('RGB', (200, 200), color='#e0e0e0')
            return placeholder

    def create_image_grid(self, images):
        """Create HTML grid of circular images"""
        html = '<div class="image-grid">'

        # Add images
        for i, img in enumerate(images[:100]):
            # Convert to base64 for embedding
            buffered = io.BytesIO()

            # Convert to RGB if needed
            if img.mode == 'RGBA':
                # Create white background
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3])
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')

            # Save as JPEG
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

            # API usage info
            st.markdown("---")
            st.markdown("### API Usage")
            st.metric("API calls today", st.session_state.api_calls_made)
            st.caption("Free tier: 100 calls/day")

            # API info
            with st.expander("ℹ️ API Configuration"):
                if self.API_KEY and self.SEARCH_ENGINE_ID:
                    st.success("✅ API credentials configured")
                    st.caption(f"Search Engine ID: {self.SEARCH_ENGINE_ID}")
                else:
                    st.error("❌ API credentials not found")

                st.info("""
                **Google Custom Search API Limits:**
                - Free: 100 queries/day
                - Each search uses ~10 API calls for 100 images

                **Need more quota?**
                Upgrade to paid tier in Google Cloud Console
                """)
        # Main area
        if search_clicked and search_query:
            # Check if API credentials are configured
            if not self.API_KEY or not self.SEARCH_ENGINE_ID:
                st.error("API credentials not configured. Please check the sidebar for setup instructions.")
                return

            st.session_state.images = []
            st.session_state.last_search = search_query

            # Progress indicators
            self.progress = st.progress(0)
            status = st.empty()

            try:
                # Search images using Google Custom Search API
                status.markdown('<p class="status-text">🔍 Searching Google Images...</p>',
                                unsafe_allow_html=True)

                # Get image metadata from API
                image_items = self.search_google_images(search_query)

                if image_items:
                    # Process images
                    status.markdown('<p class="status-text">🎨 Loading and processing images...</p>',
                                    unsafe_allow_html=True)

                    images = []
                    failed_count = 0

                    for i, item in enumerate(image_items):
                        # Get the image URL
                        image_url = item.get("link")

                        if image_url:
                            # Load the image
                            img = self.load_image_from_url(image_url)
                            images.append(img)
                        else:
                            failed_count += 1

                        # Update progress
                        self.progress.progress((i + 1) / len(image_items))

                    st.session_state.images = images

                    # Clear progress
                    self.progress.empty()
                    status.empty()

                    # Show results
                    success_msg = f"✅ Found {len(images)} images for '{search_query}'"
                    if failed_count > 0:
                        success_msg += f" ({failed_count} failed to load)"
                    st.success(success_msg)

                else:
                    st.warning("No images found. Try a different search term.")
                    self.progress.empty()
                    status.empty()

            except Exception as e:
                st.error(f"Error: {str(e)}")
                self.progress.empty()
                status.empty()

                # Provide specific error guidance
                if "API key not valid" in str(e):
                    st.error("""
                    **Invalid API Key**

                    Please check:
                    1. Your API key is correct in `.streamlit/secrets.toml`
                    2. The Custom Search API is enabled in Google Cloud Console
                    3. Your API key has not been regenerated or revoked
                    """)
                elif "invalid API key" in str(e).lower():
                    st.error("Invalid API key. Please check your Google Custom Search API configuration.")
                elif "quota" in str(e).lower():
                    st.error("API quota exceeded. The free tier allows 100 queries per day.")

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
                <p style="font-size: 14px; color: #999; margin-top: 20px;">
                    Powered by Google Custom Search API
                </p>
            </div>
            """, unsafe_allow_html=True)


# Run the app
if __name__ == "__main__":
    app = ColorDotsApp()
    app.run()