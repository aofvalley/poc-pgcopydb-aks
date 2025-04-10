import streamlit as st
import requests
import json
import os
from dotenv import load_dotenv
import pandas as pd
import time

# Load environment variables from .env file if it exists
load_dotenv()

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://85.210.78.177")
API_VERSION = "v1"  # Updated to match the actual API structure
API_ENDPOINT = f"{API_BASE_URL}/{API_VERSION}"

# Page configuration
st.set_page_config(
    page_title="pgcopydb Manager",
    page_icon="🐘",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Helper functions
def make_api_request(endpoint, method="GET", data=None, params=None):
    """Make a request to the pgcopydb API."""
    url = f"{API_ENDPOINT}/{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, params=params, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=30)
        else:
            return {"error": f"Unsupported method: {method}"}
            
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        return {"error": f"Connection error: Cannot connect to {url}. Is the API running?"}
    except requests.exceptions.Timeout:
        return {"error": f"Request timeout: The API at {url} is taking too long to respond."}
    except requests.exceptions.HTTPError as e:
        return {"error": f"HTTP error: {e}"}
    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}

def check_api_health():
    """Check if the API is available."""
    try:
        # Use the root endpoint to check health
        response = requests.get(f"{API_BASE_URL}", timeout=5)
        if response.status_code == 200:
            # Try to get additional info from /api/info if available
            try:
                info_response = requests.get(f"{API_ENDPOINT}/info", timeout=5)
                if info_response.status_code == 200:
                    return True, info_response.json()
            except:
                pass
            return True, {"status": "healthy", "pod": "API Server"}
        return False, {"status": "unhealthy", "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return False, {"status": "unhealthy", "error": str(e)}

# Sidebar
with st.sidebar:
    st.title("🐘 pgcopydb Manager")
    
    # API Connection Status
    st.subheader("API Connection")
    status, health_info = check_api_health()
    
    if status:
        st.success(f"✅ Connected to API: {health_info.get('pod', 'unknown pod')}")
        st.info(f"pgcopydb version: {health_info.get('pgcopydb_version', 'Unknown')}")
    else:
        st.error(f"❌ API not available: {health_info.get('error', 'Unknown error')}")
        st.warning(f"Check API URL: {API_ENDPOINT}")
    
    # Navigation
    st.subheader("Navigation")
    page = st.radio(
        "Select Operation",
        ["Home", "Clone Database", "Dump Database", "Restore Database", 
         "Copy Tables", "List Tables", "Monitor Jobs"]
    )

# Main content
st.title("pgcopydb Database Migration Tool")

# Home page
if page == "Home":
    st.header("Welcome to pgcopydb Manager")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("What is pgcopydb?")
        st.write("""
        pgcopydb is a tool that implements a fast database copy utility for PostgreSQL, 
        using a divide-and-conquer strategy to maximize the bandwidth of your source database server.
        
        This frontend provides a user-friendly interface for working with pgcopydb operations in AKS.
        """)
        
        if status:
            st.success("The pgcopydb API is running and ready to use!")
        else:
            st.error("The pgcopydb API is not available. Please check your connection settings.")
    
    with col2:
        st.subheader("Available Operations")
        st.markdown("""
        - **Clone Database**: Full database copy from source to target
        - **Dump Database**: Extract database schema, data, or roles
        - **Restore Database**: Restore from a dump to a target database
        - **Copy Tables**: Copy specific tables between databases
        - **List Tables**: Get a list of tables from a database
        - **Monitor Jobs**: Check the status of your running jobs
        """)
    
    st.subheader("Getting Started")
    st.info("Select an operation from the sidebar to begin.")

# Clone Database page
elif page == "Clone Database":
    st.header("Clone a PostgreSQL Database")
    st.write("Copy a complete database from source to target")
    
    with st.form("clone_form"):
        source_conn = st.text_input(
            "Source Connection String", 
            "postgresql://user:password@source-host:5432/dbname",
            help="PostgreSQL connection string for the source database"
        )
        
        target_conn = st.text_input(
            "Target Connection String", 
            "postgresql://user:password@target-host:5432/dbname",
            help="PostgreSQL connection string for the target database"
        )
        
        options = st.text_area(
            "Additional Options (one per line)", 
            "",
            help="Additional pgcopydb options, one option per line"
        )
        
        submit = st.form_submit_button("Start Clone Operation")
    
    if submit:
        if not source_conn.startswith("postgresql://") or not target_conn.startswith("postgresql://"):
            st.error("Connection strings must start with postgresql://")
        else:
            options_list = [opt.strip() for opt in options.split("\n") if opt.strip()]
            
            data = {
                "source": source_conn,
                "target": target_conn,
                "options": options_list
            }
            
            with st.spinner("Starting clone operation..."):
                result = make_api_request("clone", method="POST", data=data)
                
                if "error" in result:
                    st.error(f"Error: {result['error']}")
                else:
                    st.success(f"Clone job started successfully!")
                    st.json(result)
                    
                    # Save job ID for monitoring
                    if "job_id" in result:
                        if "recent_jobs" not in st.session_state:
                            st.session_state.recent_jobs = []
                        st.session_state.recent_jobs.append({
                            "job_id": result["job_id"],
                            "operation": "Clone",
                            "time": time.strftime("%H:%M:%S")
                        })
                    
                    st.info("You can monitor this job in the 'Monitor Jobs' section.")

# Dump Database page
elif page == "Dump Database":
    st.header("Dump a PostgreSQL Database")
    st.write("Extract database schema, data, and/or roles to a directory")
    
    with st.form("dump_form"):
        source_conn = st.text_input(
            "Source Connection String", 
            "postgresql://user:password@source-host:5432/dbname",
            help="PostgreSQL connection string for the source database"
        )
        
        dump_dir = st.text_input(
            "Dump Directory", 
            "/app/pgcopydb_files/backup",
            help="Directory where the dump will be stored"
        )
        
        dump_type = st.selectbox(
            "Dump Type",
            options=["full", "schema", "roles"],
            help="Type of dump to perform"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            no_role_passwords = st.checkbox("Don't include role passwords", value=False)
            skip_extensions = st.checkbox("Skip restoring extensions", value=False)
        
        with col2:
            snapshot = st.text_input("Use snapshot (optional)", "")
            filters_file = st.text_input("Filters file (optional)", "")
        
        table_options = st.radio(
            "Table Selection",
            ["All Tables", "Specific Tables", "Exclude Tables"]
        )
        
        if table_options == "Specific Tables":
            tables = st.text_area(
                "Tables to include (one per line)",
                "",
                help="List of specific tables to include"
            )
        elif table_options == "Exclude Tables":
            tables = st.text_area(
                "Tables to exclude (one per line)",
                "",
                help="List of tables to exclude"
            )
        else:
            tables = ""
        
        submit = st.form_submit_button("Start Dump Operation")
    
    if submit:
        if not source_conn.startswith("postgresql://"):
            st.error("Connection string must start with postgresql://")
        else:
            data = {
                "source": source_conn,
                "dir": dump_dir,
                "dump_type": dump_type,
                "no_role_passwords": no_role_passwords,
                "skip_extensions": skip_extensions
            }
            
            if snapshot:
                data["snapshot"] = snapshot
                
            if filters_file:
                data["filters_file"] = filters_file
                
            if table_options == "Specific Tables":
                data["tables"] = [t.strip() for t in tables.split("\n") if t.strip()]
            elif table_options == "Exclude Tables":
                data["exclude_tables"] = [t.strip() for t in tables.split("\n") if t.strip()]
                
            with st.spinner("Starting dump operation..."):
                result = make_api_request("pgcopydb/dump", method="POST", data=data)
                
                if "error" in result:
                    st.error(f"Error: {result['error']}")
                else:
                    st.success(f"Dump job started successfully!")
                    st.json(result)
                    
                    # Save job ID for monitoring
                    if "job_id" in result:
                        if "recent_jobs" not in st.session_state:
                            st.session_state.recent_jobs = []
                        st.session_state.recent_jobs.append({
                            "job_id": result["job_id"],
                            "operation": "Dump",
                            "time": time.strftime("%H:%M:%S")
                        })
                    
                    st.info("You can monitor this job in the 'Monitor Jobs' section.")

# Restore Database page
elif page == "Restore Database":
    st.header("Restore a PostgreSQL Database")
    st.write("Restore a database from a dump directory")
    
    with st.form("restore_form"):
        target_conn = st.text_input(
            "Target Connection String", 
            "postgresql://user:password@target-host:5432/dbname",
            help="PostgreSQL connection string for the target database"
        )
        
        restore_dir = st.text_input(
            "Dump Directory", 
            "/app/pgcopydb_files/backup",
            help="Directory where the dump is located"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            schema_only = st.checkbox("Schema Only", value=False)
        
        with col2:
            data_only = st.checkbox("Data Only", value=False)
        
        table_options = st.radio(
            "Table Selection",
            ["All Tables", "Specific Tables", "Exclude Tables"]
        )
        
        if table_options == "Specific Tables":
            tables = st.text_area(
                "Tables to restore (one per line)",
                "",
                help="List of specific tables to restore"
            )
        elif table_options == "Exclude Tables":
            tables = st.text_area(
                "Tables to exclude (one per line)",
                "",
                help="List of tables to exclude"
            )
        else:
            tables = ""
        
        submit = st.form_submit_button("Start Restore Operation")
    
    if submit:
        if not target_conn.startswith("postgresql://"):
            st.error("Connection string must start with postgresql://")
        else:
            data = {
                "target": target_conn,
                "dir": restore_dir,
                "schema_only": schema_only,
                "data_only": data_only
            }
                
            if table_options == "Specific Tables":
                data["tables"] = [t.strip() for t in tables.split("\n") if t.strip()]
            elif table_options == "Exclude Tables":
                data["exclude_tables"] = [t.strip() for t in tables.split("\n") if t.strip()]
            
            with st.spinner("Starting restore operation..."):
                result = make_api_request("restore", method="POST", data=data)
                
                if "error" in result:
                    st.error(f"Error: {result['error']}")
                else:
                    st.success(f"Restore job started successfully!")
                    st.json(result)
                    
                    # Save job ID for monitoring
                    if "job_id" in result:
                        if "recent_jobs" not in st.session_state:
                            st.session_state.recent_jobs = []
                        st.session_state.recent_jobs.append({
                            "job_id": result["job_id"],
                            "operation": "Restore",
                            "time": time.strftime("%H:%M:%S")
                        })
                    
                    st.info("You can monitor this job in the 'Monitor Jobs' section.")

# Copy Tables page
elif page == "Copy Tables":
    st.header("Copy Tables Between Databases")
    st.write("Copy specific tables from source to target database")
    
    with st.form("copy_form"):
        source_conn = st.text_input(
            "Source Connection String", 
            "postgresql://user:password@source-host:5432/dbname",
            help="PostgreSQL connection string for the source database"
        )
        
        target_conn = st.text_input(
            "Target Connection String", 
            "postgresql://user:password@target-host:5432/dbname",
            help="PostgreSQL connection string for the target database"
        )
        
        table_options = st.radio(
            "Table Selection",
            ["All Tables", "Specific Tables", "Exclude Tables"]
        )
        
        if table_options == "Specific Tables":
            tables = st.text_area(
                "Tables to copy (one per line)",
                "",
                help="List of specific tables to copy"
            )
        elif table_options == "Exclude Tables":
            tables = st.text_area(
                "Tables to exclude (one per line)",
                "",
                help="List of tables to exclude"
            )
        else:
            tables = ""
        
        submit = st.form_submit_button("Start Copy Operation")
    
    if submit:
        if not source_conn.startswith("postgresql://") or not target_conn.startswith("postgresql://"):
            st.error("Connection strings must start with postgresql://")
        else:
            data = {
                "source": source_conn,
                "target": target_conn
            }
                
            if table_options == "Specific Tables":
                data["tables"] = [t.strip() for t in tables.split("\n") if t.strip()]
            elif table_options == "Exclude Tables":
                data["exclude_tables"] = [t.strip() for t in tables.split("\n") if t.strip()]
            
            with st.spinner("Starting copy operation..."):
                result = make_api_request("/copy", method="POST", data=data)
                
                if "error" in result:
                    st.error(f"Error: {result['error']}")
                else:
                    st.success(f"Copy job started successfully!")
                    st.json(result)
                    
                    # Save job ID for monitoring
                    if "job_id" in result:
                        if "recent_jobs" not in st.session_state:
                            st.session_state.recent_jobs = []
                        st.session_state.recent_jobs.append({
                            "job_id": result["job_id"],
                            "operation": "Copy",
                            "time": time.strftime("%H:%M:%S")
                        })
                    
                    st.info("You can monitor this job in the 'Monitor Jobs' section.")

# List Tables page
elif page == "List Tables":
    st.header("List Database Tables")
    st.write("Get a list of tables from a PostgreSQL database")
    
    tab1, tab2 = st.tabs(["List All Tables", "Filter Tables"])
    
    # List all tables tab
    with tab1:
        with st.form("list_tables_form"):
            source_conn = st.text_input(
                "Connection String", 
                "postgresql://user:password@host:5432/dbname",
                help="PostgreSQL connection string for the database"
            )
            
            submit = st.form_submit_button("List Tables")
        
        if submit:
            if not source_conn.startswith("postgresql://"):
                st.error("Connection string must start with postgresql://")
            else:
                data = {
                    "connection_string": source_conn
                }
                
                with st.spinner("Fetching tables..."):
                    result = make_api_request("list-tables", method="POST", data=data)
                    
                    if "error" in result:
                        st.error(f"Error: {result['error']}")
                    else:
                        st.success(f"Found {result.get('count', 0)} tables")
                        
                        if result.get('tables'):
                            # Display as dataframe for better formatting
                            df = pd.DataFrame(result['tables'], columns=["Table Name"])
                            st.dataframe(df, use_container_width=True)
                            
                            # Add download button
                            st.download_button(
                                "Download Table List as CSV",
                                df.to_csv(index=False).encode('utf-8'),
                                "table_list.csv",
                                "text/csv",
                                key="download-csv"
                            )
    
    # Filter tables tab
    with tab2:
        with st.form("filter_tables_form"):
            source_conn = st.text_input(
                "Connection String", 
                "postgresql://user:password@host:5432/dbname",
                key="filter_conn",
                help="PostgreSQL connection string for the database"
            )
            
            filter_pattern = st.text_input(
                "Filter Pattern", 
                "%",
                help="SQL LIKE pattern for filtering tables"
            )
            
            submit = st.form_submit_button("Filter Tables")
        
        if submit:
            if not source_conn.startswith("postgresql://"):
                st.error("Connection string must start with postgresql://")
            else:
                data = {
                    "connection_string": source_conn,
                    "filter": filter_pattern
                }
                
                with st.spinner("Filtering tables..."):
                    result = make_api_request("filter-tables", method="POST", data=data)
                    
                    if "error" in result:
                        st.error(f"Error: {result['error']}")
                    else:
                        st.success(f"Found {result.get('count', 0)} tables matching pattern '{result.get('filter', '')}'")
                        
                        if result.get('tables'):
                            # Display as dataframe for better formatting
                            df = pd.DataFrame(result['tables'], columns=["Table Name"])
                            st.dataframe(df, use_container_width=True)
                            
                            # Add download button
                            st.download_button(
                                "Download Filtered Table List as CSV",
                                df.to_csv(index=False).encode('utf-8'),
                                "filtered_table_list.csv",
                                "text/csv",
                                key="download-filtered-csv"
                            )

# Monitor Jobs page
elif page == "Monitor Jobs":
    st.header("Monitor pgcopydb Jobs")
    
    # Initialize session state for job tracking if not exists
    if "recent_jobs" not in st.session_state:
        st.session_state.recent_jobs = []
        
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Recent Jobs")
        
        if st.session_state.recent_jobs:
            # Create a dataframe from recent jobs
            jobs_df = pd.DataFrame(st.session_state.recent_jobs)
            st.dataframe(jobs_df, use_container_width=True)
        else:
            st.info("No recent jobs found. Start a job to see it here.")
    
    with col2:
        st.subheader("Check Job Status")
        
        job_id = st.text_input("Job ID", 
                              placeholder="Enter job ID to check status",
                              help="Enter the job ID to check its status")
        
        check_button = st.button("Check Status")
        
        if check_button and job_id:
            with st.spinner("Checking job status..."):
                result = make_api_request(f"check-status/{job_id}")
                
                if "error" in result:
                    st.error(f"Error: {result['error']}")
                else:
                    status = result.get("status", "unknown")
                    
                    if status == "completed":
                        st.success("Job completed successfully")
                    elif status == "error":
                        st.error("Job failed")
                    elif status == "running":
                        st.warning("Job is still running")
                    else:
                        st.info(f"Job status: {status}")
                    
                    st.json(result)
    
    # Logs section
    st.subheader("Job Logs")
    
    log_job_id = st.text_input("Job ID for logs", 
                              placeholder="Enter job ID to view logs",
                              help="Enter the job ID to view its logs")
    
    view_logs_button = st.button("View Logs")
    
    if view_logs_button and log_job_id:
        with st.spinner("Fetching logs..."):
            result = make_api_request(f"logs/{log_job_id}")
            
            if "error" in result:
                st.error(f"Error: {result['error']}")
            else:
                st.text_area("Job Logs", result.get("logs", "No logs available"), height=300)
    
    # Execution logs
    st.subheader("All Execution Logs")
    
    if st.button("View All Execution Logs"):
        with st.spinner("Fetching execution logs..."):
            result = make_api_request("execution-logs")
            
            if "error" in result:
                st.error(f"Error: {result['error']}")
            else:
                st.text_area("Execution Logs", result.get("logs", "No logs available"), height=300)
