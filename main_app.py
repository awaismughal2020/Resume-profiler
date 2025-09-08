import streamlit as st
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure page
st.set_page_config(
    page_title="CV Analysis Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)


# Password protection
def check_password():
    """Returns True if the user entered the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == os.getenv("CV_ANALYZER_PASSWORD", "Abc123!@#7"):
            st.session_state["authenticated"] = True
            del st.session_state["password"]
        else:
            st.session_state["authenticated"] = False

    if st.session_state.get("authenticated", False):
        return True

    st.markdown(
        """
        <div style='text-align: center; padding: 50px;'>
            <h1>CV Analysis Dashboard</h1>
        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.text_input(
            "Password",
            type="password",
            on_change=password_entered,
            key="password",
            placeholder="Enter password"
        )
        if st.session_state.get("authenticated") == False:
            st.error("Incorrect password. Please try again.")

    return False


# Health check endpoint
@st.cache_data(ttl=30)
def check_service_health(port):
    """Check if a service is running"""
    try:
        response = requests.get(f"http://localhost:{port}/_stcore/health", timeout=5)
        return response.status_code == 200
    except:
        return False


# Main dashboard
def main():
    if not check_password():
        return

    st.title("CV Analysis Dashboard")
    st.markdown("---")

    # Sidebar with system info
    with st.sidebar:
        st.header("System Status")

        # Check service status
        cv_analyzer_status = check_service_health(8501)
        cv_enhancement_status = check_service_health(8502)

        if cv_analyzer_status:
            st.success("CV Analyzer: Online")
        else:
            st.error("CV Analyzer: Offline")

        if cv_enhancement_status:
            st.success("CV Enhancement: Online")
        else:
            st.error("CV Enhancement: Offline")

        st.markdown("---")
        st.header("Environment")

        api_key_set = bool(os.getenv("OPENAI_API_KEY"))
        if api_key_set:
            st.success("OpenAI API Key: Configured")
        else:
            st.warning("OpenAI API Key: Not Set")

        st.info(f"Password Protected: Yes")

    # Main content
    col1, col2 = st.columns(2)

    with col1:
        st.header("CV Analyzer")
        st.write("""
        **Primary Analysis Tool**

        - Upload PDF resumes for analysis
        - Generate comprehensive CV analysis reports  
        - Create targeted interview questions
        - Identify skills gaps and improvements
        - Export detailed analysis reports
        """)

        if cv_analyzer_status:
            st.success("Service is running")
            if st.button("Open CV Analyzer", key="analyzer_btn", type="primary"):
                st.markdown(
                    """
                    <script>
                    window.open('http://localhost:8501', '_blank');
                    </script>
                    """,
                    unsafe_allow_html=True
                )
                st.info("CV Analyzer should open in a new tab. If not, visit: http://localhost:8501")
        else:
            st.error("Service is offline")

    with col2:
        st.header("CV Enhancement")
        st.write("""
        **Resume Improvement Tool**

        - Answer detailed questions about experience
        - Generate enhanced resume versions
        - Address gaps identified in analysis
        - Improve quantification and impact statements
        - Create ATS-friendly formatted resumes
        """)

        if cv_enhancement_status:
            st.success("Service is running")
            if st.button("Open CV Enhancement", key="enhancement_btn", type="primary"):
                st.markdown(
                    """
                    <script>
                    window.open('http://localhost:8502', '_blank');
                    </script>
                    """,
                    unsafe_allow_html=True
                )
                st.info("CV Enhancement should open in a new tab. If not, visit: http://localhost:8502")
        else:
            st.error("Service is offline")

    # Workflow guide
    st.markdown("---")
    st.header("Recommended Workflow")

    workflow_cols = st.columns(4)
    with workflow_cols[0]:
        st.markdown("""
        **Step 1: Analysis**

        1. Upload CV to Analyzer
        2. Run comprehensive analysis
        3. Generate interview questions
        4. Download analysis report
        """)

    with workflow_cols[1]:
        st.markdown("""
        **Step 2: Enhancement**

        1. Copy analysis to Enhancement tool
        2. Paste generated questions
        3. Answer detailed questions
        4. Generate enhanced resume
        """)

    with workflow_cols[2]:
        st.markdown("""
        **Step 3: Review**

        1. Compare original vs enhanced
        2. Verify all improvements
        3. Download final resume
        4. Save Q&A data for records
        """)

    with workflow_cols[3]:
        st.markdown("""
        **Step 4: Deploy**

        1. Use enhanced resume for applications
        2. Prepare with interview questions
        3. Reference analysis for interviews
        4. Track application results
        """)

    # Direct links section
    st.markdown("---")
    st.header("Direct Access Links")

    link_col1, link_col2, link_col3 = st.columns(3)

    with link_col1:
        st.markdown("**CV Analyzer**: [http://localhost:8501](http://localhost:8501)")

    with link_col2:
        st.markdown("**CV Enhancement**: [http://localhost:8502](http://localhost:8502)")

    with link_col3:
        st.markdown("**Dashboard**: [http://localhost:8503](http://localhost:8503)")

    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666; padding: 20px;'>
            <p>CV Analysis Suite - All services running in single Docker container</p>
            <p>Ports: Analyzer (8501) | Enhancement (8502) | Dashboard (8503)</p>
        </div>
        """,
        unsafe_allow_html=True
    )


# Health endpoint for Docker health check
if __name__ == "__main__":
    # Add a simple health check route
    if len(st.query_params) > 0 and "health" in st.query_params:
        st.write("OK")
    else:
        main()
