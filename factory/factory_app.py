"""
SOFTWARE FACTORY - Streamlit UI
================================
Web interface for batch provisioning LAMP stack projects.

Run locally:
    streamlit run factory_app.py

Deploy to Railway:
    - Connect repo
    - Set root directory to: factory
    - Add environment variables
"""

import streamlit as st
import yaml
import json
import os
import asyncio
from datetime import datetime
from pathlib import Path

# Try to import factory controller
try:
    from scripts.factory_controller import (
        SoftwareFactory,
        FactoryConfig,
        Project
    )
    FACTORY_AVAILABLE = True
except ImportError:
    FACTORY_AVAILABLE = False

# Page config
st.set_page_config(
    page_title="Software Factory",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .stProgress > div > div > div > div {
        background-color: #00d26a;
    }
    .status-ready { color: #00d26a; font-weight: bold; }
    .status-warning { color: #ffa500; font-weight: bold; }
    .status-error { color: #ff4b4b; font-weight: bold; }
    .status-pending { color: #808080; }
    .status-running { color: #00bfff; font-weight: bold; }
    .metric-card {
        background: #1e1e1e;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #333;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables."""
    if "batch_data" not in st.session_state:
        st.session_state.batch_data = None
    if "batch_name" not in st.session_state:
        st.session_state.batch_name = None
    if "run_history" not in st.session_state:
        st.session_state.run_history = []
    if "current_run" not in st.session_state:
        st.session_state.current_run = None
    if "config_valid" not in st.session_state:
        st.session_state.config_valid = False


def check_config():
    """Check if required environment variables are set."""
    required = {
        "DIGITALOCEAN_API_KEY": os.getenv("DIGITALOCEAN_API_KEY", ""),
        "CLOUDFLARE_API_KEY": os.getenv("CLOUDFLARE_API_KEY", ""),
        "CLOUDFLARE_ZONE_ID": os.getenv("CLOUDFLARE_ZONE_ID", ""),
    }

    missing = [k for k, v in required.items() if not v]
    return missing


def render_sidebar():
    """Render the sidebar with configuration status."""
    with st.sidebar:
        st.title("🏭 Software Factory")
        st.caption("Batch LAMP Provisioning")

        st.divider()

        # Config status
        st.subheader("⚙️ Configuration")
        missing = check_config()

        if missing:
            st.error("Missing config:")
            for item in missing:
                st.write(f"  • {item}")
            st.session_state.config_valid = False
        else:
            st.success("✓ All keys configured")
            st.session_state.config_valid = True

        # Optional services
        st.divider()
        st.subheader("📡 Services")

        doppler = "✓" if os.getenv("DOPPLER_TOKEN") else "○"
        smtp = "✓" if os.getenv("SMTP_HOST") else "○"
        anthropic = "✓" if os.getenv("ANTHROPIC_API_KEY") else "○"

        st.write(f"{doppler} Doppler (secrets vault)")
        st.write(f"{smtp} SMTP (email)")
        st.write(f"{anthropic} Anthropic (Skyvern AI)")

        # Quick stats
        st.divider()
        st.subheader("📊 Stats")

        history_count = len(st.session_state.run_history)
        st.metric("Batches Run", history_count)

        if st.session_state.run_history:
            total_projects = sum(
                r.get("summary", {}).get("total", 0)
                for r in st.session_state.run_history
            )
            st.metric("Total Projects", total_projects)


def render_batch_upload():
    """Render batch file upload section."""
    st.subheader("📁 Batch File")

    col1, col2 = st.columns([2, 1])

    with col1:
        uploaded = st.file_uploader(
            "Upload batch YAML",
            type=["yaml", "yml"],
            help="Upload a batch definition file"
        )

        if uploaded:
            try:
                content = uploaded.read().decode()
                batch_data = yaml.safe_load(content)
                st.session_state.batch_data = batch_data
                st.session_state.batch_name = uploaded.name
                st.success(f"✓ Loaded: {uploaded.name}")
            except Exception as e:
                st.error(f"Invalid YAML: {e}")

    with col2:
        st.write("**Or use template:**")
        if st.button("📝 Create New Batch"):
            st.session_state.show_template_editor = True


def render_batch_preview():
    """Render preview of loaded batch."""
    if not st.session_state.batch_data:
        st.info("Upload a batch file to get started")
        return

    batch = st.session_state.batch_data
    projects = batch.get("projects", [])

    st.subheader(f"📋 Batch: {batch.get('batch_id', 'Unknown')}")

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Projects", len(projects))
    col2.metric("Created", batch.get("created", "N/A"))

    # Count regions
    regions = {}
    for p in projects:
        r = p.get("region", "nyc3")
        regions[r] = regions.get(r, 0) + 1
    col3.metric("Regions", len(regions))

    # Estimate cost
    est_cost = len(projects) * 6  # $6/droplet base
    col4.metric("Est. Monthly", f"${est_cost}")

    # Project table
    st.write("**Projects:**")

    table_data = []
    for p in projects:
        table_data.append({
            "ID": p.get("id", ""),
            "Name": p.get("name", ""),
            "Domain": p.get("domain", ""),
            "Client": p.get("client", ""),
            "Region": p.get("region", "nyc3"),
            "Size": p.get("server_size", "s-1vcpu-1gb"),
        })

    st.dataframe(
        table_data,
        use_container_width=True,
        hide_index=True
    )


def render_batch_editor():
    """Render batch template editor."""
    st.subheader("📝 Create New Batch")

    batch_id = st.text_input("Batch ID", value=f"batch-{datetime.now().strftime('%Y%m%d')}")

    st.write("**Add Projects:**")

    num_projects = st.number_input("Number of projects", min_value=1, max_value=20, value=5)

    projects = []
    for i in range(int(num_projects)):
        with st.expander(f"Project {i+1}", expanded=(i < 2)):
            col1, col2 = st.columns(2)

            with col1:
                proj_id = st.text_input(f"ID", value=f"project-{i+1:03d}", key=f"pid_{i}")
                name = st.text_input(f"Name", value="", key=f"pname_{i}")
                domain = st.text_input(f"Domain", value="", key=f"pdomain_{i}")

            with col2:
                client = st.text_input(f"Client", value="", key=f"pclient_{i}")
                region = st.selectbox(
                    f"Region",
                    ["nyc3", "sfo3", "lon1", "fra1", "ams3", "sgp1", "tor1"],
                    key=f"pregion_{i}"
                )
                size = st.selectbox(
                    f"Size",
                    ["s-1vcpu-1gb", "s-1vcpu-2gb", "s-2vcpu-4gb"],
                    key=f"psize_{i}"
                )

            if name and domain:
                projects.append({
                    "id": proj_id,
                    "name": name,
                    "domain": domain,
                    "client": client,
                    "region": region,
                    "server_size": size
                })

    if st.button("💾 Save Batch", type="primary"):
        if projects:
            batch_data = {
                "batch_id": batch_id,
                "created": datetime.now().strftime("%Y-%m-%d"),
                "status": "queued",
                "projects": projects
            }
            st.session_state.batch_data = batch_data
            st.session_state.batch_name = f"{batch_id}.yaml"
            st.success(f"✓ Created batch with {len(projects)} projects")

            # Show YAML for download
            yaml_str = yaml.dump(batch_data, default_flow_style=False)
            st.download_button(
                "📥 Download YAML",
                yaml_str,
                file_name=f"{batch_id}.yaml",
                mime="text/yaml"
            )
        else:
            st.warning("Add at least one complete project")


def render_run_controls():
    """Render factory run controls."""
    st.subheader("🚀 Run Factory")

    if not st.session_state.batch_data:
        st.warning("Load a batch file first")
        return

    if not st.session_state.config_valid:
        st.error("Configure required API keys first")
        return

    col1, col2, col3 = st.columns(3)

    with col1:
        parallel = st.slider("Parallel jobs", 1, 10, 5)

    with col2:
        dry_run = st.checkbox("Dry run (preview only)", value=True)

    with col3:
        st.write("")  # Spacer
        st.write("")
        run_btn = st.button(
            "🏭 Run Factory" if not dry_run else "👁️ Preview Run",
            type="primary",
            use_container_width=True
        )

    if run_btn:
        run_factory(dry_run=dry_run, parallel=parallel)


def run_factory(dry_run: bool = True, parallel: int = 5):
    """Execute the factory batch processing."""
    batch = st.session_state.batch_data
    projects = batch.get("projects", [])

    st.divider()
    st.subheader("📊 Factory Progress")

    if dry_run:
        st.info("🔍 DRY RUN - No actual changes will be made")

        # Simulate the run
        progress = st.progress(0)
        status_container = st.container()

        for i, project in enumerate(projects):
            progress.progress((i + 1) / len(projects))
            with status_container:
                st.write(f"✓ Would provision: {project['id']} - {project['domain']}")

        st.success(f"Dry run complete. {len(projects)} projects would be created.")

        # Show what would happen
        with st.expander("📋 Execution Plan"):
            for p in projects:
                st.markdown(f"""
                **{p['id']}**: {p['name']}
                - Domain: `{p['domain']}`
                - Region: {p.get('region', 'nyc3')}
                - Size: {p.get('server_size', 's-1vcpu-1gb')}
                - Steps: Provision → DNS → LAMP → DB → Deploy → SSL → Health Check
                """)

    else:
        # Actual run
        if not FACTORY_AVAILABLE:
            st.error("Factory controller not available. Check imports.")
            return

        st.warning("🏭 LIVE RUN - Creating actual resources...")

        progress = st.progress(0)
        log_container = st.container()

        # This would run the actual factory
        # For now, show placeholder
        st.info("Factory execution would start here...")
        st.code("""
# Actual execution:
config = FactoryConfig()
factory = SoftwareFactory(config)
result = asyncio.run(factory.process_batch(batch_data, parallel=parallel))
        """)


def render_history():
    """Render run history."""
    st.subheader("📜 Run History")

    if not st.session_state.run_history:
        st.info("No runs yet")
        return

    for i, run in enumerate(reversed(st.session_state.run_history)):
        with st.expander(f"Batch: {run.get('batch_id', 'Unknown')} - {run.get('completed_at', '')}"):
            summary = run.get("summary", {})

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total", summary.get("total", 0))
            col2.metric("Ready", summary.get("ready", 0))
            col3.metric("Warnings", summary.get("warnings", 0))
            col4.metric("Errors", summary.get("errors", 0))

            st.write(f"Duration: {run.get('elapsed_minutes', 0)} minutes")


def main():
    """Main application."""
    init_session_state()
    render_sidebar()

    # Main content
    st.title("🏭 Software Factory")
    st.caption("Batch provision LAMP stack projects - 10 at a time, 17 minutes")

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📁 Batch",
        "📝 Create",
        "🚀 Run",
        "📜 History"
    ])

    with tab1:
        render_batch_upload()
        st.divider()
        render_batch_preview()

    with tab2:
        render_batch_editor()

    with tab3:
        render_batch_preview()
        st.divider()
        render_run_controls()

    with tab4:
        render_history()

    # Footer
    st.divider()
    st.caption("Software Factory v1.0 | Assembly Line Automation")


if __name__ == "__main__":
    main()
