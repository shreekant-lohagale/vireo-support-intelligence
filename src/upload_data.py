from pathlib import Path
import tempfile

import streamlit as st


REQUIRED_FILES = {
    "tickets.csv",
    "agents.csv",
    "orders.csv",
    "products.csv",
}


def get_uploaded_data_dir():
    """
    Ask the user for the four required Vireo CSV files.

    Returns
    -------
    Path | None
        Temporary directory containing the uploaded files,
        or None until all required files are available.
    """

    st.subheader("Load Vireo Support Data")

    st.caption(
        "The raw assessment data is not stored in this public repository. "
        "Upload the four supplied CSV files to run the dashboard."
    )

    uploaded_files = st.file_uploader(
        "Upload tickets.csv, agents.csv, orders.csv and products.csv",
        type=["csv"],
        accept_multiple_files=True,
    )

    if not uploaded_files:
        return None

    uploaded_by_name = {file.name: file for file in uploaded_files}

    missing_files = REQUIRED_FILES - set(uploaded_by_name)

    if missing_files:
        st.warning(
            "Still required: "
            + ", ".join(sorted(missing_files))
        )
        return None

    temp_dir = Path(
        tempfile.mkdtemp(prefix="vireo_support_")
    )

    for filename in REQUIRED_FILES:
        destination = temp_dir / filename

        with destination.open("wb") as output_file:
            output_file.write(
                uploaded_by_name[filename].getbuffer()
            )

    st.success("All required datasets loaded.")

    return temp_dir