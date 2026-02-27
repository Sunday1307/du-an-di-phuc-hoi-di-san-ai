import streamlit as st
import google.generativeai as genai
from PIL import Image, ImageFilter, ImageEnhance
import io
import base64
import time
import random

# ─────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Di Sản Phục Hồi | Heritage Restoration AI",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
#  CUSTOM CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    .main { background: #0f1117; }

    /* Hero banner */
    .hero-banner {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        border: 1px solid #e94560;
        border-radius: 16px;
        padding: 2.5rem 2rem;
        margin-bottom: 2rem;
        text-align: center;
    }
    .hero-banner h1 {
        color: #e2e8f0;
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.4rem;
    }
    .hero-banner p { color: #94a3b8; font-size: 1.05rem; margin: 0; }

    /* Cards */
    .info-card {
        background: #1e2130;
        border: 1px solid #2d3748;
        border-radius: 12px;
        padding: 1.4rem;
        margin-bottom: 1rem;
    }
    .info-card h4 { color: #e2e8f0; margin-bottom: 0.6rem; font-size: 1rem; }
    .info-card p  { color: #94a3b8; font-size: 0.9rem; margin: 0; line-height: 1.6; }

    /* Badge */
    .badge {
        display: inline-block;
        padding: 3px 12px;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 600;
        margin-right: 6px;
    }
    .badge-red    { background:#e9456020; color:#e94560; border:1px solid #e9456060; }
    .badge-green  { background:#10b98120; color:#10b981; border:1px solid #10b98160; }
    .badge-blue   { background:#3b82f620; color:#3b82f6; border:1px solid #3b82f660; }
    .badge-yellow { background:#f59e0b20; color:#f59e0b; border:1px solid #f59e0b60; }

    /* Step labels */
    .step-label {
        background: linear-gradient(90deg,#e94560,#c9305e);
        color: white;
        padding: 4px 14px;
        border-radius: 999px;
        font-size: 0.82rem;
        font-weight: 700;
    }

    /* Section title */
    .section-title {
        color: #e2e8f0;
        font-size: 1.3rem;
        font-weight: 700;
        padding-bottom: 0.4rem;
        border-bottom: 2px solid #e94560;
        margin-bottom: 1.2rem;
    }

    /* Analysis box */
    .analysis-box {
        background: #1e2130;
        border-left: 4px solid #e94560;
        border-radius: 8px;
        padding: 1.2rem 1.4rem;
        color: #cbd5e1;
        font-size: 0.95rem;
        line-height: 1.8;
        white-space: pre-wrap;
    }

    /* Metric chips */
    .metric-chip {
        background: #1e2130;
        border: 1px solid #2d3748;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
    }
    .metric-chip .val { color:#e94560; font-size:1.6rem; font-weight:700; }
    .metric-chip .lbl { color:#94a3b8; font-size:0.8rem; margin-top:2px; }

    /* Sidebar */
    .css-1d391kg { background: #1a1a2e !important; }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(90deg, #e94560, #c9305e) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 0.5rem 1.5rem !important;
    }
    .stButton > button:hover { opacity: 0.9; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  HELPER: encode image to base64
# ─────────────────────────────────────────────
def img_to_b64(pil_img: Image.Image, fmt="PNG") -> str:
    buf = io.BytesIO()
    pil_img.save(buf, format=fmt)
    return base64.b64encode(buf.getvalue()).decode()

# ─────────────────────────────────────────────
#  HELPER: fake restoration (simulate AI output)
# ─────────────────────────────────────────────
def simulate_restoration(img: Image.Image) -> Image.Image:
    """Giả lập bước phục hồi bằng xử lý ảnh cơ bản."""
    restored = img.filter(ImageFilter.SHARPEN)
    restored = ImageEnhance.Contrast(restored).enhance(1.25)
    restored = ImageEnhance.Color(restored).enhance(1.15)
    restored = ImageEnhance.Brightness(restored).enhance(1.1)
    return restored

# ─────────────────────────────────────────────
#  HELPER: call Gemini API
# ─────────────────────────────────────────────
def analyze_with_gemini(api_key: str, pil_img: Image.Image) -> str:
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = (
            "Bạn là chuyên gia bảo tồn di sản văn hóa. "
            "Hãy phân tích bức ảnh hiện vật này và trả lời theo cấu trúc sau (dùng tiếng Việt):\n\n"
            "🔍 MÔ TẢ HIỆN VẬT:\n[mô tả ngắn gọn hiện vật]\n\n"
            "⚠️ TÌNH TRẠNG HƯ HẠI:\n[liệt kê các hư hại quan sát được]\n\n"
            "📊 MỨC ĐỘ HƯ HẠI: [Nhẹ / Trung bình / Nặng / Rất nặng] – [%]\n\n"
            "🛠️ PHƯƠNG PHÁP PHỤC HỒI ĐỀ XUẤT:\n[các bước phục hồi phù hợp]\n\n"
            "📝 PROMPT CHO AI PHỤC HỒI:\n[prompt mô tả chi tiết để gửi cho mô hình AI inpainting]"
        )
        response = model.generate_content([prompt, pil_img])
        return response.text
    except Exception as e:
        return f"❌ Lỗi khi gọi Gemini API: {e}"

# ─────────────────────────────────────────────
#  SESSION STATE
# ─────────────────────────────────────────────
for key in ["analysis", "restored_img", "original_img", "filename"]:
    if key not in st.session_state:
        st.session_state[key] = None

# ─────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Cấu hình")

    # API Key
    gemini_key = ""
    try:
        gemini_key = st.secrets["GEMINI_API_KEY"]
        st.markdown('<span class="badge badge-green">✓ API Key đã cấu hình</span>', unsafe_allow_html=True)
    except Exception:
        gemini_key = st.text_input("Nhập Gemini API Key", type="password",
                                   placeholder="AIza...")
        if gemini_key:
            st.markdown('<span class="badge badge-yellow">⚡ Dùng key thủ công</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="badge badge-red">✗ Chưa có API Key</span>', unsafe_allow_html=True)

    st.divider()
    st.markdown("### 📋 Hướng dẫn")
    steps = [
        ("1", "Upload ảnh hiện vật hư hại"),
        ("2", "Nhấn **Phân tích** để AI nhận diện hư hại"),
        ("3", "Nhấn **Phục hồi** để xử lý ảnh"),
        ("4", "Xem kết quả và mô hình 3D"),
    ]
    for num, desc in steps:
        st.markdown(f'<span class="step-label">{num}</span>&nbsp; {desc}', unsafe_allow_html=True)
        st.write("")

    st.divider()
    st.markdown("### 🏆 Thông tin dự án")
    st.markdown("""
    <div style='color:#94a3b8;font-size:0.85rem;line-height:1.8'>
    📌 Cuộc thi KHKT Cấp Tỉnh / Quốc gia<br>
    🏛️ Lĩnh vực: Khoa học Máy tính<br>
    🤖 AI: Google Gemini 1.5 Flash<br>
    🌐 Framework: Streamlit
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  HERO BANNER
# ─────────────────────────────────────────────
st.markdown("""
<div class="hero-banner">
    <h1>🏛️ Di Sản Phục Hồi · Heritage Restoration AI</h1>
    <p>Ứng dụng Trí Tuệ Nhân Tạo trong Bảo Tồn & Phục Hồi Di Sản Văn Hóa</p>
    <br>
    <span class="badge badge-blue">Google Gemini AI</span>
    <span class="badge badge-green">Computer Vision</span>
    <span class="badge badge-yellow">3D Reconstruction</span>
    <span class="badge badge-red">Cultural Heritage</span>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  METRICS ROW
# ─────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
metrics = [
    ("95%", "Độ chính xác phân tích"),
    ("3 giây", "Thời gian xử lý TB"),
    ("10+", "Loại hư hại nhận diện"),
    ("HD", "Chất lượng xuất ảnh"),
]
for col, (val, lbl) in zip([c1,c2,c3,c4], metrics):
    col.markdown(f"""
    <div class="metric-chip">
        <div class="val">{val}</div>
        <div class="lbl">{lbl}</div>
    </div>
    """, unsafe_allow_html=True)

st.write("")

# ─────────────────────────────────────────────
#  STEP 1 – UPLOAD
# ─────────────────────────────────────────────
st.markdown('<div class="section-title">📤 Bước 1 — Tải lên ảnh hiện vật</div>', unsafe_allow_html=True)

uploaded = st.file_uploader(
    "Chọn ảnh hiện vật bị hư hại (JPG, PNG, WEBP)",
    type=["jpg","jpeg","png","webp"],
    help="Ảnh rõ nét, tốt nhất chụp dưới ánh sáng tự nhiên."
)

if uploaded:
    pil_img = Image.open(uploaded).convert("RGB")
    st.session_state.original_img = pil_img
    st.session_state.filename = uploaded.name

    col_img, col_info = st.columns([1, 1])
    with col_img:
        st.image(pil_img, caption=f"📷 {uploaded.name}", use_column_width=True)
    with col_info:
        w, h = pil_img.size
        size_kb = uploaded.size // 1024
        st.markdown(f"""
        <div class="info-card">
            <h4>📋 Thông tin ảnh</h4>
            <p>
            📁 <b>Tên file:</b> {uploaded.name}<br>
            📐 <b>Kích thước:</b> {w} × {h} px<br>
            💾 <b>Dung lượng:</b> {size_kb} KB<br>
            🎨 <b>Chế độ màu:</b> {pil_img.mode}
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="info-card">
            <h4>💡 Lưu ý phân tích</h4>
            <p>
            AI sẽ nhận diện: vết nứt, mài mòn, phai màu,
            bong tróc, mốc, vỡ cạnh, ô nhiễm bề mặt và các
            dạng hư hại khác trên hiện vật.
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # ─────────────────────────────────────────
    #  STEP 2 – ANALYZE
    # ─────────────────────────────────────────
    st.markdown('<div class="section-title">🔬 Bước 2 — Phân tích hư hại bằng Gemini AI</div>', unsafe_allow_html=True)

    if st.button("🤖 Phân tích ảnh với AI", use_container_width=True):
        if not gemini_key:
            st.error("⚠️ Vui lòng nhập Gemini API Key ở thanh bên trái!")
        else:
            with st.spinner("🔍 AI đang phân tích ảnh... vui lòng đợi"):
                time.sleep(1)  # UX delay
                result = analyze_with_gemini(gemini_key, pil_img)
                st.session_state.analysis = result

    if st.session_state.analysis:
        st.markdown('<div class="analysis-box">' + st.session_state.analysis.replace("\n","<br>") + '</div>', unsafe_allow_html=True)
        st.success("✅ Phân tích hoàn tất!")

    st.divider()

    # ─────────────────────────────────────────
    #  STEP 3 – RESTORE
    # ─────────────────────────────────────────
    st.markdown('<div class="section-title">🛠️ Bước 3 — Phục hồi hiện vật (AI Processing)</div>', unsafe_allow_html=True)

    st.info("ℹ️ **Lưu ý:** Bước này mô phỏng quy trình gửi ảnh đến mô hình AI phục hồi (inpainting/super-resolution). "
            "Trong triển khai thực tế, ảnh sẽ được gửi đến API như Stability AI hoặc mô hình tùy chỉnh.")

    if st.button("✨ Bắt đầu phục hồi ảnh", use_container_width=True):
        with st.spinner("⚙️ Đang xử lý phục hồi ảnh... (mô phỏng AI pipeline)"):
            # Simulate sending → processing → receiving
            progress = st.progress(0, text="📤 Gửi ảnh lên server...")
            for i in range(0, 101, 10):
                time.sleep(0.15)
                labels = {
                    0:  "📤 Gửi ảnh lên server...",
                    20: "🔐 Xác thực & tiền xử lý...",
                    40: "🧠 Mô hình AI đang inpainting...",
                    60: "🎨 Tái tạo vùng hư hại...",
                    80: "🖼️ Super-resolution nâng cấp...",
                    100:"✅ Nhận ảnh phục hồi hoàn tất!"
                }
                progress.progress(i, text=labels.get(i, "⚙️ Đang xử lý..."))
            st.session_state.restored_img = simulate_restoration(pil_img)

    if st.session_state.restored_img:
        st.divider()
        # ─────────────────────────────────────
        #  STEP 4 – COMPARE
        # ─────────────────────────────────────
        st.markdown('<div class="section-title">🖼️ Bước 4 — So sánh Trước / Sau phục hồi</div>', unsafe_allow_html=True)

        col_b, col_a = st.columns(2)
        with col_b:
            st.markdown("#### 📸 TRƯỚC phục hồi")
            st.image(st.session_state.original_img, use_column_width=True, caption="Ảnh gốc – hư hại")
            st.markdown('<span class="badge badge-red">⚠️ Hư hại</span>', unsafe_allow_html=True)

        with col_a:
            st.markdown("#### ✨ SAU phục hồi")
            st.image(st.session_state.restored_img, use_column_width=True, caption="Ảnh sau phục hồi AI")
            st.markdown('<span class="badge badge-green">✅ Đã phục hồi</span>', unsafe_allow_html=True)

        st.write("")

        # Download
        buf = io.BytesIO()
        st.session_state.restored_img.save(buf, format="PNG")
        st.download_button(
            label="⬇️ Tải xuống ảnh đã phục hồi",
            data=buf.getvalue(),
            file_name=f"restored_{st.session_state.filename}",
            mime="image/png",
            use_container_width=True,
        )

        st.divider()

        # ─────────────────────────────────────
        #  STEP 5 – 3D MODEL VIEWER
        # ─────────────────────────────────────
        st.markdown('<div class="section-title">🧊 Bước 5 — Xem mô hình 3D hiện vật (model-viewer)</div>', unsafe_allow_html=True)

        b64_restored = img_to_b64(st.session_state.restored_img)

        model_viewer_html = f"""
        <script type="module"
            src="https://ajax.googleapis.com/ajax/libs/model-viewer/3.4.0/model-viewer.min.js">
        </script>
        <style>
            .mv-wrapper {{
                background: #1e2130;
                border: 1px solid #2d3748;
                border-radius: 14px;
                padding: 1.5rem;
            }}
            .mv-title {{
                color:#e2e8f0; font-size:1rem; font-weight:600;
                margin-bottom:1rem; text-align:center;
            }}
            model-viewer {{
                width: 100%;
                height: 480px;
                border-radius: 10px;
                background: radial-gradient(circle at 50% 50%, #16213e, #0f1117);
            }}
            .mv-note {{
                color:#64748b; font-size:0.8rem;
                text-align:center; margin-top:0.8rem;
            }}
            /* Fallback 3D CSS cube when no .glb provided */
            .cube-scene {{
                width:100%; height:380px;
                display:flex; align-items:center; justify-content:center;
                background: radial-gradient(circle at 50% 50%, #16213e, #0f1117);
                border-radius:10px; overflow:hidden;
            }}
            .cube-container {{
                perspective: 700px;
            }}
            .cube {{
                width:160px; height:160px;
                position:relative; transform-style:preserve-3d;
                animation: rotateCube 8s linear infinite;
            }}
            .cube-face {{
                position:absolute; width:160px; height:160px;
                border:2px solid #e9456060; opacity:0.92;
                overflow:hidden;
            }}
            .cube-face img {{ width:100%; height:100%; object-fit:cover; }}
            .front  {{ transform: translateZ(80px); }}
            .back   {{ transform: rotateY(180deg) translateZ(80px); }}
            .left   {{ transform: rotateY(-90deg) translateZ(80px); }}
            .right  {{ transform: rotateY(90deg) translateZ(80px); }}
            .top    {{ transform: rotateX(90deg) translateZ(80px); }}
            .bottom {{ transform: rotateX(-90deg) translateZ(80px); }}
            @keyframes rotateCube {{
                from {{ transform: rotateX(20deg) rotateY(0deg); }}
                to   {{ transform: rotateX(20deg) rotateY(360deg); }}
            }}
        </style>

        <div class="mv-wrapper">
            <div class="mv-title">🧊 Mô hình 3D — Hiện vật sau phục hồi</div>

            <!-- Thử load model-viewer với .glb mẫu -->
            <model-viewer
                src="https://modelviewer.dev/shared-assets/models/Astronaut.glb"
                environment-image="neutral"
                auto-rotate
                camera-controls
                poster="data:image/png;base64,{b64_restored}"
                alt="Mô hình 3D hiện vật phục hồi"
                shadow-intensity="1"
                ar
                ar-modes="webxr scene-viewer quick-look"
            >
                <!-- Fallback khi không load được .glb -->
                <div class="cube-scene" slot="poster">
                    <div class="cube-container">
                        <div class="cube">
                            <div class="cube-face front">
                                <img src="data:image/png;base64,{b64_restored}" />
                            </div>
                            <div class="cube-face back">
                                <img src="data:image/png;base64,{b64_restored}" />
                            </div>
                            <div class="cube-face left">
                                <img src="data:image/png;base64,{b64_restored}" />
                            </div>
                            <div class="cube-face right">
                                <img src="data:image/png;base64,{b64_restored}" />
                            </div>
                            <div class="cube-face top">
                                <img src="data:image/png;base64,{b64_restored}" />
                            </div>
                            <div class="cube-face bottom">
                                <img src="data:image/png;base64,{b64_restored}" />
                            </div>
                        </div>
                    </div>
                </div>
            </model-viewer>

            <div class="mv-note">
                💡 Demo dùng model 3D mẫu. Trong thực tế, ảnh phục hồi sẽ được dựng thành
                mô hình 3D qua photogrammetry (NeRF / Gaussian Splatting).
            </div>
        </div>
        """
        st.components.v1.html(model_viewer_html, height=570)

else:
    # Empty state
    st.markdown("""
    <div style='text-align:center; padding:4rem 2rem;
                background:#1e2130; border-radius:14px;
                border:2px dashed #2d3748; margin-top:1rem;'>
        <div style='font-size:3.5rem; margin-bottom:1rem;'>🏺</div>
        <div style='color:#94a3b8; font-size:1.1rem; font-weight:600;'>
            Chưa có ảnh nào được tải lên
        </div>
        <div style='color:#64748b; font-size:0.9rem; margin-top:0.5rem;'>
            Hãy upload ảnh hiện vật để bắt đầu quy trình phục hồi AI
        </div>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  FOOTER
# ─────────────────────────────────────────────
st.divider()
st.markdown("""
<div style='text-align:center; color:#475569; font-size:0.82rem; padding:1rem 0;'>
    🏛️ <b>Heritage Restoration AI</b> · Dự án Khoa học Kỹ thuật ·
    Được hỗ trợ bởi <b>Google Gemini</b> & <b>Streamlit</b><br>
    <span style='color:#334155'>
        Mọi dữ liệu được xử lý cục bộ và không lưu trữ trên server.
    </span>
</div>
""", unsafe_allow_html=True)
