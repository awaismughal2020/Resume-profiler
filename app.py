import streamlit as st
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure page
st.set_page_config(
    page_title="CV Analysis Suite",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import your existing apps (we'll need to modify them slightly)
import importlib.util


def load_app_module(app_path, module_name):
    """Dynamically load an app module"""
    spec = importlib.util.spec_from_file_location(module_name, app_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# Password protection
def check_password():
    """Returns True if the user entered the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == os.getenv("CV_ANALYZER_PASSWORD", "Abc123!@#7"):
            st.session_state["authenticated"] = True
            del st.session_state["password"]
        else:
            st.session_state["authentication_failed"] = True

    if st.session_state.get("authenticated", False):
        return True

    st.markdown(
        """
        <div style='text-align: center; padding: 50px;'>
            <h1>CV Analysis Suite</h1>
            <p>Professional Resume Analysis & Enhancement Platform</p>
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
            placeholder="Enter access password"
        )

        if st.session_state.get("authentication_failed", False):
            st.error("Incorrect password. Please try again.")

    return False


def get_app_from_url():
    """Determine which app to show based on URL path"""
    try:
        # Get the current URL path
        query_params = st.experimental_get_query_params()

        # Check for app parameter in URL
        if "app" in query_params:
            app = query_params["app"][0]
            if app in ["cv-analyzer", "analyzer"]:
                return "analyzer"
            elif app in ["cv-enhancement", "enhancement"]:
                return "enhancement"

        # Check for page parameter (alternative routing)
        if "page" in query_params:
            page = query_params["page"][0]
            if page in ["analyzer", "cv-analyzer"]:
                return "analyzer"
            elif page in ["enhancement", "cv-enhancement"]:
                return "enhancement"

        # Default to dashboard
        return "dashboard"
    except:
        return "dashboard"


def main():
    if not check_password():
        return

    # Initialize session state for app selection
    if 'current_app' not in st.session_state:
        st.session_state.current_app = get_app_from_url()

    # Sidebar navigation
    with st.sidebar:
        st.title("Navigation")

        # App selector
        app_options = ["Dashboard", "CV Analyzer", "CV Enhancement"]
        app_mapping = {"Dashboard": "dashboard", "CV Analyzer": "analyzer", "CV Enhancement": "enhancement"}

        current_selection = "Dashboard"
        if st.session_state.current_app == "analyzer":
            current_selection = "CV Analyzer"
        elif st.session_state.current_app == "enhancement":
            current_selection = "CV Enhancement"

        selected_app = st.selectbox(
            "Choose Application:",
            app_options,
            index=app_options.index(current_selection),
            key="app_selector"
        )

        # Update session state when selection changes
        if app_mapping[selected_app] != st.session_state.current_app:
            st.session_state.current_app = app_mapping[selected_app]
            st.experimental_rerun()

        st.markdown("---")
        st.header("Quick Access")

        if st.button("🏠 Dashboard", help="Go to main dashboard"):
            st.session_state.current_app = "dashboard"
            st.experimental_rerun()

        if st.button("📊 CV Analyzer", help="Analyze uploaded CVs"):
            st.session_state.current_app = "analyzer"
            st.experimental_rerun()

        if st.button("✨ CV Enhancement", help="Enhance CVs with Q&A"):
            st.session_state.current_app = "enhancement"
            st.experimental_rerun()

        st.markdown("---")
        st.header("URL Routes")
        st.write("Access directly via:")
        st.code("?app=analyzer")
        st.code("?app=enhancement")

    # Main content area - show the selected app
    if st.session_state.current_app == "dashboard":
        show_dashboard()
    elif st.session_state.current_app == "analyzer":
        show_cv_analyzer()
    elif st.session_state.current_app == "enhancement":
        show_cv_enhancement()


def show_dashboard():
    """Show the main dashboard"""
    st.title("CV Analysis Dashboard")
    st.markdown("---")

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

        if st.button("Launch CV Analyzer", key="launch_analyzer", type="primary"):
            st.session_state.current_app = "analyzer"
            st.experimental_rerun()

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

        if st.button("Launch CV Enhancement", key="launch_enhancement", type="primary"):
            st.session_state.current_app = "enhancement"
            st.experimental_rerun()

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


def show_cv_analyzer():
    """Show the CV Analyzer app"""
    # Import and run the analyzer
    exec(open('streamlit_app.py').read())


def show_cv_enhancement():
    """Show the CV Enhancement app"""
    # Import and run the enhancement app
    exec(open('streamlit_app2.py').read())


if __name__ == "__main__":
    main()
