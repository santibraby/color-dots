import streamlit as st
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

# Hide Streamlit UI elements
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container {
        padding-top: 2rem;
        max-width: 900px;
    }

    /* 10x10 Grid */
    .grid {
        display: grid;
        grid-template-columns: repeat(10, 1fr);
        gap: 8px;
        width: 100%;
        max-width: 800px;
        margin: 0 auto;
    }

    /* Circles */
    .circle {
        aspect-ratio: 1;
        border-radius: 50%;
        background: #f0f0f0;
        overflow: hidden;
        position: relative;
        opacity: 0;
        transition: opacity 0.3s ease;
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
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'images' not in st.session_state:
    st.session_state.images = []

# Google API credentials (use secrets in production)
API_KEY = st.secrets.get("GOOGLE_API_KEY", "")
SEARCH_ENGINE_ID = st.secrets.get("GOOGLE_CX", "")


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
            data = response.json()

            if "items" in data:
                all_images.extend(data["items"])
            else:
                break

        except Exception as e:
            st.error(f"API Error: {e}")
            break

    return all_images[:num_images]


def load_image(url):
    """Load image from URL"""
    try:
        response = requests.get(url, timeout=5, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        img = Image.open(io.BytesIO(response.content))
        if img.mode != 'RGB':
            img = img.convert('RGB')
        # Resize for performance
        img.thumbnail((300, 300), Image.Resampling.LANCZOS)
        return img
    except:
        # Return placeholder on error
        return Image.new('RGB', (300, 300), color='#cccccc')


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
        except:
            pass

    # Create grid HTML
    html = '<div class="grid">'
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
                    const slot = document.getElementById(`slot-${{slotId}}`);
                    if (slot) {{
                        slot.innerHTML = `<img src="data:image/jpeg;base64,${{img.base64}}" alt="">`;
                        slot.classList.add('loaded');

                        // After 2 seconds, show color
                        setTimeout(() => {{
                            slot.classList.add('color-mode');
                            slot.style.backgroundColor = img.color;
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
st.markdown("<h1 style='text-align: center; margin-bottom: 2rem;'>Color Dots</h1>", unsafe_allow_html=True)

# Search controls
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    query = st.text_input("Search for images", placeholder="Enter any word or phrase...")
    if st.button("Search", use_container_width=True):
        if query and API_KEY and SEARCH_ENGINE_ID:
            with st.spinner("Searching..."):
                # Get images from API
                image_items = search_google_images(query)

                if image_items:
                    with st.spinner("Loading images..."):
                        # Load actual images
                        images = []
                        for item in image_items:
                            if url := item.get("link"):
                                images.append(load_image(url))

                        st.session_state.images = images
                        st.success(f"Found {len(images)} images")
                else:
                    st.error("No images found")
        else:
            st.error("Please configure API credentials in .streamlit/secrets.toml")

# Display grid
if st.session_state.images:
    if st.button("🔄 Replay Animation"):
        st.rerun()

    grid_html = create_grid(st.session_state.images)
    st.markdown(grid_html, unsafe_allow_html=True)
else:
    st.markdown("""
    <div style='text-align: center; padding: 4rem; color: #666;'>
        <p>Enter a search term above to create your color dot grid</p>
    </div>
    """, unsafe_allow_html=True)