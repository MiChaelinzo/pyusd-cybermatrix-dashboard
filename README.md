# 🧬 PYUSD CyberMatrix Analytics Dashboard 🔗

[Visit PYUSD CyberMatrix](http://pyusd-cybermatrix.streamlit.app)

A Streamlit dashboard providing real-time analytics for PayPal USD (PYUSD) on the Ethereum blockchain, powered by Google Cloud Platform (GCP) Blockchain RPC. This enhanced version integrates a Google Gemini AI assistant and a NewsAPI feed, alongside a conceptual simulation of bio-implant payments.

<img width="934" alt="Screenshot 2025-04-04 111427" src="https://github.com/user-attachments/assets/15647170-2e1f-4575-8db0-64e2e6cb3157" />

<img width="929" alt="Screenshot 2025-04-04 210617" src="https://github.com/user-attachments/assets/8f0934c1-65b2-4bc9-84fb-5b75757c34d3" />

*(Screenshots reflect the general layout; specific data and AI responses will vary)*

## Features

*   **Live Transfer Feed:** Displays the latest PYUSD `Transfer` events from the blockchain (via GCP RPC).
*   **Volume & Address Analysis:** Calculates PYUSD transfer volume and visualizes top sender/receiver addresses within a recent block range (via GCP RPC).
*   **Address Balance Checker:** Look up the current PYUSD balance of any Ethereum address (via GCP RPC).
*   **Transaction Lookup:** Fetch detailed information about a specific transaction hash (via GCP RPC).
*   **Block Trace Explorer:** (Requires compatible GCP RPC) Inspect detailed execution steps within a specific block using `debug_traceBlock*`.
*   **AI Assistant:** Chat with Google Gemini about PYUSD, blockchain concepts, and the dashboard's features.
*   **News Feed:** Displays recent news articles related to PYUSD, stablecoins, and blockchain via NewsAPI.
*   **Implant Payment Simulation:** A conceptual demonstration of initiating a PYUSD payment via a simulated NFC bio-implant read, including simulated transaction creation and RPC tracing. **(Does not execute real transactions)**.
*   **Themed UI:** Custom "CyberMatrix" themed interface using Streamlit and custom CSS.

## Prerequisites

*   Python 3.8+
*   **Google Cloud Platform (GCP) Blockchain RPC Endpoint:** Access to an Ethereum Mainnet RPC endpoint. This dashboard is specifically designed with GCP's RPC in mind, but others might work. **The core blockchain features WILL NOT FUNCTION without a valid RPC endpoint.** ([Learn more about GCP Blockchain Node Engine](https://cloud.google.com/web3/blockchain-node-engine))
*   **Google Gemini API Key:** Required for the AI Assistant feature. Obtainable from Google AI Studio or Google Cloud Console.
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
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Secrets (API Keys & RPC Endpoint):**
    *   This application uses Streamlit Secrets for securely managing API keys and the RPC endpoint. **Do not hardcode them in `app.py`.**
    *   Create a directory named `.streamlit` in the root of your project folder (if it doesn't exist):
        ```bash
        mkdir .streamlit
        ```
    *   Inside the `.streamlit` directory, create a file named `secrets.toml`.
    *   Add your credentials to `secrets.toml` with the following structure:

        ```toml
        # .streamlit/secrets.toml

        [gemini_api]
        api_key = "YOUR_ACTUAL_GEMINI_API_KEY"  # Replace with your real Google AI Gemini key

        [rpc_config]
        endpoint = "YOUR_ACTUAL_GCP_RPC_ENDPOINT_URL" # Replace with your real GCP RPC endpoint URL

        [newsapi]
        api_key = "YOUR_ACTUAL_NEWSAPI_ORG_KEY" # Replace with your real NewsAPI key
        ```

    *   Replace the placeholder values (`"YOUR_ACTUAL_..."`) with your real keys and endpoint URL.
    *   **SECURITY:** Ensure the `.streamlit/secrets.toml` file is listed in your `.gitignore` file to prevent accidentally committing your secrets to version control. Create a `.gitignore` file in the project root if it doesn't exist and add the line:
        ```
        # .gitignore
        .streamlit/secrets.toml
        ```

## Running the Dashboard

Once dependencies are installed and secrets are configured, run the Streamlit application:

```bash
streamlit run app.py
```

The dashboard should open automatically in your default web browser.

## Important Considerations

*   **GCP RPC Provider:** The performance and availability of data (especially `debug_traceBlock*`) heavily depend on your GCP RPC endpoint configuration and potential quotas. Ensure the necessary APIs (`debug` namespace) are enabled if you intend to use the Block Trace feature.
*   **API Keys:** The Gemini AI and News Feed features require valid API keys configured in secrets. Usage of these APIs may be subject to third-party terms and potential costs associated with Google Cloud or NewsAPI usage limits.
*   **Simulation:** The "Implant Simulation" tab is purely conceptual and for demonstration purposes. It does *not* involve real cryptographic signing or broadcasting transactions to the network.
*   **Caching:** Data like token info, balances, and recent events are cached for short periods (defined in `@st.cache_data` / `@st.cache_resource` decorators) to improve performance and reduce RPC/API load. Refresh buttons or waiting out the cache TTL (Time To Live) will fetch new data.

## Disclaimer

This tool is provided for informational and educational purposes only. Interact with blockchain data at your own risk. The AI responses are generated by Google Gemini and may require verification. The simulation features are conceptual and do not represent a functional payment system. Ensure your API keys and RPC endpoint are secured appropriately.

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
