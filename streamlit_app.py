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
if 'sort_mode' not in st.session_state:
    st.session_state.sort_mode = 'random'  # random, hex, hue

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
    # Sample from center 60% area for better colors
    x = random.randint(int(width * 0.2), int(width * 0.8))
    y = random.randint(int(height * 0.2), int(height * 0.8))

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


def hex_to_hsl(hex_color):
    """Convert hex color to HSL values"""
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16) / 255.0
    g = int(hex_color[2:4], 16) / 255.0
    b = int(hex_color[4:6], 16) / 255.0

    max_val = max(r, g, b)
    min_val = min(r, g, b)
    diff = max_val - min_val

    # Lightness
    l = (max_val + min_val) / 2

    if diff == 0:
        h = 0
        s = 0
    else:
        # Saturation
        if l == 0 or l == 1:
            s = 0
        else:
            s = diff / (1 - abs(2 * l - 1))

        # Hue
        if max_val == r:
            h = ((g - b) / diff + (6 if g < b else 0)) / 6
        elif max_val == g:
            h = ((b - r) / diff + 2) / 6
        else:
            h = ((r - g) / diff + 4) / 6

    return h, s, l


def create_grid(images, sort_mode='random'):
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

    # Sort by color if not in random mode
    if sort_mode == 'hex':
        # Sort by hex value
        image_data.sort(key=lambda x: x['color'])
    elif sort_mode == 'hue':
        # Sort by hue for color grouping
        def hue_sort_key(item):
            h, s, l = hex_to_hsl(item['color'])
            # Put grays (low saturation) at the end
            if s < 0.1:
                return 1.0 + l  # Sort grays by lightness
            return h

        image_data.sort(key=hue_sort_key)

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
        const sortMode = '{sort_mode}';

        // If random mode, shuffle slots
        if (sortMode === 'random') {{
            for (let i = slots.length - 1; i > 0; i--) {{
                const j = Math.floor(Math.random() * (i + 1));
                [slots[i], slots[j]] = [slots[j], slots[i]];
            }}
        }}

        // Load images one by one
        images.forEach((img, index) => {{
            if (index < 100) {{
                const slotId = sortMode === 'random' ? slots[index] : index;
                // Faster animation for sorted modes
                const delay = sortMode === 'random' ? index * 100 : index * 25;

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
                        st.session_state.sort_mode = 'random'  # Reset sort mode on new search
                        st.success(f"Found {len(images)} images")
                else:
                    st.error("No images found")
        else:
            st.error("Please configure API credentials in .streamlit/secrets.toml")

    # Add reselect colors button if images are loaded
    if st.session_state.images:
        st.markdown("---")
        st.markdown("### Color Options")

        # Reselect colors
        st.markdown("##### Pick New Colors")
        st.markdown("<small style='color: #666;'>Sample different pixels from each image</small>",
                    unsafe_allow_html=True)
        if st.button("🎲 Reselect Colors", use_container_width=True):
            # Force a refresh to re-pick colors (maintains sort mode)
            st.rerun()

        # Sort button
        st.markdown("##### Arrange Grid")
        if st.session_state.sort_mode == 'random':
            help_text = "Sort colors by hex value"
            button_text = "🎨 Sort by Hex"
            next_mode = 'hex'
        elif st.session_state.sort_mode == 'hex':
            help_text = "Group colors by hue (reds, greens, blues...)"
            button_text = "🌈 Sort by Hue"
            next_mode = 'hue'
        else:  # hue
            help_text = "Random layout"
            button_text = "🔀 Randomize Order"
            next_mode = 'random'

        st.markdown(f"<small style='color: #666;'>{help_text}</small>", unsafe_allow_html=True)
        if st.button(button_text, use_container_width=True):
            st.session_state.sort_mode = next_mode
            st.rerun()

# Display grid
if st.session_state.images:
    # Show current mode with subtle styling
    if st.session_state.sort_mode == 'hex':
        st.markdown(
            "<p style='text-align: center; color: #999; font-size: 0.9em; margin-bottom: 0.5rem;'>Sorted by hex value</p>",
            unsafe_allow_html=True)
    elif st.session_state.sort_mode == 'hue':
        st.markdown(
            "<p style='text-align: center; color: #999; font-size: 0.9em; margin-bottom: 0.5rem;'>Sorted by hue (color families)</p>",
            unsafe_allow_html=True)

    # Create and display animated grid
    grid_html = create_grid(st.session_state.images, st.session_state.sort_mode)

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