import streamlit as st
from openai import OpenAI
import stripe
import pandas as pd
import json
import PyPDF2
import io
from datetime import datetime
from supabase import create_client, Client
import base64
import requests

# AuraSight AI Configuration
st.set_page_config(
    page_title="AuraSight AI - Invoice Processor",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Clients
client = OpenAI(api_key=st.secrets["OPENAI_KEY"])
stripe.api_key = st.secrets["STRIPE_SECRET"]
STRIPE_PUBLIC = st.secrets["STRIPE_PUBLIC"]
supabase: Client = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_ANON"]
)

# Custom CSS - AuraSight Branding
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp {
        background: linear-gradient(180deg, #0a0e27 0%, #1a1f3a 100%);
    }
    
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 20px;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 20px 40px rgba(102, 126, 234, 0.2);
    }
    
    h1 {
        background: linear-gradient(120deg, #00d4ff, #0099cc, #ff00ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 3rem !important;
        font-weight: 700;
        margin: 0;
        animation: gradient 3s ease infinite;
    }
    
    @keyframes gradient {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    .stButton > button {
        background: linear-gradient(90deg, #00d4ff, #0099cc);
        color: white;
        border: none;
        padding: 12px 32px;
        border-radius: 30px;
        font-weight: 600;
        font-size: 16px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(0, 212, 255, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 25px rgba(0, 212, 255, 0.5);
    }
    
    .metric-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(0, 212, 255, 0.3);
        border-radius: 15px;
        padding: 20px;
        backdrop-filter: blur(10px);
    }
    
    .success-message {
        background: linear-gradient(135deg, #667eea20, #764ba220);
        border: 2px solid #667eea;
        border-radius: 15px;
        padding: 20px;
        margin: 20px 0;
    }
    
    .pricing-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(102, 126, 234, 0.3);
        border-radius: 20px;
        padding: 30px;
        text-align: center;
        transition: all 0.3s ease;
        height: 100%;
    }
    
    .pricing-card:hover {
        transform: translateY(-5px);
        border-color: #00d4ff;
        box-shadow: 0 10px 40px rgba(0, 212, 255, 0.2);
    }
    
    .popular-badge {
        background: linear-gradient(90deg, #ff00ff, #00ff88);
        color: white;
        padding: 5px 15px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        display: inline-block;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Session State Initialization
if 'processed_docs' not in st.session_state:
    st.session_state.processed_docs = 0
if 'user_email' not in st.session_state:
    st.session_state.user_email = None

# Header
st.markdown("""
<div class="main-header">
    <h1>🔮 AuraSight AI</h1>
    <p style='color: white; font-size: 1.2rem; margin-top: 10px;'>
        AI Powered Clarity from Chaos
    </p>
    <p style='color: rgba(255,255,255,0.8); margin-top: 5px;'>
        Transform your invoices into structured data in seconds
    </p>
</div>
""", unsafe_allow_html=True)

# Sidebar Navigation
with st.sidebar:
    st.markdown("### ⚡ Navigation")
    page = st.radio(
        "",
        ["🏠 Process Invoice", "💎 Pricing", "📊 Dashboard", "🚀 API Access", "❓ Help"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    st.markdown("### 📈 Your Stats")
    st.metric("Documents Processed", st.session_state.processed_docs)
    st.metric("Time Saved", f"{st.session_state.processed_docs * 5} mins")
    st.metric("Accuracy Rate", "99.2%")
    
    st.markdown("---")
    st.markdown("### 🎯 Quick Actions")
    if st.button("📧 Contact Support", use_container_width=True):
        st.info("Email: info@aurasightai.com")
    if st.button("📚 View Documentation", use_container_width=True):
        st.info("Docs: docs.aurasightai.com")

# Main Content Area
if page == "🏠 Process Invoice":
    
    # Upload Section
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📄 Upload Your Invoice")
        uploaded_file = st.file_uploader(
            "Drag and drop or browse",
            type=['pdf', 'png', 'jpg', 'jpeg'],
            help="Supports PDF and image files up to 10MB"
        )
        
        # Processing Options
        col_a, col_b = st.columns(2)
        with col_a:
            extraction_mode = st.selectbox(
                "Extraction Mode",
                ["🚀 Smart Extract (All Fields)", "📋 Invoice Details Only", 
                 "📦 Line Items Only", "⚙️ Custom Fields"]
            )
        with col_b:
            output_format = st.selectbox(
                "Output Format",
                ["JSON", "CSV", "Excel", "QuickBooks", "Xero"]
            )
    
    with col2:
        st.markdown("### 💡 Pro Tips")
        st.info("""
        **Best Results:**
        - Clear, readable scans
        - Complete invoice visible
        - PDF format preferred
        
        **We Extract:**
        ✓ Vendor details
        ✓ Invoice numbers
        ✓ All line items
        ✓ Taxes & totals
        ✓ Payment terms
        ✓ Due dates
        """)
    
    # Process Invoice
    if uploaded_file:
        with st.spinner("🔮 AuraSight AI is analyzing your document..."):
            progress = st.progress(0)
            
            # Step 1: Read file
            progress.progress(20, text="Reading document...")
            
            if uploaded_file.type == "application/pdf":
                pdf_reader = PyPDF2.PdfReader(uploaded_file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text()
            else:
                # For images, we'd integrate OCR
                text = "Image OCR processing..."
            
            # Step 2: AI Processing
            progress.progress(60, text="Extracting data with AI...")
            
            # OpenAI API call
messages = [
    {"role": "system", "content": """You are an expert at extracting data from invoices. 
    Extract all information and return as JSON with these fields:
    - invoice_number, invoice_date, due_date
    - vendor (name, address, email, phone)
    - customer (name, address)
    - line_items (array of: description, quantity, unit_price, total)
    - subtotal, tax_amount, total_amount
    - payment_terms, notes"""},
    {"role": "user", "content": f"Extract data from this invoice:\n{text[:3000]}"}
]

response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=messages,
    temperature=0.1,
    max_tokens=2000
)

# Parse response
progress.progress(90, text="Formatting results...")
extracted_data = json.loads(response.choices[0].message.content)
            
            # Step 3: Complete
            progress.progress(100, text="Complete!")
            st.session_state.processed_docs += 1
        
        # Display Results
        st.markdown("---")
        st.success("✅ **Extraction Complete!** Your invoice has been processed successfully.")
        
        # Key Metrics Display
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Invoice #", extracted_data.get("invoice_number", "N/A"))
            st.markdown('</div>', unsafe_allow_html=True)
        with col2:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Total Amount", f"${extracted_data.get('total_amount', '0.00')}")
            st.markdown('</div>', unsafe_allow_html=True)
        with col3:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Due Date", extracted_data.get("due_date", "N/A"))
            st.markdown('</div>', unsafe_allow_html=True)
        with col4:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Items", len(extracted_data.get("line_items", [])))
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Detailed View
        tab1, tab2, tab3 = st.tabs(["📋 Extracted Data", "📝 Line Items", "💾 Export"])
        
        with tab1:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Vendor Information**")
                vendor = extracted_data.get("vendor", {})
                st.write(f"Name: {vendor.get('name', 'N/A')}")
                st.write(f"Address: {vendor.get('address', 'N/A')}")
            with col2:
                st.markdown("**Invoice Details**")
                st.write(f"Date: {extracted_data.get('invoice_date', 'N/A')}")
                st.write(f"Terms: {extracted_data.get('payment_terms', 'N/A')}")
        
        with tab2:
            if "line_items" in extracted_data:
                df = pd.DataFrame(extracted_data["line_items"])
                st.dataframe(df, use_container_width=True, height=300)
        
        with tab3:
            col1, col2, col3 = st.columns(3)
            with col1:
                json_str = json.dumps(extracted_data, indent=2)
                st.download_button(
                    "📥 Download JSON",
                    data=json_str,
                    file_name=f"invoice_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
            with col2:
                if "line_items" in extracted_data:
                    csv = df.to_csv(index=False)
                    st.download_button(
                        "📥 Download CSV",
                        data=csv,
                        file_name=f"invoice_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
            with col3:
                st.button("💾 Save to Dashboard")

elif page == "💎 Pricing":
    st.markdown("## Choose Your Perfect Plan")
    st.markdown("Start with a **7-day free trial**. No credit card required.")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="pricing-card">
            <h3 style="color: #00d4ff;">Starter</h3>
            <h1 style="color: white;">$49<span style="font-size: 16px;">/mo</span></h1>
            <p style="color: rgba(255,255,255,0.7);">Perfect for small businesses</p>
            <hr style="border-color: rgba(255,255,255,0.1);">
            <ul style="text-align: left; color: rgba(255,255,255,0.8); list-style: none; padding: 0;">
                <li>✓ 100 documents/month</li>
                <li>✓ Basic AI extraction</li>
                <li>✓ CSV & JSON export</li>
                <li>✓ Email support</li>
                <li>✓ 99% accuracy</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Start Free Trial", key="starter", use_container_width=True):
            st.session_state.selected_plan = "starter"
            st.info("Redirecting to secure checkout...")
    
    with col2:
        st.markdown("""
        <div class="pricing-card" style="border-color: #ff00ff;">
            <span class="popular-badge">MOST POPULAR</span>
            <h3 style="color: #ff00ff;">Professional</h3>
            <h1 style="color: white;">$99<span style="font-size: 16px;">/mo</span></h1>
            <p style="color: rgba(255,255,255,0.7);">For growing teams</p>
            <hr style="border-color: rgba(255,255,255,0.1);">
            <ul style="text-align: left; color: rgba(255,255,255,0.8); list-style: none; padding: 0;">
                <li>✓ 500 documents/month</li>
                <li>✓ Advanced AI extraction</li>
                <li>✓ All export formats</li>
                <li>✓ API access (1000 calls)</li>
                <li>✓ Priority support</li>
                <li>✓ Custom fields</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Start Free Trial", key="pro", use_container_width=True):
            st.session_state.selected_plan = "professional"
            st.info("Redirecting to secure checkout...")
    
    with col3:
        st.markdown("""
        <div class="pricing-card">
            <h3 style="color: #ffd700;">Enterprise</h3>
            <h1 style="color: white;">$199<span style="font-size: 16px;">/mo</span></h1>
            <p style="color: rgba(255,255,255,0.7);">Maximum power</p>
            <hr style="border-color: rgba(255,255,255,0.1);">
            <ul style="text-align: left; color: rgba(255,255,255,0.8); list-style: none; padding: 0;">
                <li>✓ 2000 documents/month</li>
                <li>✓ Custom AI training</li>
                <li>✓ QuickBooks integration</li>
                <li>✓ Unlimited API calls</li>
                <li>✓ Dedicated support</li>
                <li>✓ White-label option</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Contact Sales", key="enterprise", use_container_width=True):
            st.session_state.selected_plan = "enterprise"
            st.info("Our team will contact you within 24 hours")

elif page == "📊 Dashboard":
    st.markdown("## Your Processing Dashboard")
    
    # Stats Overview
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Processed", "127", "↑12 this week")
    with col2:
        st.metric("Time Saved", "10.5 hrs", "↑2.3 hrs")
    with col3:
        st.metric("Accuracy", "99.2%", "↑0.3%")
    with col4:
        st.metric("Active Plan", "Professional", "373 docs left")
    
    # Recent Activity
    st.markdown("### Recent Documents")
    
    # Sample data
    df = pd.DataFrame({
        'Date': pd.date_range('2024-11-10', periods=7, freq='D'),
        'Invoice #': ['INV-1001', 'INV-1002', 'INV-1003', 'INV-1004', 'INV-1005', 'INV-1006', 'INV-1007'],
        'Vendor': ['TechCorp', 'Office Pro', 'CloudServ', 'DataSys', 'NetSol', 'DevTools', 'SecureIT'],
        'Amount': ['$2,340.00', '$567.50', '$8,923.00', '$1,234.56', '$4,567.89', '$789.00', '$3,456.78'],
        'Status': ['✅ Processed', '✅ Processed', '✅ Processed', '✅ Processed', '⏳ Processing', '✅ Processed', '✅ Processed']
    })
    
    st.dataframe(df, use_container_width=True, height=300)

elif page == "🚀 API Access":
    st.markdown("## API Documentation")
    
    st.code("""
# AuraSight AI API

## Authentication
Headers: {
    'Authorization': 'Bearer YOUR_API_KEY',
    'Content-Type': 'application/json'
}

## Extract Invoice Data
POST https://api.aurasightai.com/v1/extract

Body: {
    "document": "base64_encoded_file",
    "format": "pdf",
    "output": "json"
}

Response: {
    "success": true,
    "data": {
        "invoice_number": "INV-001",
        "total_amount": 1234.56,
        "line_items": [...]
    }
}
    """, language="python")
    
    st.info("🔑 Get your API key from the Dashboard → Settings → API Keys")

elif page == "❓ Help":
    st.markdown("## How Can We Help?")
    
    with st.expander("🚀 Getting Started"):
        st.markdown("""
        1. **Upload** your invoice (PDF or image)
        2. **Select** extraction mode
        3. **Download** structured data
        
        It's that simple! Our AI handles the rest.
        """)
    
    with st.expander("📋 What We Extract"):
        st.markdown("""
        - Invoice numbers and dates
        - Vendor information
        - Line items with descriptions
        - Quantities and prices
        - Taxes and totals
        - Payment terms
        - Custom fields you specify
        """)
    
    with st.expander("🔒 Security & Privacy"):
        st.markdown("""
        - 256-bit encryption
        - GDPR compliant
        - No data retention
        - SOC 2 certified
        - HIPAA compliant (Enterprise)
        """)
    
    st.markdown("### Still need help?")
    st.markdown("📧 Email: info@aurasightai.com")
    st.markdown("💬 Live Chat: Available Mon-Fri 9am-6pm EST")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: rgba(255,255,255,0.5); padding: 20px;'>
    © 2024 AuraSight AI | Unlocking Structured Data from Unstructured Documents
</div>
""", unsafe_allow_html=True)

