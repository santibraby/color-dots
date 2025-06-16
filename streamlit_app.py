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

    /* Image grid - simplified */
    .image-grid {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        padding: 20px;
        max-width: 1200px;
        margin: 0 auto;
        justify-content: center;
    }

    /* Circle images - simplified */
    .circle-image {
        width: 80px;
        height: 80px;
        border-radius: 50%;
        overflow: hidden;
        background-color: #f0f0f0;
        flex-shrink: 0;
    }

    .circle-image img {
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
                "imgSize": "medium",  # Get medium-sized images for better quality
                "fileType": "jpg|png|jpeg"  # Only get common image formats
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
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Referer': 'https://www.google.com/'
            }

            # Try direct URL first
            response = requests.get(url, timeout=timeout, headers=headers, stream=True)
            response.raise_for_status()

            # Read content
            content = response.content
            if not content:
                raise ValueError("Empty response")

            img = Image.open(io.BytesIO(content))

            # Convert to RGB if necessary
            if img.mode not in ('RGB', 'RGBA'):
                img = img.convert('RGB')

            # Resize if too large (for performance)
            max_size = 300
            if img.width > max_size or img.height > max_size:
                img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

            return img, None

        except Exception as e:
            # Return a placeholder image with error info
            placeholder = Image.new('RGB', (200, 200), color='#ffcccc')
            return placeholder, str(e)

    def create_image_grid(self, images):
        """Create HTML grid of circular images"""
        if not images:
            return '<div class="image-grid"><p>No images to display</p></div>'

        html = '<div class="image-grid">'

        # Add images
        for i, img in enumerate(images[:100]):
            try:
                # Convert to base64 for embedding
                img_str = self._img_to_base64(img)
                html += f'<div class="circle-image"><img src="data:image/jpeg;base64,{img_str}" alt=""></div>'
            except:
                # Add placeholder on error
                html += '<div class="circle-image"></div>'

        # Fill remaining spots
        for i in range(len(images), 100):
            html += '<div class="circle-image"></div>'

        html += '</div>'
        return html

    def _img_to_base64(self, img):
        """Convert PIL image to base64 string"""
        buffered = io.BytesIO()

        # Ensure RGB mode
        if img.mode != 'RGB':
            img = img.convert('RGB')

        # Make square by cropping center
        width, height = img.size
        size = min(width, height)
        left = (width - size) // 2
        top = (height - size) // 2
        img = img.crop((left, top, left + size, top + size))

        # Resize to reasonable size
        img = img.resize((150, 150), Image.Resampling.LANCZOS)

        # Save as JPEG
        img.save(buffered, format="JPEG", quality=75)
        return base64.b64encode(buffered.getvalue()).decode()

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
                    failed_images = []
                    loaded_count = 0

                    # Debug info
                    with st.expander("🔍 Debug Info", expanded=False):
                        debug_container = st.container()

                    for i, item in enumerate(image_items):
                        # Get the image URL and metadata
                        image_url = item.get("link")
                        title = item.get("title", "No title")

                        # Try to get thumbnail first (more reliable)
                        thumbnail_url = None
                        if "image" in item:
                            thumbnail_url = item["image"].get("thumbnailLink")

                        # Prefer thumbnail over full image
                        url_to_use = thumbnail_url if thumbnail_url else image_url

                        if url_to_use:
                            img, error = self.load_image_from_url(url_to_use)

                            if error and image_url and image_url != url_to_use:
                                # Try the full image if thumbnail failed
                                img, error = self.load_image_from_url(image_url)

                            images.append(img)
                            if error:
                                failed_images.append(f"{title}: {error}")
                                with debug_container:
                                    st.caption(f"⚠️ Image {i + 1} had issues: {error[:100]}")
                            else:
                                loaded_count += 1
                        else:
                            # No URL provided
                            placeholder = Image.new('RGB', (200, 200), color='#cccccc')
                            images.append(placeholder)
                            failed_images.append(f"{title}: No URL provided")

                        # Update progress
                        self.progress.progress((i + 1) / len(image_items))

                    st.session_state.images = images

                    # Clear progress
                    self.progress.empty()
                    status.empty()

                    # Show results
                    if loaded_count > 0:
                        success_msg = f"✅ Successfully loaded {loaded_count}/{len(image_items)} images for '{search_query}'"
                        st.success(success_msg)

                        if failed_images:
                            with st.expander(f"⚠️ {len(failed_images)} images failed to load"):
                                for fail_msg in failed_images[:10]:  # Show first 10
                                    st.caption(fail_msg)
                    else:
                        st.error(
                            "Failed to load any images. This might be due to CORS restrictions or invalid image URLs.")

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

            # Add debug toggle
            debug_mode = st.checkbox("🐛 Debug Mode (Show images in simple grid)", value=False)

            if debug_mode:
                # Simple display for debugging
                st.write(f"Displaying {len(st.session_state.images)} images:")
                cols = st.columns(5)
                for idx, img in enumerate(st.session_state.images[:20]):  # Show first 20
                    with cols[idx % 5]:
                        st.image(img, caption=f"Image {idx + 1}", use_column_width=True)
            else:
                # Test if HTML rendering works
                test_html = st.checkbox("Test HTML Rendering", value=False)
                if test_html:
                    # Simple test with one image
                    if st.session_state.images:
                        test_img = st.session_state.images[0]
                        buffered = io.BytesIO()
                        if test_img.mode != 'RGB':
                            test_img = test_img.convert('RGB')
                        test_img.save(buffered, format="JPEG", quality=80)
                        img_str = base64.b64encode(buffered.getvalue()).decode()

                        st.markdown(
                            f'<div style="width: 200px; height: 200px; border-radius: 50%; overflow: hidden; margin: 20px;">'
                            f'<img src="data:image/jpeg;base64,{img_str}" style="width: 100%; height: 100%; object-fit: cover;">'
                            f'</div>',
                            unsafe_allow_html=True
                        )
                        st.write("If you see a circular image above, HTML rendering works!")

                # Regular grid display
                st.write("Generating grid...")
                grid_html = self.create_image_grid(st.session_state.images)

                # Display with container for better isolation
                grid_container = st.container()
                with grid_container:
                    st.markdown(grid_html, unsafe_allow_html=True)

                # Simplest display method using st.image
                if st.checkbox("Use Simplest Display (st.image in grid)", value=False):
                    st.write("Simple grid using st.image:")

                    # Create a 10x10 grid
                    for row in range(10):
                        cols = st.columns(10)
                        for col in range(10):
                            idx = row * 10 + col
                            if idx < len(st.session_state.images):
                                with cols[col]:
                                    # Apply circular mask using CSS
                                    st.markdown(
                                        """
                                        <style>
                                        .stImage > img {
                                            border-radius: 50% !important;
                                            object-fit: cover !important;
                                            aspect-ratio: 1 !important;
                                        }
                                        </style>
                                        """,
                                        unsafe_allow_html=True
                                    )
                                    st.image(st.session_state.images[idx], use_column_width=True)
                    st.write("Alternative grid display using Streamlit columns:")

                    # Create a 10x10 grid using Streamlit columns
                    for row in range(10):
                        cols = st.columns(10)
                        for col in range(10):
                            idx = row * 10 + col
                            if idx < len(st.session_state.images):
                                with cols[col]:
                                    # Use custom CSS for circular display
                                    img_base64 = self._img_to_base64(st.session_state.images[idx])
                                    st.markdown(
                                        f'''
                                        <div style="
                                            width: 100%;
                                            aspect-ratio: 1;
                                            border-radius: 50%;
                                            overflow: hidden;
                                            background-image: url('data:image/jpeg;base64,{img_base64}');
                                            background-size: cover;
                                            background-position: center;
                                        "></div>
                                        ''',
                                        unsafe_allow_html=True
                                    )
                            else:
                                with cols[col]:
                                    # Empty placeholder
                                    st.markdown(
                                        '<div style="width: 100%; aspect-ratio: 1; border-radius: 50%; background-color: #f0f0f0;"></div>',
                                        unsafe_allow_html=True
                                    )
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