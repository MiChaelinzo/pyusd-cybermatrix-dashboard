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
