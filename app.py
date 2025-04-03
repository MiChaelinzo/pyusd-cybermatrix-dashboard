# -*- coding: utf-8 -*-
"""Enhanced PYUSD Analytics Dashboard 📊🔗"""

# --- Imports ---
import streamlit as st
from web3 import Web3
import json  # For pretty printing JSON output
import time  # For simulated delays
from datetime import datetime # For timestamp conversion
from requests.exceptions import HTTPError # Add this import at the top

# --- Early Configuration: MUST BE FIRST STREAMLIT COMMAND ---
st.set_page_config(
    page_title="PYUSD CyberMatrix 🔗",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="🧬" # Added a page icon
)

# --- Configuration ---
# IMPORTANT: Replace with your ACTUAL Ethereum RPC endpoint.
# It can be GCP, Infura, Alchemy, or any other provider.
# We are using the GCP URL format as requested, but functionality depends on a valid endpoint.
GCP_RPC_ENDPOINT = "" # **<<< MUST REPLACE WITH YOUR ACTUAL RPC ENDPOINT KEY >>>**

PYUSD_CONTRACT_ADDRESS_NON_CHECKSUM = "0x6c3ea9036406852006290770bedfcaba0e23a0e8"
SIMULATED_IMPLANT_ID = "implant_user_cyber_777" # Updated simulated implant ID

# **Expanded PYUSD ABI (Minimal + additions for info, balance)**
PYUSD_ABI_EXPANDED = [
    # Existing Transfer Event
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "from", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "to", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "value", "type": "uint256"},
        ],
        "name": "Transfer",
        "type": "event",
    },
    # Function to get name
    {
        "constant": True,
        "inputs": [],
        "name": "name",
        "outputs": [{"name": "", "type": "string"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    },
    # Function to get symbol
    {
        "constant": True,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    },
    # Function to get decimals
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    },
    # Function to get total supply
    {
        "constant": True,
        "inputs": [],
        "name": "totalSupply",
        "outputs": [{"name": "", "type": "uint256"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    },
    # Function to get balance of an address
    {
        "constant": True,
        "inputs": [{"name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    },
]


# --- Initialize Web3 Connection ---
@st.cache_resource # Cache the web3 connection
def get_web3_connection(rpc_endpoint):
    """Initializes Web3 connection using the provided RPC endpoint."""
    if not rpc_endpoint:
        print("❌ RPC Endpoint is missing in the configuration!")
        return None
    try:
        w3 = Web3(Web3.HTTPProvider(rpc_endpoint))
        if w3.is_connected():
            # Use st.info for connection success in the app if needed, print for console debug
            print(f"✅ Successfully connected via RPC endpoint: {rpc_endpoint[:20]}...") # Shorten endpoint in print
            return w3
        else:
            print(f"❌ Connection failed using endpoint: {rpc_endpoint[:20]}.... Check endpoint and network.")
            st.error(f"❌ Connection failed. Check RPC endpoint ({rpc_endpoint[:20]}...) and network.", icon="🚨")
            return None
    except Exception as e:
        print(f"❌ Error connecting to RPC ({rpc_endpoint[:20]}...): {e}")
        st.error(f"❌ Error connecting to RPC: {e}", icon="🔥")
        return None

w3 = get_web3_connection(GCP_RPC_ENDPOINT)

# Apply custom CSS (Includes CyberMatrix, bigger title, quantum colors, Roboto font etc.)
# (Using the enhanced CSS provided in the prompt)
st.markdown(
    """
<style>
    /* PASTE YOUR CSS HERE */
    /* --- Keep the full CSS block from your original code --- */
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Inconsolata:wght@300;400;700&display=swap'); /* Cyberpunk font */

    body {
        font-family: 'Orbitron', sans-serif;
        color: #99ffcc; /* Quantum Mint Green for text */
        background-color: #000000;
        cursor: url('data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAACXBIWXMAAAsTAAALEwEAmpwYAAAF7WlUWHRYTUw6Y29tLmFkb2JlLnhtcAAAAAAAPD94cGFja2V0IGJlZ2luPSLvu78iIGlkPSJXNU0wTXBDZWhpSHpyZVN6TlRjemtjOWQiPz4gPHg6eG1wbWV0YSB4bWxuczpxPSJhZG9iZTpuczptZXRhLyIgeDp4cXB0az0iQWRvYmUgWE1QIENvcmUgNS42LWMxNDUgNzkuMTYzNDk5LCAyMDE4LzA4LzEzLTE2OjQwOjIyICAgICAgICAiPiA8cmRmOlJERiB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDcvMjItcmRmLXN5bnRheC-ucyMiPiA8cmRmOkRlc2NyaXB0aW9uIHJkZjphYb3J1dD0iIiB4bWxuczp4bXA9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC8iIHhtbG5zOmRjPSJodHRwOi8vcHVybC5vcmcvZGMvZWxlbWVudHMvMS4xLyIgeG1eNz0iaHR0cDovL25zLmFkb2JlLmNvbS9waG90b3NvcC8xLjAvIiB4bWxuczp4XGPMT0iaHR0cDovL25zLmFkb2JlLnBvbS94YXAvMS4wL21tLyIgeG1eZTpzdEV2dD0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wL3NUeXBlL1Jlc291cmNlRXZlbnQjIiB4bXA6Q3JlYXRvclRvb2w9IkFkb2JlIFBob3Rvc2hvcCBDQyAyMDE5IChXaW5kb3dzKSIgeG1wOkNyZWF0ZURhdGU9IjIwMjMtMDYtMjJUMTU6NTE6MTgrMDI6MDAiIHhtcDpNb2RpZnlEYXRlPSIyMDIzLTA2LTIyVDE1OjUzOjA4KzAyOjAwIiB4bXA6TWV0YWRhdGFEYXRlPSIyMDIzLTA2LTIyVDE1OjUzOjA4KzAyOjAwIiBkYzpmb3JtYXQ9ImltYWdlL3BuZyIgcGhvdG9zaG9wOkNvbG9yTW9kZT0iMyIgcGhvdG9zaG9wOklDUFByb2ZpbGU9InNSR0IgSUVDNjE5NjYtMi4xIiB4bXBNTTpJbnN0YW5jZUlEPSJ4bXAuaWlkOmY3NDQ0OGZkLWE3MzUtY2Q0Zi05NjdiLWI2M2M5NWU3NjdjMCIsIHhtwE5NOkRvY3VtZW50SUQ9ImFkb2JlOmRvY2lkOnBob3Rvc2hvcDphOTEzZTkyNy1kODM3LWVmNDctYjdhMC02MjRjNzA1NzUyZTAiIHhtcE1NOk9yaWdpbmFsRG9jdW1lbnRJRD0ieG1wLmRpZDo3YzUzODExNi1iZDFjLTMwNGItODMyNy0wMjg5MzA0MjA3ZGMiPiA8eG1wTU06SGlzdG9yeT4gPHJkZjpTZXE+IDxyZGY6bGkgc3RFdnQ6YWN0aW9uPSJjcmVhdGVkIiBzdEV2dDppbnN0YW5jZUlEPSJ4bXAuaWlkOjdjNTM4MTIxNi1iZDFjLTMwNGItODMyNy0wMjg5MzA0MjA3ZGMiIHN0EvnQudoZW59IjIyMy0wNi0yMlQxNTo1MToxOCswMjowMCIgc3RFdnQ6c29mdHdhcmVBZ2VudD0iAWRvYmUgUGhvdG9zaG9wIENDIDIwMTkgKFdpbmRvd3MpIi8+IDxyZGY6bGkgc3RFdnQ6YWN0aW9uPSJzYXZlZCIgc3RFdnQ6aW5zdGFuY2VJRD0ieG1wLmlpZDpmNzQ0NDhmZC1hNzM1LWNkNGYtOTY3Yi1iNjNjOTVlNzY3YzAiIHN0RXZ0OndoZW59IjIyMy0wNi0yMlQxNTo1MzowOCswMjowMCIgc3RFdnQ6c29mdHdhcmVBZ2VudD0iAWRvYmUgUGhvdG9zaG9wIENDIDIwMTkgKFdpbmRvd3MpIiBzdEV2dDpjaGFuZ2VkPSIvIi8+IDwvcmRmOlNlcT4gPC94bXBNTTpIaXN0b3J5PiA8L3JkZjpEZXNjcmlwdGlvbj4gPC9yZGY6UkRGPjwvOnhtcG1ldGE+IDw/eHBhY2tldCBlbmQ9InIiPz7PB4oMAAACOUlEQVRYhe2XPWgUURSFv7lrl0AWJAYRROMPiBFsFNRCjKKdWImFWNlZKyKColUQsTUgWFpaKIJYiYUoQkQMKBgRVEKIoBLBnyIs2WyOxcyG2cnMzs4k2cLE0+y8N3Pvu+fNvfPeWElVuJLBOEvJzDpmds7MnGv3+TUze+5/+9s5d8aS5uG4mdmFRAJmNmlmxxK4b5jZqJldNbO+XMNKTw9r5+d5BEwsnxJWAsPAD2AXsBMYAxYz5gEGgVHgNLAWOAocAt4DvcAH4F6UZLrXwOMiw0sF0Av0AW3gBvAkEh8CrnjxRuCIlxNYBbQC8TDQAZaBd8Ai0PEJ54BPqcdLA/gD/PROzNtRwDPfbuA9cBR4DXwEvvoA7gPPgLfADHABOJTSfzNZ+LLZrr5+7TbduuV6slVmNuCcm41OO+6D+OJxfAS2AJsKglIWu4BNwPZkUHW/UrHevj7Vamk5VuWYmVkryTBVHaqK6n+U5wIUazdwz8w2F4inYMWKOVHaQBr9wDrgaNT/2hsCj9z8TpKRkqGqDhQYUEkH1Zcq6kNEotuqU6pNv4cO5AmobkHVpbRXYkRVG6qTqrOqj1SvqI6pTqs+9fF+1YZvtwrGOun7TvrxVzmuVHU9I4AV1T09fVX16BoYQHVviYAfQhAJQ9WJ3aodxcf6yPBKZNkwMZZuVHVQte0zWPVCYYMJTqk2VWt+rYbqjRUG8BvMuuqE6vdCAdSAb8AOoAN8BoYIWTILMz4BLgN/gQHC+Z7nP9RDDRWeMlXHAAAAAElFTkSuQmCC'), auto;
    }

    .stApp {
        /* background-image: url('https://www.transparenttextures.com/patterns/hexellence.png'); */ /* Subtle Hex Pattern */
        background-color: rgba(0, 5, 10, 0.9); /* Dark blue-black overlay */
         background: linear-gradient(rgba(0, 0, 0, 0.6), rgba(0, 0, 0, 0.9)),
                    url('https://i.imgur.com/530DGSL.png'); /* Keep the cyberpunk background with overlay */
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }

    .title {
        font-size: 60px; /* Slightly reduced title size for better balance */
        font-family: 'Orbitron', sans-serif;
        color: #00ffff; /* Cyan title color */
        text-align: center;
        text-shadow: 0 0 15px #00ffff, 0 0 30px #00ffff, 0 0 45px #00ffff, 0 0 60px #00ffff; /* Intense glow */
        animation: flicker 1.8s infinite alternate, glitch 1.2s infinite alternate; /* Slower, alternating animations */
        margin-bottom: 30px; /* Add space below title */
    }

     .cyber-matrix-title {
        font-family: 'Orbitron', sans-serif;
        font-size: 28px; /* Adjust size */
        color: #ccff00; /* Neon lime */
        text-shadow: 0 0 10px #ccff00, 0 0 20px #ccff00;
        animation: flicker-fast 1.2s infinite alternate, glitch-slow 2.5s infinite alternate;
        margin-bottom: 10px;
    }

    @keyframes flicker {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }

    @keyframes flicker-fast {
        0%, 100% { opacity: 0.9; }
        50% { opacity: 0.5; }
    }

    @keyframes glitch {
        0% { transform: skewX(0deg); text-shadow: 0 0 10px #00ffff, 0 0 20px #00ffff; }
        25% { transform: skewX(1deg); text-shadow: -2px 0 #99ffcc, 2px 2px #00ffff; }
        50% { transform: skewX(-1deg); text-shadow: 2px -2px #99ffcc, -2px 2px #00ffff; }
        75% { transform: skewX(0.5deg); text-shadow: -1px -1px #99ffcc, 1px -1px #00ffff; }
        100% { transform: skewX(0deg); text-shadow: 0 0 10px #00ffff, 0 0 20px #00ffff; }
    }

    @keyframes glitch-slow {
       0%, 100% { transform: skewX(0deg); text-shadow: 0 0 5px #ccff00, 0 0 10px #ccff00; }
        33% { transform: skewX(-0.5deg); text-shadow: -1px 0 #99ffcc, 1px 1px #ccff00; }
        66% { transform: skewX(0.5deg); text-shadow: 1px -1px #99ffcc, -1px 1px #ccff00; }
    }

    .stButton>button {
        font-family: 'Orbitron', sans-serif;
        color: #000000; /* Black text */
        background-color: #99ffcc; /* Quantum Mint Green background */
        border: 1px solid #00ffcc; /* Slightly darker border */
        box-shadow: 0 0 10px #99ffcc;
        transition: all 0.25s ease-out;
        padding: 8px 18px; /* Adjust padding */
        border-radius: 5px; /* Rounded corners */
        font-weight: bold;
    }

    .stButton>button:hover {
        background-color: #00ffff; /* Cyan hover background */
        color: #000000;
        box-shadow: 0 0 20px #00ffff, 0 0 40px #00ffff;
        transform: translateY(-2px); /* Lift effect */
    }
     .stButton>button:active {
        transform: translateY(0px); /* Press effect */
        box-shadow: 0 0 5px #00ffff;
     }

    h1, h2, h3, h4, h5, h6 {
        font-family: 'Orbitron', sans-serif;
        color: #ff9933; /* Quantum Orange */
        text-shadow: 0 0 6px #ff9933;
    }
    h1 { font-size: 2.5em; } /* Main headers */
    h2 { font-size: 1.8em; } /* Sub-headers */
    h3 { font-size: 1.4em; } /* Section headers */


    p, div, textarea, input, select, span, li, a, label { /* Target labels too */
        color: #b3ffe6; /* Lighter mint green for readability */
        font-family: 'Roboto', sans-serif; /* Roboto for general text */
        font-size: 1.05em; /* Slightly larger base font */
    }

    /* Input field styling */
    .stTextInput>div>div>input,
    .stTextArea>div>div>textarea,
    .stNumberInput>div>div>input {
        color: #99ffcc;
        background-color: rgba(0, 30, 20, 0.8); /* Darker, slightly green background */
        border: 1px solid #99ffcc;
        box-shadow: inset 0 0 8px rgba(153, 255, 204, 0.5); /* Softer inset glow */
        font-family: 'Inconsolata', monospace; /* Monospace for inputs */
        border-radius: 4px;
        padding: 10px;
    }

    .stTextInput>div>div>input:focus,
    .stTextArea>div>div>textarea:focus,
    .stNumberInput>div>div>input:focus {
        box-shadow: inset 0 0 10px #99ffcc, 0 0 10px #99ffcc;
        border-color: #ffffff; /* White border on focus */
    }

    /* Selectbox styling */
     .stSelectbox>div>div>div {
        color: #99ffcc;
        background-color: rgba(0, 30, 20, 0.8);
        border: 1px solid #99ffcc;
        border-radius: 4px;
        font-family: 'Roboto', sans-serif;
     }

    /* Ensure Dataframes have dark background */
    .stDataFrame {
        background-color: rgba(0, 0, 0, 0.5);
        border: 1px solid #99ffcc;
    }
    .stDataFrame thead th {
        background-color: #003322; /* Dark green header */
        color: #ccff00; /* Neon lime header text */
        font-family: 'Orbitron', sans-serif;
    }
    .stDataFrame tbody tr td {
        color: #b3ffe6; /* Lighter mint text for data */
        font-family: 'Inconsolata', monospace;
        border-color: #336655; /* Darker grid lines */
    }

    /* Sidebar styling */
    .stSidebar {
        background-color: rgba(0, 10, 5, 0.95); /* Very dark, slightly green sidebar */
        border-right: 2px solid #ccff00; /* Neon lime border */
        padding-top: 20px;
    }
    .stSidebar .stMarkdown h2, .stSidebar .stMarkdown h3 { /* Target markdown headers in sidebar */
        color: #ff9933; /* Quantum Orange headers */
        text-shadow: 0 0 5px #ff9933;
    }
    .stSidebar .stSelectbox>div>div>div, .stSidebar .stRadio>div>label {
        color: #00ffff; /* Cyan text */
        font-family: 'Roboto', sans-serif;
    }
    .stSidebar .cyber-matrix-title {
        margin-bottom: 20px; /* More space below title */
    }
    .stSidebar .stMetric { /* Style metrics in sidebar */
        background-color: rgba(0, 51, 34, 0.7); /* Dark green metric background */
        border-radius: 5px;
        padding: 10px;
        margin-bottom: 10px;
        border: 1px solid #009966;
    }
    .stSidebar .stMetric label { /* Metric label */
        color: #ff9933; /* Quantum Orange label */
        font-family: 'Orbitron', sans-serif;
        font-size: 0.9em;
    }
    .stSidebar .stMetric .stMetricValue { /* Metric value */
         color: #99ffcc; /* Quantum Mint value */
         font-size: 1.3em;
         font-family: 'Inconsolata', monospace;
    }
    .stSidebar p, .stSidebar li, .stSidebar a { /* General sidebar text */
        color: #b3ffe6;
        font-family: 'Roboto', sans-serif;
    }
    .stSidebar .stExpander { /* Style expanders */
         border: 1px solid #009966;
         border-radius: 4px;
         background-color: rgba(0, 30, 20, 0.8);
         margin-bottom: 10px;
    }
     .stSidebar .stExpander header {
         color: #ff9933; /* Quantum Orange header */
         font-family: 'Orbitron', sans-serif;
     }


    /* Code block styling */
    .stCodeBlock {
        border: 1px solid #99ffcc;
        box-shadow: 0 0 10px rgba(153, 255, 204, 0.3);
        background-color: rgba(0, 0, 0, 0.85) !important; /* Ensure dark background */
    }
     .stCodeBlock code {
          color: #99ffcc; /* Quantum Mint text */
          font-family: 'Inconsolata', monospace !important; /* Monospace font */
          font-size: 1em !important;
     }

    /* Custom divider */
    hr {
        border-top: 1px dashed #99ffcc; /* Dashed mint divider */
        opacity: 0.5;
    }

    /* Adjust info/success/error boxes */
     div[data-testid="stAlert"] {
        font-family: 'Roboto', sans-serif;
        border-radius: 5px;
        border-width: 2px;
        opacity: 0.95;
     }
     div[data-testid="stAlert"] > div[role="alert"] { /* Target inner alert box */
        display: flex;
        align-items: center;
     }
    /* Success */
    div[data-baseweb="alert"][role="alert"].st-ae {
        background-color: rgba(0, 80, 40, 0.8); /* Darker green success */
        border-color: #00ff88;
        color: #ccffcc; /* Lighter green text */
    }
    /* Info */
    div[data-baseweb="alert"][role="alert"].st-b7 {
        background-color: rgba(0, 50, 80, 0.8); /* Darker blue info */
        border-color: #00aaff;
        color: #cceeff; /* Lighter blue text */
    }
    /* Error */
    div[data-baseweb="alert"][role="alert"].st-b6 {
        background-color: rgba(100, 0, 20, 0.8); /* Darker red error */
        border-color: #ff4466;
        color: #ffcccc; /* Lighter red text */
    }
     /* Warning */
    div[data-baseweb="alert"][role="alert"].st-b5 {
        background-color: rgba(100, 80, 0, 0.8); /* Darker yellow warning */
        border-color: #ffcc00;
        color: #ffffcc; /* Lighter yellow text */
    }

</style>
    """,
    unsafe_allow_html=True,
)

# --- Global Variable for Contract (Initialized after Web3 connection) ---
pyusd_contract = None

# --- Initialize Contract (Only if Web3 connection is successful) ---
if w3:
    try:
        PYUSD_CONTRACT_ADDRESS = Web3.to_checksum_address(PYUSD_CONTRACT_ADDRESS_NON_CHECKSUM)
        pyusd_contract = w3.eth.contract(address=PYUSD_CONTRACT_ADDRESS, abi=PYUSD_ABI_EXPANDED)
        print(f"✅ PYUSD contract initialized at address: {PYUSD_CONTRACT_ADDRESS}")
    except Exception as e:
        st.error(f"🚨 **Contract Error:** Failed to initialize PYUSD contract: {e}")
        st.markdown(f"`Contract Address Attempted:` `{PYUSD_CONTRACT_ADDRESS_NON_CHECKSUM}`")
        w3 = None # Invalidate w3 object if contract fails to initialize
        st.stop()
else:
    st.error("🚨 **FATAL ERROR:** Failed to connect to Ethereum RPC endpoint. Dashboard cannot function. Please check the `GCP_RPC_ENDPOINT` variable in `app.py` and your network connection.")
    st.markdown("---")
    st.markdown("`Attempted Endpoint:`")
    st.code(GCP_RPC_ENDPOINT if GCP_RPC_ENDPOINT else "<Not Set>", language='text')
    st.stop() # Stop execution if no web3 connection


# --- Helper Functions (Blockchain Interaction) ---
# Make sure functions use the globally defined pyusd_contract and w3 objects
# Or pass them explicitly if needed, but global is fine for this structure

@st.cache_data(ttl=60) # Cache token info for 1 minute
def get_token_info(_contract):
    """Fetches basic information about the token."""
    if not _contract:
        return None
    try:
        name = _contract.functions.name().call()
        symbol = _contract.functions.symbol().call()
        decimals = _contract.functions.decimals().call()
        total_supply_raw = _contract.functions.totalSupply().call()
        total_supply = total_supply_raw / (10**decimals)
        return {"name": name, "symbol": symbol, "decimals": decimals, "total_supply": total_supply}
    except Exception as e:
        st.warning(f"⚠️ Could not fetch token info: {e}")
        return None

@st.cache_data(ttl=30) # Cache balance for 30 seconds
def get_address_balance(_contract, _address):
    """Fetches the PYUSD balance for a given address."""
    if not _contract:
        return None
    try:
        checksum_address = Web3.to_checksum_address(_address)
        token_data = get_token_info(_contract) # Fetch decimals again or pass them
        if not token_data:
             st.error("❌ Cannot get balance: Token info (decimals) unavailable.")
             return None
        decimals = token_data['decimals']
        balance_raw = _contract.functions.balanceOf(checksum_address).call()
        balance = balance_raw / (10**decimals)
        return balance
    except ValueError:
        st.error(f"❌ Invalid Ethereum address provided: {_address}")
        return None
    except Exception as e:
        st.warning(f"⚠️ Could not fetch balance for {_address}: {e}")
        return None

@st.cache_data(ttl=600) # Cache events for 10 minutes
def get_recent_transfer_events(_w3, _contract, num_blocks=20):
    """Fetches recent Transfer events within a block range."""
    if not _w3 or not _contract:
        return None
    try:
        latest_block = _w3.eth.block_number
        from_block = max(0, latest_block - num_blocks)
        to_block = latest_block
        transfer_events = _contract.events.Transfer.get_logs(from_block=from_block, to_block=to_block)
        # Sort by block number descending (most recent first)
        transfer_events.sort(key=lambda x: x['blockNumber'], reverse=True)
        return transfer_events
    except HTTPError as http_err: # Catch HTTP errors specifically
        st.error(f"❌ HTTP Error fetching Transfer events (Blocks {from_block}-{to_block}): {http_err}")
        try:
            # Attempt to log response body if available
            st.error(f"Response Content: {http_err.response.text}")
        except Exception:
            st.error("Could not retrieve response content.")
        return None
    except Exception as e:
        # Log other potential errors
        st.error(f"❌ Error fetching Transfer events (Blocks {from_block}-{to_block}): {e} (Type: {type(e).__name__})")
    return None

def calculate_transfer_volume(transfer_events, decimals):
    """Calculates total PYUSD volume from Transfer events."""
    if not transfer_events or decimals is None:
        return 0
    total_volume_raw = sum(event['args']['value'] for event in transfer_events)
    return total_volume_raw / (10**decimals)

@st.cache_data(ttl=300) # Cache trace for 5 minutes
def get_block_trace(_w3, block_identifier):
    """Fetches trace for a block using trace_block (if supported by RPC)."""
    if not _w3:
        return None
    st.info(f"ℹ️ Requesting trace_block for block: {block_identifier} (Requires RPC support)")
    try:
        # Ensure block identifier is hex if it's a number
        if isinstance(block_identifier, int):
            block_param = hex(block_identifier)
        else:
            # Validate 'latest', 'earliest', 'pending' or hash format
            if isinstance(block_identifier, str) and (block_identifier in ['latest', 'earliest', 'pending'] or (block_identifier.startswith('0x') and len(block_identifier) == 66)):
                 block_param = block_identifier
            else:
                 st.error(f"❌ Invalid block identifier format: {block_identifier}")
                 return None

        block_trace_raw = _w3.provider.make_request("trace_block", [block_param])
        if 'result' in block_trace_raw:
            return block_trace_raw['result']
        elif 'error' in block_trace_raw:
            st.error(f"❌ RPC Error during trace_block: {block_trace_raw['error'].get('message', 'Unknown Error')} (Code: {block_trace_raw['error'].get('code', 'N/A')})")
            return None
        else:
             st.warning("⚠️ Unexpected response format from trace_block.")
             st.json(block_trace_raw) # Show raw response for debugging
             return None
    except Exception as e:
        st.error(f"❌ Exception during trace_block request: {e} (Type: {type(e).__name__})")
        st.warning("⚠️ Make sure your configured RPC endpoint supports the `trace_block` method.")
        return None

@st.cache_data(ttl=60) # Cache Tx details for 1 minute
def get_tx_details(_w3, tx_hash):
    """Fetches details for a specific transaction hash."""
    if not _w3:
        return None
    try:
        # Validate hash format first
        if not isinstance(tx_hash, str) or not tx_hash.startswith('0x') or len(tx_hash) != 66:
            st.error(f"❌ Invalid transaction hash format: {tx_hash}")
            return None

        tx = _w3.eth.get_transaction(tx_hash)
        if not tx:
            st.error(f"❌ Transaction not found: {tx_hash}")
            return None
        receipt = _w3.eth.get_transaction_receipt(tx_hash)
        if not receipt:
            st.warning(f"⚠️ Transaction {tx_hash} found but receipt is not yet available (likely pending).")
            # Return partial info if desired
            return {"Transaction Hash": tx_hash, "Status": "⏳ Pending", "From": tx['from'], "To": tx.get('to', 'Contract Creation?')}

        # Convert gas price and value from Wei
        gas_price_gwei = _w3.from_wei(tx['gasPrice'], 'gwei')
        value_eth = _w3.from_wei(tx['value'], 'ether') # Native ETH value, not PYUSD value
        tx_fee_eth = _w3.from_wei(receipt['gasUsed'] * tx['gasPrice'], 'ether')

        block = _w3.eth.get_block(receipt['blockNumber'])
        timestamp = datetime.utcfromtimestamp(block['timestamp']).strftime('%Y-%m-%d %H:%M:%S UTC') if block else "N/A"

        details = {
            "Transaction Hash": tx['hash'].hex(),
            "Status": "✅ Success" if receipt['status'] == 1 else "❌ Failed",
            "Block Number": receipt['blockNumber'],
            "Timestamp": timestamp,
            "From": tx['from'],
            "To": receipt.get('contractAddress') if receipt.get('contractAddress') else tx['to'], # Handle contract creation 'to'
            "Value (ETH)": f"{value_eth:.18f}",
            "Gas Used": receipt['gasUsed'],
            "Gas Limit": tx['gas'],
            "Gas Price (Gwei)": f"{gas_price_gwei:.6f}",
            "Transaction Fee (ETH)": f"{tx_fee_eth:.18f}",
            "Nonce": tx['nonce'],
            # "Input Data": tx['input'] # Often very long, uncomment if needed
        }
        return details
    except Exception as e:
        st.error(f"❌ Error fetching details for Tx Hash {tx_hash}: {e} (Type: {type(e).__name__})")
        return None

# --- Simulation Functions (Keep as is from original, minor text updates) ---
def simulate_nfc_read():
    st.info("🤖 Simulating NFC Implant Read...")
    time.sleep(1)
    return SIMULATED_IMPLANT_ID

def get_user_wallet_address(implant_id):
    st.info(f"🔑 Searching Neural-Link Database for Implant ID: {implant_id}...")
    time.sleep(0.5)
    # Simple simulation: map the specific implant ID to a dummy address
    # IMPORTANT: This is NOT secure, just a placeholder concept.
    wallet_map = {
        "implant_user_cyber_777": "0xUserSimulatedWalletAddressFromImplant777"
    }
    address = wallet_map.get(implant_id)
    if address:
        st.success(f"✅ Found associated wallet: {address[:10]}...")
    else:
        st.error(f"❌ Implant ID '{implant_id}' not found in simulated database.")
    return address # Returns None if not found

def simulate_transaction_creation(sender_wallet, recipient_wallet, amount_pyusd, _w3, _contract):
    st.info("🛠️ Compiling PYUSD Transfer Transaction...")
    time.sleep(1.5)
    try:
        current_gas_price = _w3.eth.gas_price if _w3 else 20 * 10**9 # Fallback
        nonce = _w3.eth.get_transaction_count(Web3.to_checksum_address(sender_wallet)) if _w3 and sender_wallet.startswith("0x") else "Simulated (Network Unavailable/Invalid Sender)"
    except Exception as e:
        st.warning(f"⚠️ Could not fetch live gas price/nonce: {e}. Using fallback.")
        current_gas_price = 20 * 10**9 # Fallback: 20 Gwei
        nonce = "Simulated (Error)"

    token_data = get_token_info(_contract)
    decimals = token_data['decimals'] if token_data else 6 # Fallback decimals

    # Simulate ABI encoding (basic approximation)
    transfer_function_signature = "a9059cbb"
    to_address_padded = recipient_wallet[2:].lower().zfill(64)
    amount_int = int(amount_pyusd * (10**decimals))
    amount_hex_padded = f"{amount_int:x}".zfill(64)
    simulated_input_data = f"0x{transfer_function_signature}{to_address_padded}{amount_hex_padded}"


    transaction_details = {
        "From (User Implant Wallet)": sender_wallet,
        "To (Merchant Wallet)": recipient_wallet,
        "Contract": PYUSD_CONTRACT_ADDRESS,
        "Function Signature": f"transfer(address,uint256)",
        "Value (PYUSD)": f"{amount_pyusd:.{decimals}f}", # Use correct decimals
        "Value (Raw Units)": amount_int,
        "Estimated Gas Limit": 60000, # Typical for ERC20 transfer
        "Estimated Gas Price (Gwei)": f"{_w3.from_wei(current_gas_price, 'gwei'):.2f}" if _w3 else "N/A",
        "Nonce": nonce,
        "Simulated Input Data": simulated_input_data
    }
    return transaction_details

def simulate_gcp_trace_transaction(transaction_details):
    st.info("📡 Simulating RPC debug_traceTransaction via GCP endpoint...")
    time.sleep(2)
    # More detailed simulated trace including contract interaction
    # Based on the structure of debug_traceTransaction
    sim_gas_used = 48500 # Example gas usage
    trace_output_placeholder = {
        "gas": hex(transaction_details["Estimated Gas Limit"]),
        "failed": False, # Assume success for simulation
        "returnValue": "0x", # Successful transfer typically returns empty
        "structLogs": [
            {
                "pc": 0, "op": "PUSH1", "gas": hex(transaction_details["Estimated Gas Limit"] - 3), "gasCost": hex(3), "depth": 1,
                "stack": ["0x80"], "memory": [], "storage": {}, "comment": "Start execution"
            },
            # ... many steps omitted for brevity ...
            # Simulate reading balance/allowance (SLOAD)
            {
                "pc": 100, "op": "SLOAD", "gas": hex(sim_gas_used + 3000), "gasCost": hex(2100), "depth": 1,
                "stack": ["0x...sender...balance_slot..."], "memory": [], "storage": {}, "comment": "Read sender balance"
            },
            # Simulate writing new balance (SSTORE)
            {
                "pc": 120, "op": "SSTORE", "gas": hex(sim_gas_used + 1000), "gasCost": hex(5000), # Gas cost varies (e.g., zero to non-zero)
                 "depth": 1, "stack": ["0x...new_balance...", "0x...sender_balance_slot..."], "memory": [], "storage": {}, "comment": "Update sender balance"
             },
            # Simulate emitting the Transfer event (LOG3 for indexed events)
            {
                "pc": 150, "op": "LOG3", "gas": hex(sim_gas_used + 500), "gasCost": hex(375 * 3 + 8 * 64), # Approx cost: 3 topics + data
                 "depth": 1,
                 "stack": [
                     "0x...memory_offset_for_data...", "0x...memory_size_for_data...", # Data location
                     "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef", # Transfer event signature hash
                     f"0x{transaction_details['From (User Implant Wallet)'][2:].lower().zfill(64)}", # from address (indexed)
                     f"0x{transaction_details['To (Merchant Wallet)'][2:].lower().zfill(64)}" # to address (indexed)
                 ],
                 "memory": ["0x...value_data..."], # Memory holding the non-indexed 'value' data
                 "storage": {"0x...": "0x..."}, # Shows storage state *after* this step (balances updated)
                 "comment": "Emit PYUSD Transfer Event (From, To, Value)"
            },
             {
                "pc": 160, "op": "RETURN", "gas": hex(sim_gas_used), "gasCost": hex(0), "depth": 1,
                "stack": [], "memory": [], "storage": {}, "comment": "Successful execution return"
             }
        ]
        # Omitting 'result' structure which might be specific to 'debug_traceTransaction' vs 'trace_block'
    }
    return trace_output_placeholder


# --- Streamlit App Layout ---
st.markdown("<h1 class='title'>🧬 PYUSD CyberMatrix Analytics 🔗</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; margin-bottom: 30px;'>Real-time insights & simulated bio-payments via Ethereum RPC</p>", unsafe_allow_html=True)

# --- Display Connection Status ---
if w3 and pyusd_contract:
    st.success(f"✅ Connected to Ethereum via RPC and PYUSD contract initialized ({PYUSD_CONTRACT_ADDRESS[:10]}...).", icon="🔌")
else:
    # Error messages are already displayed during failed connection/initialization
    # Optional: Add a final reminder here if needed
    # st.error("Dashboard is non-functional due to connection/contract issues.", icon="🚫")
    st.stop() # Stop here if essential components failed


# --- Sidebar ---
with st.sidebar:
    st.markdown("<h2 class='cyber-matrix-title'>🟢 System Status & Info</h2>", unsafe_allow_html=True)

    # Fetch token info once (it's cached)
    token_info = get_token_info(pyusd_contract)

    if token_info:
        st.metric(label="Token Name", value=token_info['name'])
        st.metric(label="Symbol", value=f"${token_info['symbol']}")
        st.metric(label="Decimals", value=str(token_info['decimals']))
        st.metric(label="Total Supply", value=f"{token_info['total_supply']:,.{token_info['decimals']}f} ${token_info['symbol']}") # Use correct decimals
    else:
        st.warning("⚠️ Token info unavailable.")

    st.markdown("---") # Divider

    # Network Status
    try:
        latest_block_num = w3.eth.block_number
        gas_price = w3.eth.gas_price
        gas_price_gwei = w3.from_wei(gas_price, 'gwei')
        st.metric(label="⛽ Current Gas Price (Gwei)", value=f"{gas_price_gwei:.2f}")
        st.metric(label="🔗 Latest Block", value=f"{latest_block_num:,}")
    except Exception as e:
        st.warning(f"⚠️ Network status error: {e}")

    st.markdown("---")

    # Links and Info Expander
    with st.expander("📚 Resources & Links", expanded=False):
        st.markdown(f"- [PYUSD on Etherscan](https://etherscan.io/token/{PYUSD_CONTRACT_ADDRESS})", unsafe_allow_html=True)
        st.markdown("- [PayPal PYUSD Info](https://www.paypal.com/us/digital-wallet/pyusd)", unsafe_allow_html=True)
        st.markdown("- [GCP Blockchain RPC Docs](https://cloud.google.com/web3/blockchain-rpc)", unsafe_allow_html=True)
        st.markdown("- [Web3.py Documentation](https://web3py.readthedocs.io/)", unsafe_allow_html=True)
        st.markdown("- [Streamlit Documentation](https://docs.streamlit.io/)", unsafe_allow_html=True)
        st.markdown("- [GitHub Repo (Placeholder)](https://github.com/your-username/pyusd-cybermatrix-dashboard)") # Update later

    st.markdown("---")
    st.caption(f"© {datetime.now().year} CyberMatrix Corp. | Connected via RPC")


# --- Main Content Tabs ---
tab_list = [
    "📊 Live Transfers",
    "📈 Volume Analysis",
    "💰 Address Balance",
    "🧾 Transaction Lookup",
    "🔬 Block Trace",
    "💳 Implant Simulation"
]
tabs = st.tabs(tab_list)

# --- Tab 1: Real-time Transfers ---
with tabs[0]:
    st.header("📊 Live PYUSD Transfer Feed")
    st.markdown("Shows the most recent `Transfer` events logged by the PYUSD contract.")

    col1, col2 = st.columns([1, 3])
    with col1:
        num_recent_blocks_transfers = st.slider(
            "Blocks to Scan", min_value=1, max_value=5, value=5, step=10, # Increased range slightly
            key="transfer_blocks", help="Number of recent blocks to query for events. Larger ranges take longer and might hit RPC limits."
        )
        fetch_transfers = st.button("🔄 Refresh Feed", key="fetch_transfers")

    with col2:
        # Display placeholder or results area immediately
        results_placeholder_transfers = st.empty()
        results_placeholder_transfers.info("Click 'Refresh Feed' to fetch the latest transfers.")

        if fetch_transfers:
            results_placeholder_transfers.empty() # Clear placeholder
            with st.spinner(text=f"🛰️ Syncing... Querying {num_recent_blocks_transfers} blocks for PYUSD transfers..."):
                transfer_events = get_recent_transfer_events(w3, pyusd_contract, num_blocks=num_recent_blocks_transfers)

            if transfer_events is not None: # Check if fetch was successful (didn't return None on error)
                if transfer_events and token_info:
                    st.success(f"✅ Found {len(transfer_events)} PYUSD Transfer events in the last {num_recent_blocks_transfers} blocks.", icon=" L💻")
                    decimals = token_info['decimals']
                    event_data = []
                    timestamps = {} # Cache timestamps to reduce block lookups

                    with st.spinner("Fetching timestamps..."):
                        unique_blocks = sorted(list(set(event['blockNumber'] for event in transfer_events)), reverse=True)
                        for block_num in unique_blocks[:50]: # Limit lookups if too many unique blocks
                             try:
                                 if block_num not in timestamps:
                                     block = w3.eth.get_block(block_num)
                                     timestamps[block_num] = datetime.utcfromtimestamp(block['timestamp']).strftime('%Y-%m-%d %H:%M:%S UTC')
                             except Exception as e:
                                 print(f"Warn: Could not fetch timestamp for block {block_num}: {e}")
                                 timestamps[block_num] = "N/A" # Mark as N/A on error


                    for event in transfer_events[:50]: # Display max 50 events
                        block_ts = timestamps.get(event['blockNumber'], "N/A")

                        event_data.append({
                            "Timestamp": block_ts,
                            "Block": event['blockNumber'],
                            "Tx Hash": event['transactionHash'].hex(),
                            "From": event['args']['from'],
                            "To": event['args']['to'],
                            f"Value ({token_info['symbol']})": event['args']['value'] / (10**decimals)
                        })
                    st.dataframe(event_data, hide_index=True, use_container_width=True)
                elif not token_info:
                     st.warning("⚠️ Cannot display values correctly, token decimal info missing.")
                else: # transfer_events is an empty list
                    st.info(f"ℹ️ No PYUSD Transfer events found in the last {num_recent_blocks_transfers} blocks.")
            else:
                st.error("❌ Failed to fetch transfer events. Check console/log for details.")


# --- Tab 2: Transfer Volume ---
with tabs[1]:
    st.header("📈 PYUSD Transfer Volume")
    st.markdown("Calculates the total value transferred over a specified block range.")

    col1_vol, col2_vol = st.columns([1, 2])
    with col1_vol:
        volume_blocks = st.slider(
            "Blocks for Volume Calc", min_value=1, max_value=5, value=5, step=10, # Wider range
            key="volume_blocks", help="Number of blocks to include in the volume calculation. Warning: Large ranges can be very slow or fail."
        )
        calc_volume = st.button("⚙️ Calculate Volume", key="calc_volume")

    with col2_vol:
        results_placeholder_volume = st.empty()
        results_placeholder_volume.info("Select a block range and click 'Calculate Volume'.")

        if calc_volume:
            results_placeholder_volume.empty() # Clear placeholder
            with st.spinner(text=f"⚙️ Aggregating transfer data over {volume_blocks} blocks..."):
                volume_events = get_recent_transfer_events(w3, pyusd_contract, num_blocks=volume_blocks)

            if volume_events is not None: # Check successful fetch
                if volume_events and token_info:
                    total_volume_pyusd = calculate_transfer_volume(volume_events, token_info['decimals'])
                    st.metric(
                        label=f"Total Volume ({token_info['symbol']}) | Last {volume_blocks} Blocks",
                        value=f"{total_volume_pyusd:,.{token_info['decimals']}f}" # Use correct decimals
                    )
                    st.caption(f"Based on {len(volume_events):,} transfer events found.")
                elif not token_info:
                    st.warning("⚠️ Cannot calculate volume, token decimal info missing.")
                else: # volume_events is empty list
                    st.info(f"ℹ️ No transfer events found in the last {volume_blocks} blocks to calculate volume.")
            else:
                 st.error("❌ Failed to fetch events for volume calculation. Check console/log for details.")


# --- Tab 3: Address Balance ---
with tabs[2]:
    st.header("💰 Check PYUSD Address Balance")
    st.markdown("Enter an Ethereum address to check its current PYUSD balance.")

    address_to_check = st.text_input("Ethereum Address (e.g., 0x...)", key="balance_address", placeholder="0x...")

    if st.button("Check Balance", key="check_balance_btn"):
        if address_to_check:
            # Basic validation (optional but good)
            if not Web3.is_address(address_to_check):
                 st.error(f"❌ Invalid Ethereum address format: {address_to_check}")
            elif token_info:
                with st.spinner(f"🔍 Querying balance for {address_to_check[:10]}..."):
                    checksum_addr = Web3.to_checksum_address(address_to_check) # Use checksummed internally
                    balance = get_address_balance(pyusd_contract, checksum_addr)

                if balance is not None:
                    st.metric(label=f"Balance for {checksum_addr}", value=f"{balance:,.{token_info['decimals']}f} ${token_info['symbol']}")
                # Error handled within get_address_balance now potentially including token info error
            else:
                 st.warning("⚠️ Cannot check balance, token decimal info missing.")
        else:
            st.warning("⚠️ Please enter an Ethereum address.")

# --- Tab 4: Transaction Lookup ---
with tabs[3]:
    st.header("🧾 Transaction Details Lookup")
    st.markdown("Enter a transaction hash to view its details.")

    tx_hash_lookup = st.text_input("Transaction Hash (e.g., 0x...)", key="tx_hash_lookup", placeholder="0x...")

    if st.button("🔍 Lookup Transaction", key="lookup_tx_btn"):
        if tx_hash_lookup:
             # Basic validation
            if not isinstance(tx_hash_lookup, str) or not tx_hash_lookup.startswith('0x') or len(tx_hash_lookup) != 66:
                st.error(f"❌ Invalid transaction hash format: {tx_hash_lookup}")
            else:
                with st.spinner(f"⏳ Fetching details for Tx {tx_hash_lookup[:10]}..."):
                    tx_details = get_tx_details(w3, tx_hash_lookup)

                if tx_details:
                    if tx_details.get("Status", "") == "⏳ Pending":
                         st.info("⏳ Transaction found but is still pending.")
                    elif tx_details.get("Status", "") == "✅ Success":
                         st.success("✅ Transaction details found:")
                    elif tx_details.get("Status", "") == "❌ Failed":
                         st.error("❌ Transaction failed.")
                    else:
                         st.info("ℹ️ Transaction details retrieved.") # Generic case

                    # Display details nicely using st.expander or columns
                    details_expander = st.expander("Show Transaction Details", expanded=True)
                    with details_expander:
                        col_tx1, col_tx2 = st.columns(2)
                        for i, (key, value) in enumerate(tx_details.items()):
                            if i % 2 == 0:
                                col_tx1.text(f"{key}:")
                                col_tx1.code(f"{value}", language='text')
                            else:
                                col_tx2.text(f"{key}:")
                                col_tx2.code(f"{value}", language='text')

                    # Provide Etherscan link
                    st.markdown(f"\n👀 [View Transaction on Etherscan](https://etherscan.io/tx/{tx_hash_lookup})", unsafe_allow_html=True)
                # Else: Error is handled and displayed within get_tx_details
        else:
            st.warning("⚠️ Please enter a transaction hash.")


# --- Tab 5: Block Trace Example ---
with tabs[4]:
    st.header("🔬 Block Trace Explorer")
    st.markdown("Use the `trace_block` RPC method (if supported by your endpoint) to inspect execution traces within a block.")
    st.warning("⚠️ **Note:** `trace_block` can be slow, resource-intensive for the RPC node, and is **not supported by all RPC providers** (including many free tiers or public endpoints). It's often considered a debug method.")

    block_identifier_input = st.text_input(
        "Block Number or Hash (or 'latest', 'earliest', 'pending')",
        value="latest", key="trace_block_id",
        help="Enter a specific block number (integer), block hash (0x...), or symbolic name."
    )

    if st.button("🔬 Get Block Trace", key="get_trace_btn"):
        if block_identifier_input:
            # Simplified validation - let get_block_trace handle detailed checks
            block_param = block_identifier_input
            try:
                 # Try converting to int if it looks like a number
                 block_param = int(block_identifier_input)
            except ValueError:
                 # Keep as string if not a simple integer ('latest', '0x...', etc.)
                 block_param = block_identifier_input.lower() # Standardize symbolic names

            with st.spinner(f"⏳ Requesting trace for block '{block_identifier_input}'... (This may take a while)"):
                block_trace = get_block_trace(w3, block_param)

            if block_trace is not None: # Check for successful fetch (not None)
                if isinstance(block_trace, list) and len(block_trace) > 0:
                    st.success(f"✅ Trace received for block {block_identifier_input} ({len(block_trace)} execution steps found)")
                    collapsed = st.checkbox("Collapse JSON Output?", value=True, key="collapse_trace")
                    st.json(block_trace[:25], expanded=(not collapsed)) # Show first few trace items
                    if len(block_trace) > 25:
                        st.info(f"Showing first 25 trace entries out of {len(block_trace)}. Expand JSON above or download full trace.")

                    # Provide full data download option
                    try:
                        trace_json_string = json.dumps(block_trace, indent=2)
                        st.download_button(
                             label="📥 Download Full Trace (JSON)",
                             data=trace_json_string,
                             file_name=f"trace_block_{block_identifier_input}.json",
                             mime="application/json",
                         )
                    except Exception as json_e:
                        st.error(f"Error preparing trace for download: {json_e}")

                elif isinstance(block_trace, list) and len(block_trace) == 0:
                    st.info(f"ℹ️ Received empty trace list for block {block_identifier_input}. This might mean no relevant transactions or state changes occurred in that block, or an issue with the trace.")
                else:
                    st.warning(f"⚠️ Received unexpected trace data format for block {block_identifier_input}. Displaying raw output:")
                    st.json(block_trace) # Display whatever was returned
            # Else: Errors handled and displayed in get_block_trace
        else:
            st.warning("⚠️ Please enter a block identifier.")

# --- Tab 6: Simulated Implant Payment ---
with tabs[5]:
    st.header("💳 Simulate Bio-Implant Payment")
    st.markdown("Conceptual simulation of initiating a PYUSD payment via a biochip implant, using simulated RPC tracing. **This does not send a real transaction.**")
    st.info(f"Using simulated Implant ID: `{SIMULATED_IMPLANT_ID}` which maps to a hardcoded example wallet address in this script.", icon="🔬")

    col1_sim, col2_sim = st.columns(2)
    with col1_sim:
        merchant_wallet_address = st.text_input("Merchant Wallet Address", "0xMerchantSimWalletPYUSD", key="merchant_sim", placeholder="0x...")
        amount_pyusd_sim = st.number_input("Amount (PYUSD)", value=1.50, min_value=0.01, format="%.6f", key="amount_sim", help="Enter the amount of PYUSD to simulate sending.") # Allow more decimals

    with col2_sim:
        st.markdown("<br/>", unsafe_allow_html=True) # Add spacing
        # Disable button if Web3 connection isn't working or token info failed
        disable_sim_button = not w3 or not token_info
        button_tooltip = "Requires active Web3 connection and token info" if disable_sim_button else "Simulate payment authorization"

        if st.button("⚡ Tap Implant & Authorize Payment", key="simulate_pay_btn", disabled=disable_sim_button, help=button_tooltip):
            implant_id = simulate_nfc_read() # Step 1
            user_wallet = get_user_wallet_address(implant_id) # Step 2

            if user_wallet:
                # Basic validation for merchant address
                if not Web3.is_address(merchant_wallet_address):
                     st.error(f"❌ Invalid Merchant Wallet Address format: {merchant_wallet_address}")
                else:
                    checksum_merchant = Web3.to_checksum_address(merchant_wallet_address)
                    # Step 3: Simulate Transaction creation
                    transaction_details_sim = simulate_transaction_creation(user_wallet, checksum_merchant, amount_pyusd_sim, w3, pyusd_contract)
                    st.success("✅ Payment Authorization Sequence Simulated!")

                    with st.expander("Simulated Transaction Data (Pre-Sign)", expanded=True):
                         st.json(transaction_details_sim)

                    # Step 4: Simulate GCP Trace (based on the created tx details)
                    trace_output_sim = simulate_gcp_trace_transaction(transaction_details_sim)
                    with st.expander("Simulated RPC Trace Output (`debug_traceTransaction` style)", expanded=False):
                         st.code(json.dumps(trace_output_sim, indent=2), language="json")
                         st.caption("This trace is a simulation based on the transaction details above. It mimics the structure of a debug trace.")

            # Implicit else: Error message already shown by get_user_wallet_address if not found

    st.markdown("---")
    st.caption("Disclaimer: This is a purely conceptual simulation for demonstration purposes. No real assets are moved, and no real cryptographic signing occurs.")

# --- Footer ---
st.markdown("---")
st.markdown("<p style='text-align:center; font-size: 0.9em; opacity: 0.7;'>PYUSD CyberMatrix Dashboard v1.2</p>", unsafe_allow_html=True)



