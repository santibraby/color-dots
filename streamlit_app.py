import streamlit as st
import streamlit.components.v1 as components
import requests
from PIL import Image
import io
import base64
import random
import json

# Page config
st.set_page_config(
    page_title="Color Dots",
    page_icon="🎨",
    layout="wide"
)

# Hide Streamlit UI elements and set white background
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container {
        padding-top: 2rem;
        max-width: 100%;
        padding-left: 0.5rem;
        padding-right: 0.5rem;
    }

    /* White background for the app */
    .stApp {
        background-color: white;
    }

    /* Flexbox Grid */
    .grid {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        width: 100%;
        max-width: 800px;
        margin: 1px auto;
        padding: 1px;
        background: white;
        border-radius: 0px;
        border: none;
        justify-content: center;
    }

    /* Circles */
    .circle {
        width: calc(10% - 7.2px); /* 10 columns with gap */
        aspect-ratio: 1;
        border-radius: 50%;
        background: #f5f5f5;
        overflow: hidden;
        position: relative;
        opacity: 1;
        transition: all 0.3s ease;
        border: none;
        cursor: pointer;
    }

    /* Mobile responsive - 5 columns */
    @media (max-width: 768px) {
        .circle {
            width: calc(20% - 6.4px); /* 5 columns with gap */
        }

        /* Fix iframe sizing on mobile */
        iframe {
            width: 100% !important;
        }
    }

    .circle:hover {
        transform: scale(1.05);
    }

    .circle.loaded {
        opacity: 1;
    }

    .circle img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        transition: opacity 0.5s ease;
    }

    .circle.color-mode img {
        opacity: 0;
    }

    /* Hex tooltip */
    .circle .hex-tooltip {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: rgba(0, 0, 0, 0.8);
        color: white;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 12px;
        font-family: monospace;
        opacity: 0;
        transition: opacity 0.2s ease;
        pointer-events: none;
        white-space: nowrap;
        z-index: 10;
    }

    .circle:hover .hex-tooltip {
        opacity: 1;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'images' not in st.session_state:
    st.session_state.images = []

# Google API credentials (use secrets in production)
API_KEY = st.secrets.get("GOOGLE_API_KEY", "")
SEARCH_ENGINE_ID = st.secrets.get("GOOGLE_CX", "")

# Check if API is configured
if not API_KEY or not SEARCH_ENGINE_ID:
    with st.sidebar:
        st.warning("""
        ⚠️ **API credentials not configured!**

        To use Google Image Search:
        1. Create `.streamlit/secrets.toml` file
        2. Add your credentials:
        ```
        GOOGLE_API_KEY = "your_api_key"
        GOOGLE_CX = "your_search_engine_id"
        ```
        """)


def search_google_images(query, num_images=100):
    """Get images from Google Custom Search API"""
    base_url = "https://www.googleapis.com/customsearch/v1"
    all_images = []

    # API returns max 10 per call, so we need multiple calls
    for start in range(0, num_images, 10):
        params = {
            "key": API_KEY,
            "cx": SEARCH_ENGINE_ID,
            "q": query,
            "searchType": "image",
            "num": 10,
            "start": start + 1
        }

        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            data = response.json()

            if "error" in data:
                st.error(f"API Error: {data['error'].get('message', 'Unknown error')}")
                return []

            if "items" in data:
                all_images.extend(data["items"])
            else:
                break

        except requests.exceptions.RequestException as e:
            st.error(f"Request Error: {e}")
            break
        except Exception as e:
            st.error(f"Unexpected Error: {e}")
            break

    return all_images[:num_images]


def load_image(url):
    """Load image from URL"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8'
        }
        response = requests.get(url, timeout=5, headers=headers)
        response.raise_for_status()

        img = Image.open(io.BytesIO(response.content))
        if img.mode != 'RGB':
            img = img.convert('RGB')
        # Resize for performance
        img.thumbnail((300, 300), Image.Resampling.LANCZOS)
        return img
    except Exception as e:
        # Return placeholder on error
        placeholder = Image.new('RGB', (300, 300), color='#f0f0f0')
        return placeholder


def get_random_color(img):
    """Extract a random color from image"""
    if img.mode != 'RGB':
        img = img.convert('RGB')

    width, height = img.size
    # Sample from center area for better colors
    x = random.randint(width // 4, 3 * width // 4)
    y = random.randint(height // 4, 3 * height // 4)

    r, g, b = img.getpixel((x, y))
    return f"#{r:02x}{g:02x}{b:02x}"


def image_to_base64(img):
    """Convert PIL image to base64"""
    buffered = io.BytesIO()
    # Make square
    width, height = img.size
    size = min(width, height)
    img = img.crop((
        (width - size) // 2,
        (height - size) // 2,
        (width + size) // 2,
        (height + size) // 2
    ))
    img = img.resize((150, 150), Image.Resampling.LANCZOS)
    img.save(buffered, format="JPEG", quality=80)
    return base64.b64encode(buffered.getvalue()).decode()


def create_grid(images):
    """Create the animated grid HTML"""
    # Prepare image data
    image_data = []
    for img in images:
        try:
            image_data.append({
                'base64': image_to_base64(img),
                'color': get_random_color(img)
            })
        except Exception as e:
            pass

    # Create grid HTML
    html = '<div class="grid" id="imageGrid">'
    for i in range(100):
        html += f'<div class="circle" id="slot-{i}"></div>'
    html += '</div>'

    # Add animation script
    html += f'''
    <script>
    (function() {{
        const images = {json.dumps(image_data)};
        const slots = Array.from({{length: 100}}, (_, i) => i);

        // Shuffle slots for random placement
        for (let i = slots.length - 1; i > 0; i--) {{
            const j = Math.floor(Math.random() * (i + 1));
            [slots[i], slots[j]] = [slots[j], slots[i]];
        }}

        // Load images one by one
        images.forEach((img, index) => {{
            if (index < 100) {{
                const slotId = slots[index];
                const delay = index * 100; // 100ms between each

                setTimeout(() => {{
                    const slot = document.getElementById('slot-' + slotId);
                    if (slot) {{
                        slot.innerHTML = '<img src="data:image/jpeg;base64,' + img.base64 + '" alt="">';
                        slot.style.opacity = '1';
                        slot.classList.add('loaded');

                        // After 2 seconds, show color
                        setTimeout(() => {{
                            slot.classList.add('color-mode');
                            slot.style.backgroundColor = img.color;

                            // Add hex tooltip
                            const tooltip = document.createElement('div');
                            tooltip.className = 'hex-tooltip';
                            tooltip.textContent = img.color;
                            slot.appendChild(tooltip);
                        }}, 2000);
                    }}
                }}, delay);
            }}
        }});
    }})();
    </script>
    '''

    return html


# UI
# Sidebar search controls
with st.sidebar:
    st.markdown("### 🎨 Color Dots")
    st.markdown("---")
    st.markdown("### Search Images")
    query = st.text_input("Search for images", placeholder="Enter any word or phrase...", label_visibility="collapsed")
    if st.button("Search", use_container_width=True):
        if query and API_KEY and SEARCH_ENGINE_ID:
            with st.spinner("Searching..."):
                # Get images from API
                image_items = search_google_images(query)

                if image_items:
                    with st.spinner("Loading images..."):
                        # Load actual images
                        images = []
                        progress_bar = st.progress(0)

                        for i, item in enumerate(image_items):
                            # Try thumbnail first, then full image
                            url = None
                            if "image" in item and "thumbnailLink" in item["image"]:
                                url = item["image"]["thumbnailLink"]
                            elif "link" in item:
                                url = item["link"]

                            if url:
                                img = load_image(url)
                                images.append(img)

                            # Update progress
                            progress_bar.progress((i + 1) / len(image_items))

                        progress_bar.empty()
                        st.session_state.images = images
                        st.success(f"Found {len(images)} images")
                else:
                    st.error("No images found")
        else:
            st.error("Please configure API credentials in .streamlit/secrets.toml")

# Display grid
if st.session_state.images:
    # Create and display animated grid
    grid_html = create_grid(st.session_state.images)

    # Create complete HTML document
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{
                margin: 0;
                padding: 0;
                background: white;
                overflow-x: hidden;
                width: 100%;
            }}

            .grid {{
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
                width: calc(100% - 40px);
                max-width: 800px;
                margin: 10px auto;
                padding: 20px;
                background: white;
                border-radius: 10px;
                border: none;
                justify-content: center;
                box-sizing: border-box;
            }}

            .circle {{
                width: calc(10% - 7.2px); /* 10 columns with gap */
                aspect-ratio: 1;
                border-radius: 50%;
                background: #f5f5f5;
                overflow: hidden;
                position: relative;
                opacity: 1;
                transition: all 0.3s ease;
                border: none;
                cursor: pointer;
                box-sizing: border-box;
            }}

            /* Mobile responsive - 5 columns */
            @media (max-width: 768px) {{
                .grid {{
                    width: calc(100% - 20px);
                    padding: 10px;
                    gap: 6px;
                }}

                .circle {{
                    width: calc(20% - 4.8px); /* 5 columns with gap */
                }}
            }}

            .circle:hover {{
                transform: scale(1.05);
            }}

            .circle.loaded {{
                opacity: 1;
            }}

            .circle img {{
                width: 100%;
                height: 100%;
                object-fit: cover;
                transition: opacity 0.5s ease;
            }}

            .circle.color-mode img {{
                opacity: 0;
            }}

            /* Hex tooltip */
            .circle .hex-tooltip {{
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                background: rgba(0, 0, 0, 0.8);
                color: white;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 12px;
                font-family: monospace;
                opacity: 0;
                transition: opacity 0.2s ease;
                pointer-events: none;
                white-space: nowrap;
                z-index: 10;
            }}

            .circle:hover .hex-tooltip {{
                opacity: 1;
            }}
        </style>
    </head>
    <body>
        {grid_html}
    </body>
    </html>
    """

    # Use components.html for proper rendering
    # Calculate height based on grid: 100 items / 5 columns = 20 rows for mobile
    # Account for gaps and padding
    components.html(html_content, height=1600, scrolling=False)

else:
    st.markdown("""
    <div style='text-align: center; padding: 8rem 2rem; color: #666;'>
        <h1 style='color: #333; margin-bottom: 2rem;'>Color Dots</h1>
        <p>Enter a search term in the sidebar to create your color dot grid</p>
    </div>
    """, unsafe_allow_html=True)