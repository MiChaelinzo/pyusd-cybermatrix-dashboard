# 🧬 PYUSD CyberMatrix Analytics Dashboard 🔗

A Streamlit dashboard providing real-time analytics for PayPal USD (PYUSD) on the Ethereum blockchain, featuring a conceptual simulation of bio-implant payments. This tool interacts directly with an Ethereum RPC endpoint to fetch live data.

![Cyberpunk Background](https://i.imgur.com/530DGSL.png) 

## Features

*   **Live Transfer Feed:** Displays the latest PYUSD `Transfer` events from the blockchain.
*   **Volume Analysis:** Calculates the total PYUSD transferred within a recent block range.
*   **Address Balance Checker:** Look up the current PYUSD balance of any Ethereum address.
*   **Transaction Lookup:** Fetch detailed information about a specific transaction hash.
*   **Block Trace Explorer:** (Requires compatible RPC) Inspect detailed execution steps within a specific block using `trace_block`.
*   **Implant Payment Simulation:** A conceptual demonstration of initiating a PYUSD payment via a simulated NFC bio-implant read, including simulated transaction creation and RPC tracing. **(Does not execute real transactions)**.
*   **Themed UI:** Custom "CyberMatrix" themed interface using Streamlit and custom CSS.

## Prerequisites

*   Python 3.8+
*   Access to an Ethereum Mainnet RPC endpoint (e.g., from Google Cloud Blockchain Node Engine, Infura, Alchemy, QuickNode, etc.). **This dashboard WILL NOT FUNCTION without a valid RPC endpoint.**

## Setup & Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/pyusd-cybermatrix-dashboard.git # Replace with your repo URL
    cd pyusd-cybermatrix-dashboard
    ```

2.  **Create and activate a virtual environment (Recommended):**
    ```bash
    python -m venv venv
    # On Windows:
    .\venv\Scripts\activate
    # On macOS/Linux:
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure RPC Endpoint:**
    *   Open the `app.py` file in a text editor.
    *   Locate the line: `GCP_RPC_ENDPOINT = ""`
    *   **Replace the empty string `""` with your actual Ethereum RPC endpoint URL.**
    *   Save the file.

    ```python
    # Example (replace with your REAL endpoint):
    GCP_RPC_ENDPOINT = "https://mainnet.infura.io/v3/YOUR_INFURA_PROJECT_ID"
    # or for GCP BNE:
    # GCP_RPC_ENDPOINT = "https://YOUR-ENDPOINT-ID.blockchainnodeengine.googleusercontent.com"
    ```
    **Security Note:** For better security, consider using environment variables or Streamlit secrets (`.streamlit/secrets.toml`) to manage your RPC endpoint instead of hardcoding it directly in `app.py`, especially if sharing the repository publicly.

## Running the Dashboard

Once configured, run the Streamlit application:

```bash
streamlit run app.py
```

The dashboard should open automatically in your web browser.

## Important Considerations

*   **RPC Provider:** The performance and availability of data (especially `trace_block`) heavily depend on your chosen Ethereum RPC provider and its capabilities/limitations. Some public or free endpoints might rate-limit requests or not support tracing methods.
*   **Simulation:** The "Implant Simulation" tab is purely conceptual and for demonstration purposes. It does *not* involve real cryptographic signing or broadcasting transactions to the network.
*   **Caching:** Data like token info, balances, and recent events are cached for short periods (defined in `@st.cache_data` / `@st.cache_resource` decorators) to improve performance and reduce RPC load. Refresh buttons or waiting out the cache TTL (Time To Live) will fetch new data.

## Disclaimer

This tool is provided for informational and educational purposes only. Interact with blockchain data at your own risk. The simulation features are conceptual and do not represent a functional payment system. Ensure your RPC endpoint is secured appropriately.
```

---

**Next Steps:**

1.  Create a folder named `pyusd-cybermatrix-dashboard`.
2.  Inside this folder, create the four files (`app.py`, `requirements.txt`, `.gitignore`, `README.md`) and paste the corresponding content into each.
3.  **Crucially, edit `app.py` and insert your actual `GCP_RPC_ENDPOINT`.**
4.  Open your terminal or command prompt, navigate into the `pyusd-cybermatrix-dashboard` folder.
5.  Initialize a Git repository: `git init`
6.  Add the files: `git add .`
7.  Commit the files: `git commit -m "Initial commit of PYUSD CyberMatrix Dashboard"`
8.  (Optional) Create a repository on GitHub (or GitLab/Bitbucket) and follow their instructions to link your local repository and push it:
    ```bash
    git remote add origin <your-remote-repo-url>
    git branch -M main
    git push -u origin main
    ```

The dashboard should open automatically in your web browser.

## Important Considerations

*   **RPC Provider:** The performance and availability of data (especially `trace_block`) heavily depend on your chosen Ethereum RPC provider and its capabilities/limitations. Some public or free endpoints might rate-limit requests or not support tracing methods.
*   **Simulation:** The "Implant Simulation" tab is purely conceptual and for demonstration purposes. It does *not* involve real cryptographic signing or broadcasting transactions to the network.
*   **Caching:** Data like token info, balances, and recent events are cached for short periods (defined in `@st.cache_data` / `@st.cache_resource` decorators) to improve performance and reduce RPC load. Refresh buttons or waiting out the cache TTL (Time To Live) will fetch new data.

## Disclaimer

This tool is provided for informational and educational purposes only. Interact with blockchain data at your own risk. The simulation features are conceptual and do not represent a functional payment system. Ensure your RPC endpoint is secured appropriately.
```

---

**Next Steps:**

1.  Create a folder named `pyusd-cybermatrix-dashboard`.
2.  Inside this folder, create the four files (`app.py`, `requirements.txt`, `.gitignore`, `README.md`) and paste the corresponding content into each.
3.  **Crucially, edit `app.py` and insert your actual `GCP_RPC_ENDPOINT`.**
4.  Open your terminal or command prompt, navigate into the `pyusd-cybermatrix-dashboard` folder.
5.  Initialize a Git repository: `git init`
6.  Add the files: `git add .`
7.  Commit the files: `git commit -m "Initial commit of PYUSD CyberMatrix Dashboard"`
8.  (Optional) Create a repository on GitHub (or GitLab/Bitbucket) and follow their instructions to link your local repository and push it:
    ```bash
    git remote add origin <your-remote-repo-url>
    git branch -M main
    git push -u origin main
    ```

# PYUSD Transaction Analytics Dashboard using GCP Blockchain RPC

**Project Name:** PYUSD Transaction Analytics Dashboard
**Team Name:** Cybears-Rangers

## Project Description

This project aims to provide real-time and historical analytics for PayPal's PYUSD stablecoin using Google Cloud Platform (GCP) services.  We leverage GCP's Blockchain RPC service to access Ethereum blockchain data and explore potential integration with Google BigQuery for historical analysis.

This is a submission for the StackUp Hackathon, focusing on the challenge to build innovative projects using GCP Blockchain RPC and PYUSD.

## Tech Stack

*   **GCP Blockchain RPC:** For accessing real-time Ethereum blockchain data.
*   **PayPal PYUSD:** The stablecoin we are analyzing.
*   **Google Colaboratory (or Jupyter Notebooks):** For interactive data analysis and demonstration.
*   **Python:**  Programming language used for data retrieval and analysis.
*   **(Optional) Google BigQuery:** For querying and analyzing historical blockchain data (potential future enhancement).
*   **(Optional) Google Sheets:** For exporting data and creating shareable reports (potential future enhancement).

## Setup Instructions

1.  **GCP Project Setup:**
    *   You'll need a Google Cloud Platform project. If you don't have one, create one [here](https://console.cloud.google.com/).
    *   **Enable the Blockchain RPC API:** Go to the [API Library](https://console.cloud.google.com/apis/library) in your GCP project and search for "Blockchain RPC API" and enable it.
    *   **(Optional - for BigQuery):** Enable the BigQuery API in your GCP project.
    *   **(Optional - for Google Sheets API):** Enable the Google Sheets API in your GCP project if you plan to use it.

2.  **Python Environment:**
    *   We recommend using Google Colaboratory ([https://colab.google/](https://colab.google/)) as it provides a pre-configured environment with Python and easy access to GCP services. You can also use your local Python environment if you prefer.
    *   **Install necessary Python libraries:** If using a local environment, you'll need to install libraries.  In Colab, you can run these in a cell:
        ```bash
        !pip install web3 google-cloud-bigquery  # Add other libraries as needed
        ```

3.  **GCP RPC Endpoint:**
    *   You will need to obtain a GCP Blockchain RPC endpoint.  Refer to the [GCP Blockchain RPC Quickstart](https://cloud.google.com/blockchain-rpc/docs/quickstart) for instructions on how to get your endpoint.
    *   **Important:**  You will need to replace `"YOUR_GCP_RPC_ENDPOINT"` placeholder in the code examples below with your actual endpoint.

4.  **(Optional - BigQuery Credentials):**
    *   If you plan to use BigQuery, you'll need to set up authentication.  Colab usually handles this automatically if you are logged in with your Google account associated with your GCP project.  For local environments, you might need to set up service account credentials.  See the [BigQuery documentation](https://cloud.google.com/bigquery/docs/authentication).

5.  **(Optional - Google Sheets API Credentials):**
    *   If you plan to export to Google Sheets, you'll need to set up Google Sheets API credentials.  Refer to the [Google Sheets API documentation](https://developers.google.com/sheets/api/quickstart/python).


## Usage Instructions

1.  **Open the `notebook/pyusd_analytics.ipynb` notebook in Google Colab.** (Or run the Python scripts if you create separate scripts).
2.  **Replace placeholders:**  Look for comments like `"# REPLACE WITH YOUR GCP RPC ENDPOINT"` in the notebook and update them with your actual GCP RPC endpoint and any other configuration details (like PYUSD contract address if needed, though it's already in the code example).
3.  **Run the notebook cells sequentially.** The notebook is designed to demonstrate basic interaction with the GCP Blockchain RPC and fetch PYUSD transaction data.
4.  **Explore and extend!** This is just a starting point.  Modify the notebook, add more analysis, integrate with BigQuery, create visualizations, etc., to build out your hackathon project based on the ideas and challenges outlined in the hackathon description.

## Future Enhancements

*   Integrate with Google BigQuery to analyze historical PYUSD data.
*   Develop interactive dashboards using libraries like Plotly or Dash.
*   Implement more advanced blockchain analysis techniques using GCP's computationally expensive methods.
*   Add user interface for easier interaction and data visualization.
*   Export data to Google Sheets for reporting and sharing.

## License

[MIT License](LICENSE) (or choose Apache 2.0 if you selected that)
