# 🌌 PYUSD CyberMatrix Analytics Dashboard v2.0 🔗

[Visit 🧬PYUSD CyberMatrix Analytics Dashboard 🔗](http://pyusd-cybermatrix.streamlit.app) *(Note: Link might point to an older version)*

An advanced Streamlit dashboard providing real-time and historical analytics for PayPal USD (PYUSD) on the Ethereum blockchain, powered by Google Cloud Platform (GCP) Blockchain RPC. This enhanced version (v2.0) integrates a Google Gemini AI assistant, a NewsAPI feed with AI sentiment, extensive event tracking (Transfers, Mint, Burn, Approvals), network graph visualization, historical analysis capabilities, address tagging, a watchlist, and a conceptual simulation of bio-implant payments.

<img width="934" alt="Screenshot 2025-04-04 111427" src="https://github.com/user-attachments/assets/15647170-2e1f-4575-8db0-64e2e6cb3157" />

<img width="929" alt="Screenshot 2025-04-04 210617" src="https://github.com/user-attachments/assets/8f0934c1-65b2-4bc9-84fb-5b75757c34d3" />

*(Screenshots reflect the general layout of v1.x; specific data, AI responses, and new v2.0 features like network graphs/historical tabs will vary)*

## Features (v2.0)

*   **Live Event Feeds:** Displays recent PYUSD events from the blockchain (via GCP RPC):
    *   **Transfers:** Includes filtering options, address tagging, and optional auto-refresh.
    *   **Mint/Burn:** Tracks supply creation and destruction.
    *   **Approvals:** Monitors ERC20 approvals, highlighting unlimited allowances.
*   **Volume & Address Analysis:**
    *   Calculates PYUSD transfer volume over a block range.
    *   Visualizes top sender/receiver addresses (Pie Charts with Address Tagging).
    *   **Network Graph Visualization:** Interactive graph (using `pyvis`) showing PYUSD flow between addresses.
*   **Historical Analysis:** (RPC-Based) Analyze selected events (Transfer, Mint, etc.) over user-defined block ranges. **Warning:** Can be very slow and hit RPC limits for large ranges.
*   **Contract & Address Tools:**
    *   **Address Balance Checker:** Look up the current PYUSD balance (accepts addresses or known labels).
    *   **Address Watchlist:** Add addresses to monitor their balances easily.
    *   **Contract State Display:** Shows basic public state like the contract owner (if function exists and ABI is correct).
*   **Blockchain Interaction:**
    *   **Transaction Lookup:** Fetch detailed information about a specific transaction hash.
    *   **Block Trace Explorer:** (Requires compatible GCP RPC) Inspect detailed execution steps within a block using `debug_traceBlock*`.
*   **AI Integration (Google Gemini):**
    *   **AI Assistant:** Chat about PYUSD, blockchain concepts, and the dashboard's features.
    *   **News Sentiment Analysis:** Basic sentiment (Positive/Neutral/Negative) shown alongside news items.
    *   **Data Summarization:** Generate AI summaries for volume analysis insights.
*   **News Feed (NewsAPI):** Displays recent news articles related to PYUSD, stablecoins, and blockchain.
*   **Implant Payment Simulation:** Conceptual demo of a PYUSD payment initiated via simulated bio-implant read. **(Does not execute real transactions)**.
*   **Data Export:** Download filtered transfer data, supply events, or historical analysis results as CSV files.
*   **Themed UI:** Custom "CyberMatrix" themed interface using Streamlit and custom CSS.

## Prerequisites

*   Python 3.8+
*   **Google Cloud Platform (GCP) Blockchain RPC Endpoint:** Access to an Ethereum Mainnet RPC endpoint. **The core blockchain features WILL NOT FUNCTION without a valid RPC endpoint.** ([Learn more about GCP Blockchain Node Engine](https://cloud.google.com/web3/blockchain-node-engine)). Ensure necessary APIs (e.g., `debug`) are enabled for full functionality.
*   **Google Gemini API Key:** Required for the AI Assistant, Sentiment Analysis, and Summarization features. Obtainable from Google AI Studio or Google Cloud Console.
*   **NewsAPI API Key:** Required for the News Feed feature. Obtainable from [newsapi.org](https://newsapi.org/).

## Setup & Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/MiChaelinzo/pyusd-cybermatrix-dashboard.git # Use the correct repo URL
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
    *   Ensure you have a `requirements.txt` file in the project root containing at least:
        ```txt
        # requirements.txt
        streamlit
        web3
        requests
        google-generativeai
        pandas
        plotly
        pyvis
        ```
    *   Install the requirements:
        ```bash
        pip install -r requirements.txt
        ```

4.  **Configure Secrets (API Keys & RPC Endpoint):**
    *   Create a directory named `.streamlit` in the root of your project folder (if it doesn't exist): `mkdir .streamlit`
    *   Inside `.streamlit`, create a file named `secrets.toml`.
    *   Add your credentials to `secrets.toml` with the following structure:

        ```toml
        # .streamlit/secrets.toml

        [gemini_api]
        api_key = "YOUR_ACTUAL_GEMINI_API_KEY"

        [rpc_config]
        endpoint = "YOUR_ACTUAL_GCP_RPC_ENDPOINT_URL"

        [newsapi]
        api_key = "YOUR_ACTUAL_NEWSAPI_ORG_KEY"
        ```

    *   Replace the placeholder values (`"YOUR_ACTUAL_..."`) with your real keys and endpoint URL.
    *   **SECURITY:** Ensure `.streamlit/secrets.toml` is listed in your `.gitignore` file:
        ```
        # .gitignore
        .streamlit/secrets.toml
        venv/
        *.pyc
        __pycache__/
        ```

## Running the Dashboard

Once dependencies are installed and secrets are configured, run the Streamlit application (assuming your main script is named `app.py` or similar - adjust if needed):

```streamlit run your_script_name.py # e.g., streamlit run chip_rpc_chat.py```

The dashboard should open automatically in your default web browser.

## Important Considerations

*   **GCP RPC Provider:** Performance and data availability depend heavily on your GCP RPC endpoint configuration and quotas. Ensure the necessary APIs/namespaces (`debug` for Block Trace) are enabled.
*   **🚨 ABI Verification:** The code uses standard definitions for `Mint`, `Burn`, `Approval` events and the `owner()` function. **You MUST verify these signatures against the actual deployed PYUSD contract's ABI on Etherscan.** If they differ, you need to update the `PYUSD_ABI_EXPANDED` list in the Python script for the corresponding features (Supply Events, Approvals, Contract State) to work correctly.
*   **🐢 Historical Analysis Performance:** The historical analysis feature uses direct RPC batching (`get_logs`). This is **extremely slow and resource-intensive** for large block ranges and may hit RPC node request limits or timeouts. Use with caution and prefer smaller ranges. Production solutions often use dedicated indexing services (e.g., BigQuery, Dune).
*   **API Keys & Costs:** The Gemini AI and News Feed features require valid API keys. Usage may incur costs based on Google Cloud / NewsAPI pricing tiers and usage limits. The increased use of AI features in v2.0 might increase costs compared to previous versions.
*   **Simulation:** The "Implant Simulation" is conceptual and does *not* execute real transactions.
*   **Caching:** Data is cached (`@st.cache_data`/`@st.cache_resource`) to improve performance. Use refresh buttons or wait for the cache TTL (Time To Live) to get fresh data. Modifications to cached function arguments (like adding underscores) affect cache invalidation.

## Disclaimer

This tool is for informational and educational purposes only. Interact with blockchain data at your own risk. AI responses are generated by Google Gemini and may require verification. Simulations are conceptual. Secure your API keys and RPC endpoint appropriately. The accuracy of event/state data depends on the correctness of the ABI definitions used in the code relative to the deployed contract.

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
