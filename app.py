
# -*- coding: utf-8 -*-
"""
Enhanced PYUSD CyberMatrix Analytics Dashboard v2.0 🌌🔗 powered by Google Cloud Blockchain RPC
Integrates News API, Visualizations, Gemini Chat & Feed, Historical Analysis,
Mint/Burn/Approval Tracking, Network Graph, Watchlist, AI Summaries & More!
(Based on v1.8 - Includes Features 1-12)
"""

# --- Imports ---
import streamlit as st
from web3 import Web3, exceptions as web3_exceptions # Added exceptions for specific handling
import json         # For pretty printing JSON output
import time         # For simulated delays and auto-refresh
from datetime import datetime, timezone, timedelta # For timestamp conversion and date ranges
import pandas as pd # For data manipulation
import plotly.express as px # For interactive charts
from collections import Counter # For counting addresses
import google.generativeai as genai # For Gemini Chat
import re           # For cleaning markdown
import requests     # For making HTTP requests (NewsAPI)
from requests.exceptions import HTTPError, RequestException # Error handling for RPC and API calls
import streamlit.components.v1 as components # For displaying pyvis graph HTML
from pyvis.network import Network # For Network Graph Visualization
import math # For ceiling function in batching

# --- Early Configuration: MUST BE FIRST STREAMLIT COMMAND ---
st.set_page_config(
    page_title="PYUSD CyberMatrix [GCP RPC + NewsAPI + Enhancements] 🔗 v2.0", # Updated version
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="🌌" # New Icon
)

# --- Configuration ---
# --- User MUST Configure These Using Streamlit Secrets ---
# Example structure in secrets.toml:
# [gemini_api]
# api_key = "YOUR_GEMINI_API_KEY"
# [rpc_config]
# endpoint = "YOUR_GOOGLE_CLOUD_BLOCKCHAIN_RPC_ENDPOINT"
# [newsapi]
# api_key = "YOUR_NEWSAPI_ORG_KEY"

# Fetch secrets with robust error handling
try:
    GEMINI_API_KEY = st.secrets["gemini_api"]["api_key"]
except (AttributeError, KeyError):
    st.error("🚨 **Config Error:** Gemini API Key (`gemini_api.api_key`) missing.", icon="⚙️")
    GEMINI_API_KEY = None

try:
    GCP_RPC_ENDPOINT = st.secrets["rpc_config"]["endpoint"]
    if not GCP_RPC_ENDPOINT: raise KeyError
    print("✅ Google Cloud Blockchain RPC Endpoint found.")
except (AttributeError, KeyError):
    st.error("🚨 **Config Error:** GCP Blockchain RPC Endpoint (`rpc_config.endpoint`) missing/empty. Blockchain features disabled.", icon="⚙️")
    GCP_RPC_ENDPOINT = None

try:
    NEWSAPI_API_KEY = st.secrets["newsapi"]["api_key"]
    if not NEWSAPI_API_KEY: raise KeyError
    print("✅ NewsAPI Key found.")
except (AttributeError, KeyError):
    st.error("🚨 **Config Error:** NewsAPI Key (`newsapi.api_key`) missing/empty. News Feed disabled.", icon="⚙️")
    NEWSAPI_API_KEY = None


PYUSD_CONTRACT_ADDRESS_NON_CHECKSUM = "0x6c3ea9036406852006290770bedfcaba0e23a0e8"
SIMULATED_IMPLANT_ID = "implant_user_cyber_777"
MAX_UINT256 = 2**256 - 1 # For checking unlimited approvals

# **Expanded PYUSD ABI**
# Added standard Mint, Burn, Approval events and owner function.
# !!! VERIFY THESE AGAINST ACTUAL PYUSD CONTRACT ABI ON ETHERSCAN !!!
PYUSD_ABI_EXPANDED = [
    # --- Core ERC20 Read Functions ---
    {"constant": True,"inputs": [],"name": "name","outputs": [{"name": "", "type": "string"}],"payable": False,"stateMutability": "view","type": "function"},
    {"constant": True,"inputs": [],"name": "symbol","outputs": [{"name": "", "type": "string"}],"payable": False,"stateMutability": "view","type": "function"},
    {"constant": True,"inputs": [],"name": "decimals","outputs": [{"name": "", "type": "uint8"}],"payable": False,"stateMutability": "view","type": "function"},
    {"constant": True,"inputs": [],"name": "totalSupply","outputs": [{"name": "", "type": "uint256"}],"payable": False,"stateMutability": "view","type": "function"},
    {"constant": True,"inputs": [{"name": "account", "type": "address"}],"name": "balanceOf","outputs": [{"name": "", "type": "uint256"}],"payable": False,"stateMutability": "view","type": "function"},
    # --- Standard View Function (Verify Existence) ---
    {"constant": True,"inputs": [],"name": "owner","outputs": [{"name": "", "type": "address"}],"payable": False,"stateMutability": "view","type": "function"},
    # --- Standard ERC20 Events (Verify Signatures) ---
    {"anonymous": False,"inputs": [{"indexed": True, "internalType": "address", "name": "from", "type": "address"},{"indexed": True, "internalType": "address", "name": "to", "type": "address"},{"indexed": False, "internalType": "uint256", "name": "value", "type": "uint256"}],"name": "Transfer","type": "event"},
    {"anonymous": False,"inputs": [{"indexed": True, "internalType": "address", "name": "owner", "type": "address"},{"indexed": True, "internalType": "address", "name": "spender", "type": "address"},{"indexed": False, "internalType": "uint256", "name": "value", "type": "uint256"}],"name": "Approval","type": "event"},
    # --- Common Mint/Burn Style Events (Verify Signatures & Parameters) ---
    # Note: PYUSD might use different event names or parameter names/types (e.g., 'minter', 'burner', 'amount')
    {"anonymous": False,"inputs": [{"indexed": True, "internalType": "address", "name": "to", "type": "address"},{"indexed": False, "internalType": "uint256", "name": "amount", "type": "uint256"}],"name": "Mint","type": "event"}, # Example Mint
    {"anonymous": False,"inputs": [{"indexed": True, "internalType": "address", "name": "from", "type": "address"},{"indexed": False, "internalType": "uint256", "name": "amount", "type": "uint256"}],"name": "Burn","type": "event"}, # Example Burn
    # --- Potentially Other State Functions (Add if needed and verified) ---
    # {"constant": True,"inputs": [],"name": "isPaused","outputs": [{"name": "", "type": "bool"}],"payable": False,"stateMutability": "view","type": "function"},
]

# --- System Instruction for Gemini ---
# Updated to reflect new features
SYSTEM_INSTRUCTION = f"""You are the PYUSD CyberMatrix AI Assistant v2.0, integrated into an advanced Streamlit dashboard.
The dashboard utilizes Google Cloud Platform's Blockchain RPC for Ethereum data and NewsAPI for news feeds.
Your purpose is to provide helpful and informative responses regarding PayPal USD (PYUSD), blockchain technology (especially Ethereum via GCP RPC), stablecoins, and relate answers back to the dashboard's functionalities.
Dashboard functionalities include:
- Viewing live PYUSD transfers, mints, burns, and approvals.
- Analyzing volume/addresses, including network graphs and address tagging.
- Checking balances and looking up transactions/blocks via GCP RPC.
- Historical analysis of PYUSD activity (RPC-based, potentially slow).
- Viewing blockchain/PYUSD news (from NewsAPI) with basic AI sentiment analysis.
- Simulating a bio-implant payment (conceptual).
- Checking contract state (e.g., owner).
- Maintaining an address watchlist.
- Providing AI summaries of displayed data.
Be concise, accurate, and maintain a helpful, cyberpunk/tech-focused tone consistent with the 'CyberMatrix' theme.
Do NOT invent information or transaction details. If asked about specific live data visible *only* on the dashboard (like current transfer feed details or a specific balance check result), explain that you don't have direct real-time access to the dashboard's *current state* but can explain *how* the user can find that information using the dashboard's tabs (which query GCP RPC or NewsAPI), or provide *general* information about PYUSD/blockchain based on your knowledge. You can also explain *how* to use features like the watchlist or historical analysis.
You can answer general questions about:
- PYUSD: How it works, issuer (Paxos/PayPal), backing, features, mint/burn mechanics, approvals.
- Ethereum: Blocks, transactions, gas, contracts, events, ERC-20, PoS. Explain data comes via GCP RPC.
- Stablecoins: Types, use cases, risks, regulations (informed by NewsAPI).
- Dashboard Tabs: Explain their function conceptually (Live Feeds, Analysis, Tools, Historical, Contract, News, Sim, Watchlist), noting reliance on GCP RPC and NewsAPI.
- AI Features: Explain the AI summary and news sentiment features (powered by Gemini).
Keep responses well-formatted using markdown.
Today's date is {datetime.now().strftime('%A, %B %d, %Y')}. Use this date for context.
"""

# --- Known Addresses for Tagging (Feature 6) ---
# Add more known addresses (exchanges, protocols, whales, PYUSD contract itself)
# Use checksummed addresses
KNOWN_ADDRESSES = {
    Web3.to_checksum_address("0x6c3ea9036406852006290770bedfcaba0e23a0e8"): "PYUSD Contract",
    # Add more like:
    # Web3.to_checksum_address("0x742d35Cc6634C0532925a3b844Bc454e4438f44e"): "Kraken Exchange",
    # Web3.to_checksum_address("0x...") : "Binance Exchange",
}

# --- Initialize Web3 Connection ---
@st.cache_resource
def get_web3_connection(rpc_endpoint):
    if not rpc_endpoint: return None
    print(f"Attempting connection via RPC: {rpc_endpoint[:30]}...")
    try:
        request_kwargs = {'timeout': 120} # Increased timeout for potentially longer calls like historical batching
        provider = Web3.HTTPProvider(rpc_endpoint, request_kwargs=request_kwargs)
        w3_instance = Web3(provider)
        if w3_instance.is_connected():
            print(f"✅ Successfully connected via Google Cloud Blockchain RPC: {rpc_endpoint[:30]}...")
            return w3_instance
        else:
            print(f"❌ Connection check failed for RPC: {rpc_endpoint[:30]}...")
            st.error(f"❌ Connection check failed. Verify GCP RPC Endpoint ({rpc_endpoint[:30]}...) & network.", icon="🚨")
            return None
    except Exception as e_connect:
        print(f"❌ Error connecting/checking GCP RPC ({rpc_endpoint[:30]}...): {e_connect}")
        st.error(f"❌ Error connecting/checking GCP RPC: {e_connect}", icon="🔥")
        return None

w3 = get_web3_connection(GCP_RPC_ENDPOINT)

# --- Apply Custom CSS ---
# >> CSS remains the same as in the provided code <<
st.markdown(
    """
<style>
    /* --- Global Font Imports --- */
     @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Inconsolata:wght@300;400;700&display=swap'); /* Cyberpunk font */

   /* --- Base Body & App Styling --- */
   body {
        font-family: 'Orbitron', sans-serif;
        color: #99ffcc; /* Quantum Mint Green for text */
        background-color: #000000;
        cursor: url('data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAACXBIWXMAAAsTAAALEwEAmpwYAAAF7WlUWHRYTUw6Y29tLmFkb2JlLnhtcAAAAAAAPD94cGFja2V0IGJlZ2luPSLvu78iIGlkPSJXNU0wTXBDZWhpSHpyZVN6TlRjemtjOWQiPz4gPHg6eG1wbWV0YSB4bWxuczpxPSJhZG9iZTpuczptZXRhLyIgeDp4cXB0az0iQWRvYmUgWE1QIENvcmUgNS42LWMxNDUgNzkuMTYzNDk5LCAyMDE4LzA4LzEzLTE2OjQwOjIyICAgICAgICAiPiA8cmRmOlJERiB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDcvMjItcmRmLXN5bnRheC-ucyMiPiA8cmRmOkRlc2NyaXB0aW9uIHJkZjphYb3J1dD0iIiB4bWxuczpxbXA9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC8iIHhtbG5zOmRjPSJodHRwOi8vcHVybC5vcmcvZGMvZWxlbWVudHMvMS4xLyIgeG1eNz0iaHR0cDovL25zLmFkb2JlLmNvbS9waG90b3NvcC8xLjAvIiB4bWxuczp4XGPMT0iaHR0cDovL25zLmFkb2JlLnBvbS94YXAvMS4wL21tLyIgeG1eZTpzdEV2dD0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wL3NUeXBlL1Jlc291cmNlRXZlbnQjIiB4bXA6Q3JlYXRvclRvb2w9IkFkb2JlIFBob3Rvc2hvcCBDQyAyMDE5IChXaW5kb3dzKSIgeG1wOkNyZWF0ZURhdGU9IjIwMjMtMDYtMjJUMTU6NTE6MTgrMDI6MDAiIHhtcDpNb2RpZnlEYXRlPSIyMDIzLTA2LTIyVDE1OjUzOjA4KzAyOjAwIiB4bXA6TWV0YWRhdGFEYXRlPSIyMDIzLTA2LTIyVDE1OjUzOjA4KzAyOjAwIiBkYzpmb3JtYXQ9ImltYWdlL3BuZyIgcGhvdG9zaG9wOkNvbG9yTW9kZT0iMyIgcGhvdG9zaG9wOklDUFByb2ZpbGU9InNSR0IgSUVDNjE5NjYtMi4xIiB4bXBNTTpJbnN0YW5jZUlEPSJ4bXAuaWlkOmY3NDQ0OGZkLWE3MzUtY2Q0Zi05NjdiLWI2M2M5NWU3NjdjMCIsIHhtwE5NOkRvY3VtZW50SUQ9ImFkb2JlOmRvY2lkOnBob3Rvc2hvcDphOTEzZTkyNy1kODM3LWVmNDctYjdhMC02MjRjNzA1NzUyZTAiIHhtcE1NOk9yaWdpbmFsRG9jdW1lbnRJRD0ieG1wLmRpZDo3YzUzODExNi1iZDFjLTMwNGItODMyNy0wMjg5MzA0MjA3ZGMiPiA8eG1wTU06SGlzdG9yeT4gPHJkZjpTZXE+IDxyZGY6bGkgc3RFdnQ6YWN0aW9uPSJjcmVhdGVkIiBzdEV2dDppbnN0YW5jZUlEPSJ4bXAuaWlkOjdjNTM4MTIxNi1iZDFjLTMwNGItODMyNy0wMjg5MzA0MjA3ZGMiIHN0EvnQudoZW59IjIyMy0wNi0yMlQxNTo1MToxOCswMjowMCIgc3RFdnQ6c29mdHdhcmVBZ2VudD0iAWRvYmUgUGhvdG9zaG9wIENDIDIwMTkgKFdpbmRvd3MpIi8+IDxyZGY6bGkgc3RFdnQ6YWN0aW9uPSJzYXZlZCIgc3RFdnQ6aW5zdGFuY2VJRD0ieG1wLmlpZDpmNzQ0NDhmZC1hNzM1LWNkNGYtOTY3Yi1iNjNjOTVlNzY3YzAiIHN0RXZ0OndoZW59IjIyMy0wNi0yMlQxNTo1MzowOCswMjowMCIgc3RFdnQ6c29mdHdhcmVBZ2VudD0iAWRvYmUgUGhvdG9zaG9wIENDIDIwMTkgKFdpbmRvd3MpIiBzdEV2dDpjaGFuZ2VkPSIvIi8+IDwvcmRmOlNlcT4gPC94bXBNTTpIaXN0b3J5PiA8L3JkZjpEZXNjcmlwdGlvbj4gPC9yZGY6UkRGPjwvOnhtcG1ldGE+IDw/eHBhY2tldCBlbmQ9InIiPz7PB4oMAAACOUlEQVRYhe2XPWgUURSFv7lrl0AWJAYRROMPiBFsFNRCjKKdWImFWNlZKyKColUQsTUgWFpaKIJYiYUoQkQMKBgRVEKIoBLBnyIs2WyOxcyG2cnMzs4k2cLE0+y8N3Pvu+fNvfPeWElVuJLBOEvJzDpmds7MnGv3+TUze+5/+9s5d8aS5uG4mdmFRAJmNmlmxxK4b5jZqJldNbO+XMNKTw9r5+d5BEwsnxJWAsPAD2AXsBMYAxYz5gEGgVHgNLAWOAocAt4DvcAH4F6UZLrXwOMiw0sF0Av0AW3gBvAkEh8CrnjxRuCIlxNYBbQC8TDQAZaBd8Ai0PEJ54BPqcdLA/gD/PROzNtRwDPfbuA9cBR4DXwEvvoA7gPPgLfADHABOJTSfzNZ+LLZrr5+7TbduuV6slVmNuCcm41OO+6D+OJxfAS2AJsKglIWu4BNwPZkUHW/UrHevj7Vamk5VuWYmVkryTBVHaqK6n+U5wIUazdwz8w2F4inYMWKOVHaQBr9wDrgaNT/2hsCj9z8TpKRkqGqDhQYUEkH1Zcq6kNEotuqU6pNv4cO5AmobkHVpbRXYkRVG6qTqrOqj1SvqI6pTqs+9fF+1YZvtwrGOun7TvrxVzmuVHU9I4AV1T09fVX16BoYQHVviYAfQhAJQ9WJ3aodxcf6yPBKZNkwMZZuVHVQte0zWPVCYYMJTqk2VWt+rYbqjRUG8BvMuuqE6vdCAdSAb8AOoAN8BoYIWTILMz4BLgN/gQHC+Z7nP9RDDRWeMlXHAAAAAElFTkSuQmCC'), auto;
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

    /* --- Title Styles --- */
    .title { /* Main Dashboard Title */
        font-size: 55px; /* Adjusted slightly */
        font-family: 'Orbitron', sans-serif;
        color: #00ffff; /* Cyan title color */
        text-align: center;
        text-shadow: 0 0 15px #00ffff, 0 0 30px #00ffff, 0 0 45px #00ffff, 0 0 60px #00ffff; /* Intense glow */
        animation: flicker 1.8s infinite alternate, glitch 1.2s infinite alternate; /* Slower, alternating animations */
        margin-bottom: 15px; /* Reduced space below title */
    }
    .gcp-subtitle { /* Subtitle specific to v1.8 */
        font-size: 18px;
        font-family: 'Roboto', sans-serif;
        color: #99ffcc;
        text-align: center;
        text-shadow: 0 0 5px #99ffcc;
        margin-bottom: 25px;
        opacity: 0.9;
     }
     .cyber-matrix-title { /* Used in sidebar and potentially elsewhere */
        font-family: 'Orbitron', sans-serif;
        font-size: 26px; /* Adjusted size */
        color: #ccff00; /* Neon lime */
        text-shadow: 0 0 10px #ccff00, 0 0 20px #ccff00;
        animation: flicker-fast 1.2s infinite alternate, glitch-slow 2.5s infinite alternate;
        margin-bottom: 10px;
    }
    .ai-assistant-title { /* Used for the Gemini chat title in sidebar */
        font-family: 'Orbitron', sans-serif;
        font-size: 1.4em;
        color: #ff9933; /* Quantum Orange */
        text-shadow: 0 0 6px #ff9933;
        margin-top: 20px;
        margin-bottom: 10px;
    }

    /* --- Animations --- */
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

    /* --- General Element Styling --- */
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
     /* Added Disabled Style */
      .stButton>button:disabled {
        background-color: rgba(100, 100, 100, 0.5);
        color: rgba(0, 0, 0, 0.7);
        border-color: rgba(150, 150, 150, 0.6);
        box-shadow: none;
        cursor: not-allowed;
     }
      .stButton>button:disabled:hover {
        background-color: rgba(100, 100, 100, 0.5); /* Prevent hover effects when disabled */
        color: rgba(0, 0, 0, 0.7);
        box-shadow: none;
        transform: none;
      }

    h1, h2, h3, h4, h5, h6 {
        font-family: 'Orbitron', sans-serif;
        color: #ff9933; /* Quantum Orange */
        text-shadow: 0 0 6px #ff9933;
    }
    /* Adjusted Header Sizes slightly */
    h1 { font-size: 2.4em; } /* Main headers */
    h2 { font-size: 1.7em; } /* Sub-headers */
    h3 { font-size: 1.3em; } /* Section headers */

    /* General text elements */
    p, div, textarea, input, select, span, li, a, label {
        color: #b3ffe6; /* Lighter mint green for readability */
        font-family: 'Roboto', sans-serif; /* Roboto for general text */
        font-size: 1.05em; /* Slightly larger base font */
    }
    /* Optional: Specific style for tab descriptions if needed */
    .tab-description {
       font-size: 0.95em;
       color: #99ccff; /* Light blue for description */
       margin-bottom: 15px;
       opacity: 0.9;
    }

    /* Input Fields */
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
    /* Optional: Hover effect for dataframe rows */
    .stDataFrame tbody tr:hover {
       background-color: rgba(0, 50, 40, 0.7) !important; /* Highlight row on hover */
    }

    /* --- >>> SIDEBAR STYLES (Restored from v1.3) <<< --- */
    .stSidebar {
        background-color: rgba(0, 10, 5, 0.95); /* Very dark, slightly green sidebar */
        border-right: 2px solid #ccff00; /* Neon lime border */
        padding-top: 20px;
    }
    .stSidebar .stMarkdown h2, .stSidebar .stMarkdown h3 { /* Target markdown headers in sidebar */
        color: #ff9933; /* Quantum Orange headers */
        text-shadow: 0 0 5px #ff9933;
        /* This will NOT affect .ai-assistant-title unless it's also an h2/h3 */
    }
    .stSidebar .stSelectbox>div>div>div, .stSidebar .stRadio>div>label { /* Sidebar controls */
        color: #00ffff; /* Cyan text */
        font-family: 'Roboto', sans-serif;
    }
    .stSidebar .cyber-matrix-title { /* Sidebar title */
        margin-bottom: 20px; /* More space below title */
        /* Inherits base .cyber-matrix-title styles */
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
    /* Keep v1.8 specific metric styling if needed */
     .stSidebar .stMetric label[for*="rpc-status"] { /* Style GCP RPC status label slightly */
        font-weight: bold; /* Example */
     }
    .stSidebar .stMetric .stMetricValue { /* Metric value */
         color: #99ffcc; /* Quantum Mint value */
         font-size: 1.3em;
         font-family: 'Inconsolata', monospace;
    }
    .stSidebar p, .stSidebar li, .stSidebar a { /* General sidebar text (excluding chat) */
        color: #b3ffe6;
        font-family: 'Roboto', sans-serif;
    }
    .stSidebar .stExpander { /* Style expanders */
         border: 1px solid #009966;
         border-radius: 4px;
         background-color: rgba(0, 30, 20, 0.8);
         margin-bottom: 10px;
    }
     .stSidebar .stExpander header { /* Expander header */
         color: #ff9933; /* Quantum Orange header */
         font-family: 'Orbitron', sans-serif;
     }
     .stSidebar .stExpander a { /* Base link style in expanders */
         color: #00ffff !important;
         text-decoration: none; /* Or underline if preferred */
         transition: color 0.2s ease;
     }
     .stSidebar .stExpander a:hover {
         color: #ffffff !important;
         text-decoration: underline;
     }
     /* Keep v1.8 specific link styles */
     .stSidebar .stExpander a[href*="cloud.google.com/web3"] {
        font-weight: bold;
        color: #99ffcc !important; /* Override base link color */
     }
     .stSidebar .stExpander a[href*="cloud.google.com/web3"]:hover {
        color: #ffffff !important;
     }
     .stSidebar .stExpander a[href*="newsapi.org"] {
        font-weight: bold;
        color: #99ccff !important; /* Light blue for NewsAPI link */
    }
    .stSidebar .stExpander a[href*="newsapi.org"]:hover {
        color: #ffffff !important;
    }
    /* --- >>> END OF RESTORED SIDEBAR STYLES <<< --- */


     /* --- Chat Specific Styles (Kept from v1.8) --- */
    [data-testid="chatAvatarIcon-user"] svg { fill: #00ffff; }
    [data-testid="chatAvatarIcon-assistant"] svg { fill: #ccff00; }

    /* ENLARGE CHATBOX CHANGE: Adjustments to chat messages */
    .stChatMessage {
        background-color: rgba(0, 20, 15, 0.85); /* Slightly more opaque */
        border: 1px solid rgba(153, 255, 204, 0.5); /* Slightly stronger border */
        border-radius: 8px;
        margin-bottom: 18px; /* Increased spacing */
        padding: 12px 18px; /* Increased padding */
    }
     .stChatMessage p, .stChatMessage li { /* Increase message font size */
        color: #e6fff2;
        font-family: 'Roboto', sans-serif;
        font-size: 1.05em; /* Increased font size */
        line-height: 1.6; /* Improved readability */
     }
      .stChatMessage code { /* Inline code styling */
        background-color: rgba(0, 0, 0, 0.5);
        color: #ff9933;
        font-family: 'Inconsolata', monospace;
        padding: 2px 5px;
        border-radius: 3px;
        border: 1px solid #336655;
        font-size: 0.95em; /* Slightly larger inline code */
     }
     /* Style ``` code blocks within chat */
     .stChatMessage pre > code {
        background-color: rgba(0, 0, 0, 0.75) !important;
        color: #aaffdd !important; /* Adjusted code block text */
        font-family: 'Inconsolata', monospace !important;
        padding: 12px; /* Increased padding */
        border-radius: 5px;
        border: 1px solid #99ccff;
        display: block;
        overflow-x: auto;
        font-size: 1.0em !important; /* Larger code block font */
     }
     .stChatMessage a { color: #00ffff !important; text-decoration: underline; }
     .stChatMessage a:hover { color: #ffffff !important; }


    /* ENLARGE CHATBOX CHANGE: Target chat input specifically */
    .stChatInput textarea {
        font-family: 'Inconsolata', monospace !important;
        color: #ccff00 !important;
        background-color: rgba(0, 40, 30, 0.9) !important;
        border: 1px solid #00ffff !important;
        box-shadow: inset 0 0 8px rgba(0, 255, 255, 0.6);
        min-height: 80px !important; /* Increased minimum height */
        height: 120px !important; /* Increased default height */
        font-size: 1.1em !important; /* Larger font in input */
        padding: 12px !important; /* Adjust padding */
        line-height: 1.5 !important;
    }
     .stChatInput textarea:focus {
        box-shadow: inset 0 0 12px #00ffff, 0 0 12px #00ffff;
     }
     /* Container for chat input */
     div[data-testid="stChatInput"] {
        /* Add styles here if needed, e.g., background */
        background-color: rgba(0, 10, 5, 0.8); /* Match sidebar base? */
        padding-top: 10px; /* Add some space above */
     }

    /* --- Code Blocks (General) --- */
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

    /* --- News Feed Styling (Kept from v1.8) --- */
     .news-item {
        border: 1px dashed rgba(153, 255, 204, 0.4); /* Mint dashed border */
        padding: 15px;
        margin-bottom: 20px;
        border-radius: 5px;
        background-color: rgba(0, 20, 15, 0.6); /* Dark background */
     }
     .news-item h3 {
        font-size: 1.2em; /* Slightly smaller news titles */
        color: #ccff00; /* Neon lime for titles */
        margin-bottom: 5px;
        text-shadow: 0 0 5px #ccff00;
     }
     .news-item h3 a {
         color: #ccff00 !important; /* Ensure link matches title color */
         text-decoration: none;
         transition: color 0.2s ease;
     }
     .news-item h3 a:hover {
         color: #ffffff !important; /* White hover */
         text-decoration: underline;
     }
     .news-item p { /* News snippet */
         font-size: 0.95em;
         color: #b3ffe6; /* Lighter mint */
         margin-bottom: 8px;
         line-height: 1.5;
     }
     .news-item .news-date { /* News date */
         font-size: 0.85em;
         color: #99ccff; /* Light blue for date */
         font-family: 'Inconsolata', monospace;
         text-align: right;
         opacity: 0.8;
     }


    /* --- Dividers --- */
    hr {
        border-top: 1px dashed #99ffcc; /* Dashed mint divider */
        opacity: 0.5;
    }

    /* --- Alerts (Info/Success/Error/Warning) --- */
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
    div[data-baseweb="alert"][role="alert"].st-ae { /* Selector might change between versions */
        background-color: rgba(0, 80, 40, 0.8); /* Darker green success */
        border-color: #00ff88;
        color: #ccffcc; /* Lighter green text */
    }
    /* Info */
    div[data-baseweb="alert"][role="alert"].st-b7 { /* Selector might change */
        background-color: rgba(0, 50, 80, 0.8); /* Darker blue info */
        border-color: #00aaff;
        color: #cceeff; /* Lighter blue text */
    }
    /* Error */
    div[data-baseweb="alert"][role="alert"].st-b6 { /* Selector might change */
        background-color: rgba(100, 0, 20, 0.8); /* Darker red error */
        border-color: #ff4466;
        color: #ffcccc; /* Lighter red text */
    }
     /* Warning */
    div[data-baseweb="alert"][role="alert"].st-b5 { /* Selector might change */
        background-color: rgba(100, 80, 0, 0.8); /* Darker yellow warning */
        border-color: #ffcc00;
        color: #ffffcc; /* Lighter yellow text */
    }

    /* --- Plotly Chart Backgrounds --- */
    .plotly-graph-div {
        background: transparent !important;
    }
    .plot-container .plotly svg {
        background: transparent !important;
    }
</style>
    """,
    unsafe_allow_html=True,
)

# --- Global Variables ---
pyusd_contract = None
PYUSD_CONTRACT_ADDRESS = None
token_info = None # Initialize token_info

# --- Initialize PYUSD Contract ---
rpc_ok = w3 and w3.is_connected()
contract_ok = False

if rpc_ok:
    try:
        PYUSD_CONTRACT_ADDRESS = Web3.to_checksum_address(PYUSD_CONTRACT_ADDRESS_NON_CHECKSUM)
        pyusd_contract = w3.eth.contract(address=PYUSD_CONTRACT_ADDRESS, abi=PYUSD_ABI_EXPANDED)
        contract_ok = True
        print(f"✅ PYUSD contract initialized via GCP RPC: {PYUSD_CONTRACT_ADDRESS}")
    except Exception as e_contract:
        st.error(f"🚨 **Contract Error:** Failed init via GCP RPC: {e_contract}", icon="📜")
        pyusd_contract = None


# --- Helper Functions ---

# --- Feature 6 Helper ---
def get_address_label(address):
    """Returns a label for a known address, or a shortened version."""
    checksum_addr = Web3.to_checksum_address(address)
    label = KNOWN_ADDRESSES.get(checksum_addr)
    if label:
        return f"{label} ({checksum_addr[:6]}...{checksum_addr[-4:]})"
    else:
        return f"{checksum_addr[:6]}...{checksum_addr[-4:]}"

# --- Cached Token Info ---
@st.cache_data(ttl=3600) # Cache for 1 hour
def get_token_info(_contract): # <-- Added underscore
    """Safely gets token info via the configured GCP RPC endpoint."""
    if not _contract or not w3 or not w3.is_connected(): return None # Note: using global w3 here, which is okay
    # ... rest of function using _contract ...
    try:
        name = _contract.functions.name().call()
        symbol = _contract.functions.symbol().call()
        decimals = _contract.functions.decimals().call()
        total_supply_raw = _contract.functions.totalSupply().call()
        total_supply = total_supply_raw / (10**decimals)
        return {"name": name, "symbol": symbol, "decimals": decimals, "total_supply": total_supply}
    except Exception as e:
        if isinstance(e, web3_exceptions.ContractLogicError):
             st.warning(f"⚠️ Token info function error (GCP RPC): {e}. Function might be missing/reverted.", icon="🔢")
        else:
            st.warning(f"⚠️ Token info fetch error (GCP RPC): {e}", icon="🔢")
        return None

@st.cache_data(ttl=30)
def get_address_balance(_contract, _address): # <-- Added underscore
    """Safely gets PYUSD balance for an address via the configured GCP RPC endpoint."""
    if not _contract or not w3 or not w3.is_connected(): return None # Using global w3
    if not Web3.is_address(_address): st.error(f"❌ Invalid Address Format: {_address}"); return None
    # ... rest of function using _contract and _address ...
    try:
        cs_addr = Web3.to_checksum_address(_address)
        token_data_local = token_info if token_info else get_token_info(_contract) # Fallback fetch needs _contract
        if not token_data_local: st.error("❌ Balance failed: Token info missing (via GCP RPC)."); return None
        decimals = token_data_local['decimals']
        balance_raw = _contract.functions.balanceOf(cs_addr).call()
        return balance_raw / (10**decimals)
    except Exception as e:
        st.warning(f"⚠️ Balance fetch error (GCP RPC) for {get_address_label(cs_addr)}: {e}", icon="💰")
        return None

@st.cache_data(ttl=60) # Cache Tx details for 1 minute
def get_tx_details(_w3, tx_hash): # <-- Added underscore
    """Safely retrieves transaction details and receipt via GCP RPC."""
    if not _w3 or not _w3.is_connected(): # <-- Use _w3
        st.error("❌ Cannot fetch Tx: RPC disconnected.", icon="🔌")
        return None
    # ... rest of function using _w3 and tx_hash ...
    try:
        if not isinstance(tx_hash, str) or not tx_hash.startswith('0x') or len(tx_hash) != 66:
            st.error(f"❌ Invalid Tx Hash Format: `{tx_hash[:15]}...`"); return None

        print(f"Fetching transaction details for: {tx_hash}")
        tx = _w3.eth.get_transaction(tx_hash)
        if not tx: st.error(f"❌ Tx not found: `{tx_hash[:15]}...`"); return None
        print(f"Transaction found for {tx_hash[:10]}...")

        receipt = None
        try:
            print(f"Fetching transaction receipt for: {tx_hash}")
            receipt = _w3.eth.get_transaction_receipt(tx_hash)
            if receipt: print(f"Receipt found for {tx_hash[:10]}...")
        except web3_exceptions.TransactionNotFound:
             print(f"Receipt not found yet for {tx_hash[:10]}... (Pending)")
             receipt = None # Ensure receipt is None
        except Exception as receipt_e:
             st.warning(f"⚠️ Tx `{tx_hash[:15]}...` receipt lookup error: {receipt_e}", icon="⏳")
             receipt = None # Ensure receipt is None

        # Process PENDING Transaction (No Receipt)
        if not receipt:
            st.info(f"⏳ Tx `{tx_hash[:15]}...` is pending (receipt not yet available).", icon="🕒")
            gas_price_gwei = "N/A"; value_eth = _w3.from_wei(tx.get('value', 0), 'ether')
            try: gas_price_gwei = f"{_w3.from_wei(tx.get('gasPrice', 0), 'gwei'):.6f}"
            except Exception: pass
            return {
                "Tx Hash": tx['hash'].hex(), "Status": "⏳ Pending", "From": tx.get('from', 'N/A'),
                "To": tx.get('to', 'N/A'), "Value (ETH)": f"{value_eth:.18f}", "Gas Limit": tx.get('gas', 'N/A'),
                "Gas Price (Gwei)": gas_price_gwei, "Nonce": tx.get('nonce', 'N/A')
                }

        # Process CONFIRMED Transaction (Receipt Available)
        gas_price_gwei = _w3.from_wei(tx['gasPrice'], 'gwei')
        value_eth = _w3.from_wei(tx['value'], 'ether')
        tx_fee_eth = _w3.from_wei(receipt['gasUsed'] * tx['gasPrice'], 'ether')
        status_text = "✅ Success" if receipt.get('status') == 1 else "❌ Failed"
        timestamp = "N/A (Block Error)"
        try:
             print(f"Fetching block details for block: {receipt['blockNumber']}")
             block = _w3.eth.get_block(receipt['blockNumber'])
             if block and 'timestamp' in block:
                 timestamp = datetime.fromtimestamp(block['timestamp'], tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
                 print(f"Block timestamp found: {timestamp}")
             else:
                 st.warning(f"⚠️ Incomplete block data for {receipt['blockNumber']}.", icon="🧱")
                 print(f"Warning: Incomplete block data for {receipt['blockNumber']}.")
        except Exception as block_e:
            st.warning(f"⚠️ Block timestamp error: {block_e}", icon="🧱")
            print(f"Exception fetching block timestamp for {receipt['blockNumber']}: {block_e}")

        return {
            "Tx Hash": tx['hash'].hex(), "Status": status_text, "Block": receipt['blockNumber'], "Timestamp": timestamp,
            "From": tx['from'], "To": receipt.get('contractAddress') or tx.get('to') or 'N/A', "Value (ETH)": f"{value_eth:.18f}",
            "Gas Used": receipt['gasUsed'], "Gas Limit": tx['gas'], "Gas Price (Gwei)": f"{gas_price_gwei:.6f}",
            "Tx Fee (ETH)": f"{tx_fee_eth:.18f}", "Nonce": tx['nonce'], "Logs Count": len(receipt.get('logs', [])),
            "Contract Address Created": receipt.get('contractAddress', None)
        }
    except HTTPError as http_err: st.error(f"❌ HTTP Error looking up Tx `{tx_hash[:15]}...`: {http_err}", icon="📡"); return None
    except Exception as e: st.error(f"❌ Tx details error `{tx_hash[:15]}...`: {e}", icon="🔥"); return None

@st.cache_data(ttl=300) # Cache block trace for 5 minutes
def get_block_trace(_w3, block_identifier): # <-- Added underscore
    """Requests a block trace using debug_traceBlock* methods via GCP RPC."""
    if not _w3 or not _w3.is_connected(): # <-- Use _w3
         st.error("❌ Cannot trace block: RPC disconnected.", icon="🔌")
         return None
    # ... rest of function using _w3 and block_identifier ...
    st.info(f"ℹ️ Requesting trace for block: `{block_identifier}` via Google Cloud RPC...")
    try:
        param = None; is_hash = False
        if isinstance(block_identifier, int):
            param = hex(block_identifier)
        elif isinstance(block_identifier, str):
            block_id_lower = block_identifier.lower()
            if block_id_lower in ['latest', 'earliest', 'pending']: param = block_id_lower
            elif block_id_lower.startswith('0x') and len(block_id_lower) == 66: param = block_id_lower; is_hash = True
            else:
                 try: param = hex(int(block_identifier))
                 except ValueError: st.error(f"❌ Invalid block identifier string: `{block_identifier}`"); return None
        else: st.error(f"❌ Invalid block identifier type: `{type(block_identifier)}`"); return None

        if param is None: st.error(f"❌ Failed to process block identifier: `{block_identifier}`"); return None

        rpc_method = "debug_traceBlockByHash" if is_hash else "debug_traceBlockByNumber"
        tracer_config = {"tracer": "callTracer"} # Example
        print(f"Making RPC Request: method='{rpc_method}', params=['{param}', {tracer_config}]")
        st.caption(f"Using tracer: `{tracer_config.get('tracer', 'default')}`")

        # Make raw RPC request (using _w3.provider)
        trace_raw = _w3.provider.make_request(rpc_method, [param, tracer_config])

        if 'result' in trace_raw:
            print("Trace successfully received.")
            return trace_raw['result']
        elif 'error' in trace_raw:
            error_msg = trace_raw['error'].get('message', 'N/A'); error_code = trace_raw['error'].get('code', 'N/A')
            st.error(f"❌ RPC Error during trace: {error_msg} (Code: {error_code})", icon="📡")
            st.warning(f"⚠️ Ensure GCP RPC endpoint supports `{rpc_method}` and the tracer `{tracer_config.get('tracer')}`.", icon="🛠️")
            print(f"RPC Error: {trace_raw['error']}")
            return None
        else:
            st.warning("⚠️ Unexpected trace response format (no 'result' or 'error')."); st.json(trace_raw); return None

    except HTTPError as http_err: st.error(f"❌ HTTP Error during trace operation for `{block_identifier}`: {http_err}", icon="📡"); return None
    except Exception as e: st.error(f"❌ Exception during trace operation for `{block_identifier}`: {e}", icon="🔥"); return None


@st.cache_data(ttl=300) # Cache state for 5 mins
def get_contract_state(_contract): # <-- Added underscore
    """Fetches specific public state variables from the contract."""
    if not _contract or not w3 or not w3.is_connected(): # Using global w3
        return {"Error": "Contract/Connection unavailable"}
    # ... rest of function using _contract ...
    state = {}
    try:
        owner = _contract.functions.owner().call()
        state["Owner"] = owner
        state["Owner Tagged"] = get_address_label(owner)
    except (web3_exceptions.ContractLogicError, AttributeError, KeyError):
        state["Owner"] = "N/A or Error"
        print("Note: Could not fetch contract owner.")
    except Exception as e:
        state["Owner"] = f"Error: {e}"
        print(f"Error fetching owner: {e}")

    # Add other state checks here if needed...

    return state

# --- Markdown Cleaner ---
def clean_markdown(text):
    """Removes specific markdown code block specifiers."""
    # ... (Keep existing function body) ...
    text = re.sub(r"```json\n", "```\n", text)
    text = re.sub(r"```python\n", "```\n", text)
    text = re.sub(r"```text\n", "```\n", text)
    return text

# --- Configure Gemini ---
@st.cache_resource
def configure_gemini(api_key):
    """Configures and returns the Gemini Generative Model."""
    # ... (Keep existing function body, using updated SYSTEM_INSTRUCTION) ...
    if not api_key: return None
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash-latest', # Or preferred model
                                   system_instruction=SYSTEM_INSTRUCTION, # Use updated instructions
                                   generation_config=genai.GenerationConfig(temperature=0.7))
        print("✅ Gemini model configured.")
        return model
    except Exception as e: st.error(f"🚨 **Gemini Error:** Config failed: {e}", icon="🔥"); return None

gemini_model = configure_gemini(GEMINI_API_KEY)

# --- Feature 10: AI Sentiment Analysis Helper ---
@st.cache_data(ttl=3600) # Cache sentiment for 1 hour
def get_news_sentiment(article_text):
    """Uses Gemini to get basic sentiment for news text."""
    if not gemini_model or not article_text:
        return "⚪" # Neutral/Unknown default

    prompt = f"""Analyze the sentiment of the following news headline/snippet regarding PYUSD, stablecoins, or blockchain technology. Respond ONLY with one word: POSITIVE, NEGATIVE, or NEUTRAL.

    News Text: "{article_text}"

    Sentiment:"""
    try:
        # Use a separate chat instance or direct generate_content for single tasks
        response = gemini_model.generate_content(prompt)
        sentiment_text = response.text.strip().upper()

        if "POSITIVE" in sentiment_text: return "🟢"
        elif "NEGATIVE" in sentiment_text: return "🔴"
        else: return "⚪"
    except Exception as e:
        print(f"Error getting news sentiment from Gemini: {e}")
        return "⚪" # Default on error


# --- News API Fetching (Modified for Sentiment - Feature 10) ---
@st.cache_data(ttl=1800) # Cache news+sentiment for 30 minutes
def fetch_news_from_newsapi(api_key, keywords):
    """Fetches news from NewsAPI and adds basic sentiment."""
    # ... (Keep existing NewsAPI logic) ...
    if not api_key:
        st.warning("⚠️ NewsAPI key is missing. Cannot fetch news.", icon="📰")
        return []

    base_url = "https://newsapi.org/v2/everything"
    query = " OR ".join(f'"{k}"' if " " in k else k for k in keywords)
    params = {
        'q': query, 'apiKey': api_key, 'language': 'en',
        'sortBy': 'publishedAt', 'pageSize': 30 # Increased slightly
    }
    print(f"Querying NewsAPI with parameters: {params}")
    processed_news = []
    try:
        response = requests.get(base_url, params=params, timeout=15) # Increased timeout
        response.raise_for_status()
        data = response.json()

        if data.get("status") == "ok":
            articles = data.get("articles", [])
            print(f"NewsAPI returned {len(articles)} articles.")
            #Use st.progress for sentiment fetching if many articles
            progress_bar = st.progress(0, text="Analyzing news sentiment...")
            for i, article in enumerate(articles):
                title = article.get('title', 'No Title Provided')
                link = article.get('url', '#')
                snippet = article.get('description', article.get('content', 'No snippet available.'))
                if snippet and len(snippet) > 250: snippet = snippet[:247] + "..."
                raw_date = article.get('publishedAt')
                publish_date_str = "Date unavailable"
                if raw_date:
                    try:
                        parsed_date_utc = datetime.strptime(raw_date, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
                        publish_date_str = parsed_date_utc.strftime('%b %d, %Y %H:%M UTC') # Abbreviated month
                    except (ValueError, TypeError): publish_date_str = raw_date

                # --- Feature 10 Integration ---
                sentiment_text = title + " " + snippet if snippet else title
                sentiment_emoji = get_news_sentiment(sentiment_text[:500]) # Limit text sent to AI
                # --- End Feature 10 ---

                processed_news.append({
                    'title': title, 'link': link, 'snippet': snippet,
                    'date': publish_date_str, 'sentiment': sentiment_emoji # Add sentiment
                })
                progress_bar.progress((i + 1) / len(articles), text=f"Analyzing sentiment... ({i+1}/{len(articles)})")
            progress_bar.empty() # Clear progress bar
            print(f"Processed {len(processed_news)} news items from NewsAPI with sentiment.")
            return processed_news
        else:
            # ... (keep existing NewsAPI error handling) ...
            api_message = data.get('message', 'Unknown API error')
            st.error(f"❌ NewsAPI Error: {api_message} (Code: {data.get('code', 'N/A')})", icon="📰")
            print(f"NewsAPI Error: Status={data.get('status')}, Code={data.get('code')}, Message={api_message}")
            return []

    except HTTPError as http_err:
        progress_bar.empty() # Clear progress bar on error
        st.error(f"❌ HTTP Error fetching news: {http_err}", icon="📡")
        print(f"HTTP Error during NewsAPI request: {http_err}")
        return []
    # ... (keep other exception handling) ...
    except Exception as e:
        # progress_bar.empty() # Clear progress bar on error
        st.error(f"❌ Error processing news feed: {e}", icon="📰")
        print(f"Exception during NewsAPI fetch/processing: {e}")
        import traceback
        traceback.print_exc()
        return []


# --- Event Fetching Base Function (Internal) ---
def _fetch_events_base(w3_conn, contract_obj, event_name, process_func, from_block, to_block):
    """Internal helper to fetch and process events."""
    try:
        event_obj = getattr(contract_obj.events, event_name)
        logs = event_obj.get_logs(from_block=from_block, to_block=to_block)

        if not logs:
            return [] # No events found in this range

        processed_events = []
        # Cache timestamps for efficiency within this fetch
        timestamps_cache = {}
        unique_block_nums = sorted(list(set(log['blockNumber'] for log in logs)))

        # Fetch timestamps efficiently (can still be slow for many unique blocks)
        # Consider adding a progress bar here if block range is large
        for block_num in unique_block_nums:
            if block_num not in timestamps_cache:
                try:
                    block = w3_conn.eth.get_block(block_num)
                    timestamps_cache[block_num] = datetime.fromtimestamp(block['timestamp'], tz=timezone.utc) if block and 'timestamp' in block else None
                except Exception as ts_e:
                    print(f"Warn: Timestamp fetch error block {block_num}: {ts_e}")
                    timestamps_cache[block_num] = None

        for log in logs:
            processed = process_func(log, timestamps_cache.get(log['blockNumber']))
            if processed:
                processed_events.append(processed)

        return processed_events

    except web3_exceptions.ABIFunctionNotFound:
         st.error(f"❌ Event '{event_name}' not found in contract ABI. Verify ABI definition.", icon="📜")
         print(f"ABI Error: Event '{event_name}' not found.")
         return None # Indicate ABI error
    except HTTPError as http_err:
        st.error(f"❌ HTTP Error fetching '{event_name}' events (Blocks {from_block}-{to_block}): {http_err}", icon="📡")
        try: st.error(f"Response: {http_err.response.text}")
        except Exception: pass
        return None # Indicate fetch error
    except Exception as e:
        st.error(f"❌ Error processing '{event_name}' events (Blocks {from_block}-{to_block}): {e} (Type: {type(e).__name__})", icon="🔥")
        print(f"Exception during {event_name} event fetch/processing: {e}")
        import traceback
        traceback.print_exc()
        return None # Indicate processing error


# --- Event Processing Functions (for _fetch_events_base) ---
def _process_transfer_event(log, timestamp):
    """Processes a raw Transfer event log."""
    if not token_info: return None # Need decimals
    decimals = token_info['decimals']
    symbol = token_info['symbol']
    value_pyusd = log['args']['value'] / (10**decimals)
    return {
        "Timestamp": timestamp, "Block": log['blockNumber'], "Tx Hash": log['transactionHash'].hex(),
        "From": log['args']['from'], "To": log['args']['to'], f"Value ({symbol})": value_pyusd,
        # Add labeled addresses for Feature 6
        "From Tagged": get_address_label(log['args']['from']),
        "To Tagged": get_address_label(log['args']['to']),
    }

def _process_mint_event(log, timestamp):
    """Processes a raw Mint event log. !!! Adjust args based on actual event !!!"""
    if not token_info: return None
    decimals = token_info['decimals']
    symbol = token_info['symbol']
    try:
        # !!! VERIFY 'to' and 'amount' parameter names in the actual Mint event !!!
        amount = log['args']['amount'] / (10**decimals)
        recipient = log['args']['to']
        return {
            "Timestamp": timestamp, "Block": log['blockNumber'], "Tx Hash": log['transactionHash'].hex(),
            "Recipient": recipient, f"Amount ({symbol})": amount,
            "Recipient Tagged": get_address_label(recipient)
        }
    except KeyError as e:
        st.warning(f"⚠️ Mint event processing error: Missing key {e}. Check ABI parameters.", icon="📜")
        return None # Skip malformed/unexpected event structure

def _process_burn_event(log, timestamp):
    """Processes a raw Burn event log. !!! Adjust args based on actual event !!!"""
    if not token_info: return None
    decimals = token_info['decimals']
    symbol = token_info['symbol']
    try:
        # !!! VERIFY 'from' and 'amount' parameter names in the actual Burn event !!!
        amount = log['args']['amount'] / (10**decimals)
        burner = log['args']['from']
        return {
            "Timestamp": timestamp, "Block": log['blockNumber'], "Tx Hash": log['transactionHash'].hex(),
            "Burner": burner, f"Amount ({symbol})": amount,
            "Burner Tagged": get_address_label(burner)
        }
    except KeyError as e:
        st.warning(f"⚠️ Burn event processing error: Missing key {e}. Check ABI parameters.", icon="📜")
        return None

def _process_approval_event(log, timestamp):
    """Processes a raw Approval event log."""
    if not token_info: return None
    decimals = token_info['decimals']
    symbol = token_info['symbol']
    value_pyusd = log['args']['value'] / (10**decimals)
    is_unlimited = log['args']['value'] == MAX_UINT256
    return {
        "Timestamp": timestamp, "Block": log['blockNumber'], "Tx Hash": log['transactionHash'].hex(),
        "Owner": log['args']['owner'], "Spender": log['args']['spender'],
        f"Amount ({symbol})": value_pyusd, "Unlimited": is_unlimited,
        "Owner Tagged": get_address_label(log['args']['owner']),
        "Spender Tagged": get_address_label(log['args']['spender']),
    }


# --- Public Event Fetching Functions (using base) ---
@st.cache_data(ttl=60) # Short cache for live feeds
def get_recent_events_df(_w3, _contract, event_name, _process_func, num_blocks=100): # <-- Added underscore here
    """Fetches recent events of a specific type via GCP RPC and returns DataFrame."""
    # --- IMPORTANT: Use the argument name with the underscore inside the function ---
    if not _w3 or not _w3.is_connected() or not _contract or not token_info:
        print(f"Event fetch precondition failed for {event_name} (w3/contract/token_info missing).")
        return None # Precondition failed, distinct from empty list

    try:
        latest_block = _w3.eth.block_number
        from_block = max(0, latest_block - num_blocks + 1)
        to_block = latest_block
        print(f"Fetching '{event_name}' events from block {from_block} to {to_block}...")

        # Pass the processing function (with underscore in its name now) to the base function
        event_list = _fetch_events_base(_w3, _contract, event_name, _process_func, from_block, to_block) # <-- Use _process_func here

        if event_list is None: # Indicates an error during fetch/processing
             return None
        if not event_list: # Empty list, no events found
            print(f"No '{event_name}' events found in blocks {from_block}-{to_block}.")
            return pd.DataFrame() # Return empty DataFrame

        print(f"Found {len(event_list)} '{event_name}' events.")
        df = pd.DataFrame(event_list)
        if not df.empty:
            df.sort_values(by="Block", ascending=False, inplace=True) # Ensure sorted
            # Format timestamp column nicely if present
            if "Timestamp" in df.columns:
                 try: df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce').dt.strftime('%Y-%m-%d %H:%M:%S UTC')
                 except Exception as fmt_e: print(f"Timestamp formatting error: {fmt_e}")
            print(f"Created DataFrame for {event_name} with {len(df)} rows.")
        return df

    except Exception as e:
        st.error(f"❌ Unexpected error fetching {event_name} events: {e}", icon="🔥")
        print(f"Unexpected error in get_recent_events_df for {event_name}: {e}")
        return None

# --- Feature 4: Historical Event Fetching (RPC Batching) ---
# WARNING: VERY SLOW FOR LARGE RANGES. USE WITH CAUTION.
@st.cache_data(ttl=3600) # Cache historical data longer
def get_historical_events_batched(_w3_conn, _contract_obj, event_name, _process_func, start_block, end_block, batch_size=1000): # <-- Added underscore to _contract_obj
    """Fetches events over a range in batches. SLOW!"""
    # --- Use the argument names with underscores inside the function ---
    if not _w3_conn or not _w3_conn.is_connected() or not _contract_obj or not token_info: #<-- Use _contract_obj
        st.error("❌ Historical fetch failed: Connection/Contract/Token Info unavailable.")
        return None

    st.warning(f"⚠️ Fetching historical '{event_name}' data from block {start_block} to {end_block} (Batch Size: {batch_size}). This can be very slow and may hit RPC limits.", icon="⏳")
    print(f"Starting historical batch fetch for {event_name} from {start_block} to {end_block}")

    all_events = []
    total_blocks = end_block - start_block + 1
    num_batches = math.ceil(total_blocks / batch_size)
    progress_bar_key = f"progress_{event_name}_{start_block}_{end_block}"
    if progress_bar_key not in st.session_state:
        st.session_state[progress_bar_key] = st.progress(0, text=f"Starting historical fetch for {event_name}...")
    progress_bar = st.session_state[progress_bar_key]

    try:
        for i in range(num_batches):
            batch_start = start_block + (i * batch_size)
            batch_end = min(end_block, batch_start + batch_size - 1)
            progress_text = f"Fetching '{event_name}' batch {i+1}/{num_batches} (Blocks {batch_start}-{batch_end})..."
            progress_bar.progress((i + 1) / num_batches, text=progress_text)
            print(progress_text)

            # Pass the connection and processing function (with underscores) to the base function
            batch_events = _fetch_events_base(_w3_conn, _contract_obj, event_name, _process_func, batch_start, batch_end) # <-- Use _contract_obj

            if batch_events is None:
                 st.error(f"❌ Error encountered during batch {i+1}. Stopping historical fetch.", icon="🔥")
                 progress_bar.empty()
                 if progress_bar_key in st.session_state: del st.session_state[progress_bar_key]
                 return None
            elif batch_events:
                 all_events.extend(batch_events)

            time.sleep(0.2)

        progress_bar.empty()
        if progress_bar_key in st.session_state: del st.session_state[progress_bar_key]

        if not all_events:
            st.info(f"ℹ️ No '{event_name}' events found in the specified historical range ({start_block}-{end_block}).")
            return pd.DataFrame()

        df = pd.DataFrame(all_events)
        # ... rest of the function remains the same ...
        df.sort_values(by="Block", ascending=False, inplace=True)
        if "Timestamp" in df.columns:
             try: df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce').dt.strftime('%Y-%m-%d %H:%M:%S UTC')
             except Exception: pass # Ignore formatting errors
        st.success(f"✅ Fetched {len(df)} historical '{event_name}' events from block {start_block} to {end_block}.", icon="💾")
        print(f"Finished historical batch fetch. Found {len(df)} events.")
        return df


    except Exception as e:
        if progress_bar_key in st.session_state:
             try: # Progress bar might already be gone if error was late
                 st.session_state[progress_bar_key].empty()
                 del st.session_state[progress_bar_key]
             except: pass
        st.error(f"❌ Unexpected error during historical batch fetch for {event_name}: {e}", icon="🔥")
        print(f"Unexpected error in get_historical_events_batched for {event_name}: {e}")
        return None

# --- Volume Calculation ---
def calculate_transfer_volume_from_df(df, symbol):
    """Calculates total PYUSD volume from the DataFrame."""
    # ... (Keep existing function body) ...
    value_col = f"Value ({symbol})"
    if df is None or df.empty or value_col not in df.columns:
        return 0
    try:
        return pd.to_numeric(df[value_col], errors='coerce').sum()
    except Exception as e:
        print(f"Error calculating volume: {e}")
        return 0

# --- Plotting Functions ---
# (Keep existing plot functions: plot_transfers_per_block, plot_transfer_value_distribution, plot_volume_per_block)
# Modify plot_top_addresses_pie to use tagged addresses
# --- Plotting Functions ---
# Re-adding original plot functions that were missing

def plot_transfers_per_block(df, symbol):
    """Generates a bar chart of transfer counts per block."""
    if df is None or df.empty or 'Block' not in df.columns: return None
    try:
        block_counts = df.groupby('Block').size().reset_index(name='Transfer Count')
        block_counts.sort_values('Block', inplace=True) # Sort by block number for chart
        fig = px.bar(block_counts, x='Block', y='Transfer Count',
                    title=f'PYUSD Transfer Count per Block (Filtered Scan)', # Updated title slightly
                    labels={'Block': 'Block Number', 'Transfer Count': 'Number of Transfers'},
                    template='plotly_dark') # Use dark theme
        fig.update_layout(bargap=0.2, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        fig.update_traces(marker_color='#00ffff', marker_line_color='#99ffcc', marker_line_width=1.5, opacity=0.8)
        return fig
    except Exception as e: print(f"Error plotting transfers per block: {e}"); return None

def plot_transfer_value_distribution(df, symbol):
    """Generates a histogram of transfer values."""
    value_col = f"Value ({symbol})"
    if df is None or df.empty or value_col not in df.columns: return None
    try:
         # Ensure numeric, drop non-numeric rows for plotting
         df[value_col] = pd.to_numeric(df[value_col], errors='coerce')
         df_filtered = df.dropna(subset=[value_col])
         # Filter out zero or negative values if they exist and aren't meaningful
         df_plot = df_filtered[df_filtered[value_col] > 0]
         if df_plot.empty: return None

         fig = px.histogram(df_plot, x=value_col,
                           title=f'Distribution of PYUSD Transfer Values (Filtered Scan)', # Updated title
                           labels={value_col: f'Transfer Value (${symbol})'},
                           template='plotly_dark', nbins=50, log_y=True) # Use log scale for Y axis
         fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
         fig.update_traces(marker_color='#99ffcc', marker_line_color='#00ffcc', opacity=0.7)
         return fig
    except Exception as e: print(f"Error plotting value distribution: {e}"); return None

def plot_volume_per_block(df, symbol):
    """Generates a bar chart of PYUSD volume transferred per block."""
    value_col = f"Value ({symbol})"
    if df is None or df.empty or value_col not in df.columns or 'Block' not in df.columns: return None
    try:
        df[value_col] = pd.to_numeric(df[value_col], errors='coerce')
        df_clean = df.dropna(subset=[value_col, 'Block'])
        volume_per_block = df_clean.groupby('Block')[value_col].sum().reset_index()
        volume_per_block.sort_values('Block', inplace=True)
        if volume_per_block.empty: return None

        fig = px.bar(volume_per_block, x='Block', y=value_col,
                    title=f'PYUSD Volume per Block (Analysis Scan)', # Updated title
                    labels={'Block': 'Block Number', value_col: f'Volume (${symbol})'},
                    template='plotly_dark')
        fig.update_layout(bargap=0.2, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        fig.update_traces(marker_color='#ff9933', marker_line_color='#ccff00', marker_line_width=1.5, opacity=0.8)
        return fig
    except Exception as e: print(f"Error plotting volume per block: {e}"); return None

# --- Feature 5: Network Graph Plotting ---
# (Keep the plot_network_graph function here)
# def plot_network_graph(df, symbol, value_threshold=1000, top_n_edges=50): ...

# --- Pie Chart Plotting (Modified for Tags) ---
# (Keep the plot_top_addresses_pie function here)
# def plot_top_addresses_pie(df, symbol, direction='From', top_n=10): ...
def plot_top_addresses_pie(df, symbol, direction='From', top_n=10):
    """Generates pie chart for top addresses by volume, using tagged labels."""
    value_col = f"Value ({symbol})"
    # Use the tagged address column for grouping
    address_col = f"{direction} Tagged" # Feature 6 change
    original_address_col = direction # Keep original for hover data

    if df is None or df.empty or address_col not in df.columns or value_col not in df.columns or original_address_col not in df.columns:
         print(f"Skipping pie chart: Missing columns ({address_col}, {value_col}, {original_address_col})")
         return None
    token_data_local = token_info # Use global token info
    if not token_data_local: token_data_local = {'decimals': 6} # Fallback

    try:
        df[value_col] = pd.to_numeric(df[value_col], errors='coerce')
        # Group by the TAGGED address, but keep original address for hover data
        # We need to aggregate both the tagged label and the original address
        # This requires a more complex aggregation if multiple original addresses map to the same tag (unlikely with current simple tagging)
        # For now, group by original address, sum volume, then add the tag for the top N
        address_volume = df.groupby(original_address_col)[value_col].sum().reset_index()

        address_volume = address_volume[address_volume[value_col] > 0]
        address_volume.sort_values(value_col, ascending=False, inplace=True)
        if address_volume.empty: return None

        # Aggregate smaller amounts into 'Other'
        if len(address_volume) > top_n:
            top_df = address_volume.head(top_n)
            other_sum = address_volume.iloc[top_n:][value_col].sum()
            if other_sum > 1e-9:
                 # For 'Other', use a placeholder label and address
                other_df = pd.DataFrame([{original_address_col: 'Other Addresses', value_col: other_sum}])
                final_df = pd.concat([top_df, other_df], ignore_index=True)
            else: final_df = top_df
        else: final_df = address_volume

        # Apply tagging to the final aggregated list for display names
        final_df[address_col] = final_df[original_address_col].apply(
             lambda addr: KNOWN_ADDRESSES.get(addr, f"{addr[:6]}...{addr[-4:]}") if addr != 'Other Addresses' else 'Other Addresses'
        )


        direction_label = "Sender" if direction == 'From' else "Recipient"
        fig = px.pie(final_df, names=address_col, values=value_col, # Use tagged name for pie slices
                    hover_data=[original_address_col], # Show full original address on hover
                    hole=0.3, template='plotly_dark',
                    title=f'Top {min(top_n, len(address_volume))} {direction_label} Addresses by Volume (${symbol})')

        cyberpunk_colors = ['#00ffff', '#ff9933', '#99ffcc', '#ccff00', '#ff00ff', '#ffff00', '#ff4500', '#00ff7f', '#8a2be2', '#ffa500', '#ff69b4']
        fig.update_traces(textposition='inside', textinfo='percent', insidetextorientation='radial',
                          marker_colors=cyberpunk_colors, pull=[0.05] * len(final_df),
                          # Custom hover template: Use customdata[0] for the original address
                          hovertemplate = f"<b>Address:</b> %{{customdata[0]}}<br><b>Label:</b> %{{label}}<br><b>Volume ({symbol}):</b> %{{value:,.{token_data_local['decimals']}f}}<br><b>Percentage:</b> %{{percent}}<extra></extra>")
        fig.update_layout(legend_title_text=f'{direction_label}s', paper_bgcolor='rgba(0,0,0,0)',
                          legend=dict(traceorder="reversed", title=f'{direction_label}s (Top {min(top_n, len(final_df))})', font=dict(size=10), itemsizing='constant'),
                          uniformtext_minsize=8, uniformtext_mode='hide')
        return fig
    except Exception as e:
        print(f"Error plotting top addresses pie: {e}"); import traceback; traceback.print_exc(); return None


# --- Feature 5: Network Graph Plotting ---
def plot_network_graph(df, symbol, value_threshold=1000, top_n_edges=50):
    """Generates an interactive network graph using pyvis."""
    value_col = f"Value ({symbol})"
    if df is None or df.empty or 'From' not in df.columns or 'To' not in df.columns or value_col not in df.columns:
        return None

    try:
        # Filter data for graph
        df_graph = df[[ 'From', 'To', value_col, 'From Tagged', 'To Tagged']].copy() # Include tagged columns
        df_graph[value_col] = pd.to_numeric(df_graph[value_col], errors='coerce')
        df_graph.dropna(subset=[value_col], inplace=True)
        df_graph = df_graph[df_graph[value_col] >= value_threshold] # Filter by minimum value

        # Aggregate volume between pairs
        agg_graph = df_graph.groupby(['From', 'To', 'From Tagged', 'To Tagged']).agg(
             total_volume=(value_col, 'sum'),
             transfer_count=(value_col, 'size')
        ).reset_index()

        # Limit number of edges for performance/clarity
        agg_graph.sort_values('total_volume', ascending=False, inplace=True)
        agg_graph = agg_graph.head(top_n_edges)

        if agg_graph.empty:
            st.info(f"No transfers found above ${value_threshold:,.2f} threshold for network graph.")
            return None

        # Create pyvis network
        net = Network(notebook=True, cdn_resources='in_line', height='600px', width='100%', bgcolor='#00050a', font_color='#99ffcc', filter_menu=True) # Dark background, cyberpunk font color

        # Add nodes and edges
        nodes = set(agg_graph['From']).union(set(agg_graph['To']))
        for node in nodes:
            label = KNOWN_ADDRESSES.get(node, f"{node[:6]}...{node[-4:]}") # Use tagging for node label
            title = f"Address: {node}\nKnown As: {KNOWN_ADDRESSES.get(node, 'N/A')}" # Hover title
            color = '#ff9933' if node in KNOWN_ADDRESSES else '#00ffff' # Different color for known addresses
            net.add_node(node, label=label, title=title, color=color, shape='dot', size=15) # Dot shape

        for _, row in agg_graph.iterrows():
            from_node, to_node = row['From'], row['To']
            volume = row['total_volume']
            count = row['transfer_count']

            # Scale edge width based on volume (log scale often works well)
            width = max(1, min(10, math.log10(volume + 1))) # Log scale, capped between 1 and 10

            title = f"From: {row['From Tagged']}\nTo: {row['To Tagged']}\nVolume: ${volume:,.2f}\nTransfers: {count}"
            net.add_edge(from_node, to_node, title=title, value=volume, width=width, color='#99ffcc') # Mint color for edges

        # Configure physics and interaction
        net.set_options("""
        var options = {
          "nodes": {
            "font": {
              "size": 12,
              "face": "Orbitron"
            },
            "borderWidth": 2,
             "borderWidthSelected": 4
          },
          "edges": {
            "color": {
              "inherit": false
            },
            "smooth": {
              "type": "continuous",
               "forceDirection": "none",
                "roundness": 0.2
            }
          },
           "interaction": {
            "hover": true,
            "tooltipDelay": 200,
            "navigationButtons": true,
             "keyboard": true
          },
          "physics": {
            "forceAtlas2Based": {
              "gravitationalConstant": -30,
              "centralGravity": 0.005,
              "springLength": 100,
              "springConstant": 0.18
            },
            "maxVelocity": 146,
             "solver": "forceAtlas2Based",
            "timestep": 0.35,
            "stabilization": {"iterations": 150}
          }
        }
        """)

        # Save to HTML and return path (or HTML content)
        html_file = "pyusd_network_graph.html"
        net.save_graph(html_file)
        return html_file

    except Exception as e:
        st.error(f"❌ Error generating network graph: {e}", icon="🕸️")
        print(f"Error generating network graph: {e}")
        import traceback
        traceback.print_exc()
        return None


# --- Simulation Functions ---
# Using slightly updated/cleaned sim functions from v1.5

def simulate_nfc_read():
    st.info("🤖 Simulating NFC Implant Read...")
    time.sleep(0.8) # Faster sim
    return SIMULATED_IMPLANT_ID

def get_user_wallet_address(implant_id):
    st.info(f"🔑 Searching Neural-Link DB for Implant ID: `{implant_id}`...")
    time.sleep(0.4) # Faster sim
    # Example mapping - use the actual contract address as a dummy user for consistency
    wallet_map = {
        "implant_user_cyber_777": PYUSD_CONTRACT_ADDRESS_NON_CHECKSUM,
        "implant_user_generic_123": "0x1234567890123456789012345678901234567890",
        "implant_admin_override_001": "0xAdminSimAddress001AdminSimAddress001Admin"
        }
    address = wallet_map.get(implant_id)
    if address: st.success(f"✅ Wallet found: `{address[:10]}...`")
    else: st.error(f"❌ Implant ID `{implant_id}` not found in simulated DB.")
    return address

def simulate_transaction_creation(sender_wallet, recipient_wallet, amount_pyusd, _w3, _contract):
    st.info("🛠️ Compiling Simulated PYUSD Transfer Transaction...")
    time.sleep(1.0) # Faster sim
    is_connected = _w3 and _w3.is_connected()
    sender_valid = Web3.is_address(sender_wallet)
    recipient_valid = Web3.is_address(recipient_wallet)
    nonce_val = "Sim (Connect/Addr Invalid)"; gas_price_gwei = "N/A"

    if is_connected:
        try:
            gas_price_raw = _w3.eth.gas_price; gas_price_gwei = f"{_w3.from_wei(gas_price_raw, 'gwei'):.2f}"
        except Exception as gas_e: st.warning(f"⚠️ Gas price fetch error: {gas_e}", icon="⛽"); gas_price_gwei = "N/A (Error)"

        if sender_valid:
             try: nonce_val = _w3.eth.get_transaction_count(Web3.to_checksum_address(sender_wallet))
             except Exception as nonce_e: st.warning(f"⚠️ Nonce fetch error: {nonce_e}", icon="🔢"); nonce_val = "Sim (Nonce Error)"

    token_data_local = get_token_info(_contract); decimals = token_data_local['decimals'] if token_data_local else 6
    if not token_data_local: st.warning("⚠️ Could not get decimals for amount calculation.", icon="🔢")

    try:
        amount_pyusd_float = float(amount_pyusd) # Ensure it's a float
        amount_int = int(amount_pyusd_float * (10**decimals))
    except (ValueError, TypeError): st.error(f"❌ Invalid Amount for transaction: {amount_pyusd}"); return None

    # ERC20 transfer function signature hash: 'a9059cbb'
    sig = "a9059cbb"
    # Pad recipient address and amount to 32 bytes (64 hex chars)
    to_pad = recipient_wallet[2:].lower().zfill(64) if recipient_valid else "".zfill(64)
    amt_pad = f"{amount_int:x}".zfill(64)
    data = f"0x{sig}{to_pad}{amt_pad}"

    contract_addr_display = PYUSD_CONTRACT_ADDRESS if _contract else "N/A (Contract Error)"

    return {
        "From (User Implant Wallet)": sender_wallet,
        "To (Merchant Wallet)": recipient_wallet,
        "Contract": contract_addr_display,
        "Function Signature": "transfer(address,uint256)",
        "Value (PYUSD)": f"{amount_pyusd_float:.{decimals}f}", # Format with correct decimals
        "Value (Raw Units)": amount_int,
        "Estimated Gas Limit": 60000, # Typical ERC20 transfer limit
        "Estimated Gas Price (Gwei)": gas_price_gwei,
        "Nonce": nonce_val,
        "Simulated Input Data": data
    }


def simulate_gcp_trace_transaction(transaction_details):
    st.info("📡 Simulating RPC `debug_traceTransaction`...")
    time.sleep(1.5) # Faster sim
    # More detailed placeholder trace structure based on v1.5
    sim_gas_used = 48500 # Example gas used
    from_addr = transaction_details.get('From (User Implant Wallet)', '0xSENDER_ADDRESS_PLACEHOLDER______')
    to_addr = transaction_details.get('To (Merchant Wallet)', '0xRECIPIENT_ADDRESS_PLACEHOLDER___')
    contract_addr = transaction_details.get('Contract', '0xCONTRACT_ADDRESS_PLACEHOLDER____')
    value_raw = transaction_details.get('Value (Raw Units)', 0)
    gas_limit = transaction_details.get('Estimated Gas Limit', 60000)

    # Basic validation (as in v1.5)
    if not all([Web3.is_address(from_addr), Web3.is_address(to_addr), Web3.is_address(contract_addr)]):
         st.warning("⚠️ Sim trace potentially inaccurate due to invalid addresses.", icon="🚧")
         # Use placeholder addresses if invalid to avoid errors in trace structure
         from_addr_safe = "0x"+"0"*40
         to_addr_safe = "0x"+"1"*40
    else:
        from_addr_safe = from_addr
        to_addr_safe = to_addr

    # Simplified trace steps for an ERC20 transfer (from v1.5 example)
    trace_result = {
        "gas": hex(gas_limit),
        "failed": False, # Assume success for simulation
        "returnValue": "0x0000000000000000000000000000000000000000000000000000000000000001", # ERC20 transfer success returns true (1)
        "structLogs": [
            {"pc": 0, "op": "PUSH1", "gas": hex(gas_limit-3), "gasCost": hex(3), "depth": 1, "stack": ["0x80"], "memory": [], "storage": {}, "comment": "Initial memory setup push"},
            {"pc": 50, "op": "CALLER", "gas": hex(gas_limit-100), "gasCost": hex(2), "depth": 1, "stack": [], "memory": [], "storage": {}, "comment": "Get transaction sender (msg.sender)"},
            {"pc": 75, "op": "SLOAD", "gas": hex(gas_limit-5000), "gasCost": hex(2100), "depth": 1, "stack": ["0x...", f"0x{from_addr_safe[2:]}"], "memory": [], "storage": {}, "comment": "Load sender's balance storage slot"},
            {"pc": 120, "op": "SSTORE", "gas": hex(gas_limit-10000), "gasCost": hex(5000), "depth": 1, "stack": ["0x...", "0x...", f"0x{from_addr_safe[2:]}"], "memory": [], "storage": {}, "comment": "Update (decrement) sender's balance in storage"},
            {"pc": 125, "op": "SLOAD", "gas": hex(gas_limit-15000), "gasCost": hex(2100), "depth": 1, "stack": ["0x...", f"0x{to_addr_safe[2:]}"], "memory": [], "storage": {}, "comment": "Load receiver's balance storage slot"},
            {"pc": 150, "op": "SSTORE", "gas": hex(gas_limit-20000), "gasCost": hex(5000), "depth": 1, "stack": ["0x...", "0x...", f"0x{to_addr_safe[2:]}"], "memory": [], "storage": {}, "comment": "Update (increment) receiver's balance in storage"},
            {"pc": 200, "op": "LOG3", "gas": hex(sim_gas_used+500), "gasCost": hex(1875), "depth": 1,
             "stack": [
                "0x0", # Memory start offset for data
                "0x20", # Memory length for data (uint256 = 32 bytes)
                "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef", # Keccak256 hash of "Transfer(address,address,uint256)"
                f"0x{from_addr_safe[2:].lower().zfill(64)}", # Indexed 'from' address
                f"0x{to_addr_safe[2:].lower().zfill(64)}"  # Indexed 'to' address
                ],
             "memory": [f"0x{value_raw:064x}"], # Non-indexed 'value' in memory data part
             "storage": {}, # Storage state after this step (usually complex)
             "comment": "Emit Transfer(from, to, value) event"},
            {"pc": 220, "op": "PUSH1", "gas": hex(sim_gas_used+3), "gasCost": hex(3), "depth": 1, "stack": ["0x01"], "comment": "Push return value 'true' (0x01)"},
            {"pc": 222, "op": "RETURN", "gas": hex(sim_gas_used), "gasCost": hex(0), "depth": 1, "stack": [], "memory": [], "storage": {}, "comment": "Return success"}
        ],
        "gasUsed": hex(sim_gas_used) # Report simulated gas used
    }
    return trace_result

# Transaction Details Fetcher (using robust v1.5 version)
@st.cache_data(ttl=60) # Cache Tx details for 1 minute
def get_tx_details(_w3, tx_hash):
    """Safely retrieves transaction details and receipt via GCP RPC."""
    if not _w3 or not _w3.is_connected():
        st.error("❌ Cannot fetch Tx: RPC disconnected.", icon="🔌")
        return None
    try:
        if not isinstance(tx_hash, str) or not tx_hash.startswith('0x') or len(tx_hash) != 66:
            st.error(f"❌ Invalid Tx Hash Format: `{tx_hash[:15]}...`"); return None

        print(f"Fetching transaction details for: {tx_hash}")
        # --- FIX: Remove request_kwargs ---
        tx = _w3.eth.get_transaction(tx_hash)
        # --- END OF FIX ---
        if not tx: st.error(f"❌ Tx not found: `{tx_hash[:15]}...`"); return None
        print(f"Transaction found for {tx_hash[:10]}...")

        receipt = None
        try:
            print(f"Fetching transaction receipt for: {tx_hash}")
            # --- FIX: Remove request_kwargs ---
            receipt = _w3.eth.get_transaction_receipt(tx_hash)
            # --- END OF FIX ---
            if receipt: print(f"Receipt found for {tx_hash[:10]}...")
        except Exception as receipt_e:
             # Be specific about 'not found' vs other errors
             if receipt_e.__class__.__name__ == 'TransactionNotFound' or 'not found' in str(receipt_e).lower():
                 print(f"Receipt not found yet for {tx_hash[:10]}... (Pending)")
             else:
                 st.warning(f"⚠️ Tx `{tx_hash[:15]}...` receipt lookup error: {receipt_e}", icon="⏳")
             receipt = None # Ensure receipt is None if lookup fails or not found

        # Process PENDING Transaction (No Receipt)
        if not receipt:
            st.info(f"⏳ Tx `{tx_hash[:15]}...` is pending (receipt not yet available).", icon="🕒")
            gas_price_gwei = "N/A"; value_eth = _w3.from_wei(tx.get('value', 0), 'ether')
            try: gas_price_gwei = f"{_w3.from_wei(tx.get('gasPrice', 0), 'gwei'):.6f}"
            except Exception: pass # Ignore errors fetching potentially missing fields
            return {
                "Tx Hash": tx['hash'].hex(),
                "Status": "⏳ Pending",
                "From": tx.get('from', 'N/A'),
                "To": tx.get('to', 'N/A'), # Might be None for contract creation
                "Value (ETH)": f"{value_eth:.18f}",
                "Gas Limit": tx.get('gas', 'N/A'),
                "Gas Price (Gwei)": gas_price_gwei,
                "Nonce": tx.get('nonce', 'N/A')
                }

        # Process CONFIRMED Transaction (Receipt Available)
        gas_price_gwei = _w3.from_wei(tx['gasPrice'], 'gwei')
        value_eth = _w3.from_wei(tx['value'], 'ether')
        tx_fee_eth = _w3.from_wei(receipt['gasUsed'] * tx['gasPrice'], 'ether')
        status_text = "✅ Success" if receipt.get('status') == 1 else "❌ Failed"
        timestamp = "N/A (Block Error)"
        try:
             print(f"Fetching block details for block: {receipt['blockNumber']}")
             # --- FIX: Remove request_kwargs ---
             block = _w3.eth.get_block(receipt['blockNumber'])
             # --- END OF FIX ---
             if block and 'timestamp' in block:
                 timestamp = datetime.utcfromtimestamp(block['timestamp']).strftime('%Y-%m-%d %H:%M:%S UTC')
                 print(f"Block timestamp found: {timestamp}")
             else:
                 st.warning(f"⚠️ Incomplete block data for {receipt['blockNumber']}.", icon="🧱")
                 print(f"Warning: Incomplete block data for {receipt['blockNumber']}.")
        except Exception as block_e:
            st.warning(f"⚠️ Block timestamp error: {block_e}", icon="🧱")
            print(f"Exception fetching block timestamp for {receipt['blockNumber']}: {block_e}")


        return {
            "Tx Hash": tx['hash'].hex(),
            "Status": status_text,
            "Block": receipt['blockNumber'],
            "Timestamp": timestamp,
            "From": tx['from'],
            "To": receipt.get('contractAddress') or tx.get('to') or 'N/A', # Handles contract creation 'to'
            "Value (ETH)": f"{value_eth:.18f}",
            "Gas Used": receipt['gasUsed'],
            "Gas Limit": tx['gas'],
            "Gas Price (Gwei)": f"{gas_price_gwei:.6f}",
            "Tx Fee (ETH)": f"{tx_fee_eth:.18f}",
            "Nonce": tx['nonce'],
            "Logs Count": len(receipt.get('logs', [])),
            "Contract Address Created": receipt.get('contractAddress', None) # None if not a creation tx
        }
    except HTTPError as http_err: st.error(f"❌ HTTP Error looking up Tx `{tx_hash[:15]}...`: {http_err}", icon="📡"); return None
    except Exception as e: st.error(f"❌ Tx details error `{tx_hash[:15]}...`: {e}", icon="🔥"); return None


# Block Trace Function (using robust v1.5 version)
@st.cache_data(ttl=300) # Cache block trace for 5 minutes
def get_block_trace(_w3, block_identifier):
    """Requests a block trace using debug_traceBlock* methods via GCP RPC."""
    if not _w3 or not _w3.is_connected():
         st.error("❌ Cannot trace block: RPC disconnected.", icon="🔌")
         return None
    st.info(f"ℹ️ Requesting trace for block: `{block_identifier}` via Google Cloud RPC...")
    try:
        param = None; is_hash = False
        # Determine if identifier is number, hash, or tag
        if isinstance(block_identifier, int):
            param = hex(block_identifier)
        elif isinstance(block_identifier, str):
            block_id_lower = block_identifier.lower()
            if block_id_lower in ['latest', 'earliest', 'pending']:
                param = block_id_lower
            elif block_id_lower.startswith('0x') and len(block_id_lower) == 66:
                param = block_id_lower
                is_hash = True
            else:
                 # Try converting string to int, then hex
                 try: param = hex(int(block_identifier))
                 except ValueError: st.error(f"❌ Invalid block identifier string: `{block_identifier}`"); return None
        else: st.error(f"❌ Invalid block identifier type: `{type(block_identifier)}`"); return None

        if param is None: st.error(f"❌ Failed to process block identifier: `{block_identifier}`"); return None

        # Choose RPC method based on identifier type
        rpc_method = "debug_traceBlockByHash" if is_hash else "debug_traceBlockByNumber"
        # Common tracer configurations (can be customized or made selectable)
        # 'callTracer' is good for call hierarchy, 'structTracer' for step-by-step opcodes
        tracer_config = {"tracer": "callTracer"} # Example: Use callTracer
        # tracer_config = {"tracer": "structLogger"} # Example: For opcode steps

        print(f"Making RPC Request: method='{rpc_method}', params=['{param}', {tracer_config}]")
        st.caption(f"Using tracer: `{tracer_config.get('tracer', 'default')}`")

        # Make raw RPC request
        # --- FIX: Remove request_kwargs (timeout should be set at provider level if needed) ---
        trace_raw = _w3.provider.make_request(rpc_method, [param, tracer_config])
        # --- END OF FIX ---

        # Process response
        if 'result' in trace_raw:
            print("Trace successfully received.")
            return trace_raw['result']
        elif 'error' in trace_raw:
            error_msg = trace_raw['error'].get('message', 'N/A'); error_code = trace_raw['error'].get('code', 'N/A')
            st.error(f"❌ RPC Error during trace: {error_msg} (Code: {error_code})", icon="📡")
            st.warning(f"⚠️ Ensure GCP RPC endpoint supports `{rpc_method}` and the tracer `{tracer_config.get('tracer')}`.", icon="🛠️")
            print(f"RPC Error: {trace_raw['error']}")
            return None
        else:
            st.warning("⚠️ Unexpected trace response format (no 'result' or 'error')."); st.json(trace_raw); return None

    except HTTPError as http_err: st.error(f"❌ HTTP Error during trace operation for `{block_identifier}`: {http_err}", icon="📡"); return None
    except Exception as e: st.error(f"❌ Exception during trace operation for `{block_identifier}`: {e}", icon="🔥"); return None



# --- Feature 3: Contract State Fetcher ---
@st.cache_data(ttl=300) # Cache state for 5 mins
def get_contract_state(_contract):
    """Fetches specific public state variables from the contract."""
    if not _contract or not w3 or not w3.is_connected():
        return {"Error": "Contract/Connection unavailable"}

    state = {}
    # --- Attempt to fetch common state variables ---
    # Owner
    try:
        owner = _contract.functions.owner().call()
        state["Owner"] = owner
        state["Owner Tagged"] = get_address_label(owner) # Add tag
    except (web3_exceptions.ContractLogicError, AttributeError, KeyError): # Handle if 'owner' func doesn't exist or reverts
        state["Owner"] = "N/A or Error"
        print("Note: Could not fetch contract owner.")
    except Exception as e:
        state["Owner"] = f"Error: {e}"
        print(f"Error fetching owner: {e}")

    # Add more state checks here if needed and ABIs are present
    # Example: Paused status
     #try:
         #paused = _contract.functions.isPaused().call()
         #state["Paused Status"] = "Paused" if paused else "Not Paused"
     #except (web3_exceptions.ContractLogicError, AttributeError, KeyError):
          #state["Paused Status"] = "N/A or Error"
          #print("Note: Could not fetch paused status.")
     #except Exception as e:
         #state["Paused Status"] = f"Error: {e}"
         #print(f"Error fetching paused status: {e}")

    #return state


# --- Streamlit App Layout ---
st.markdown("<h1 class='title'>🌌 PYUSD CyberMatrix Analytics v2.0 🔗</h1>", unsafe_allow_html=True) # Updated Title & Icon
st.markdown("<p class='gcp-subtitle'>Enhanced Real-time & Historical Insights via Google Cloud RPC, NewsAPI, AI Analysis & More</p>", unsafe_allow_html=True) # Updated Subtitle

# Critical component checks
if not rpc_ok: st.warning("GCP RPC connection failed. Blockchain features limited.", icon="🚫")
elif not contract_ok: st.warning("PYUSD Contract initialization failed (via GCP RPC). Check address and ABI.", icon="📜")
else: st.success(f"✅ Connected via Google Cloud Platform Blockchain RPC & PYUSD contract initialized ({get_address_label(PYUSD_CONTRACT_ADDRESS)}).", icon="🔌")

if not NEWSAPI_API_KEY: st.warning("News Feed disabled - NewsAPI Key missing in secrets.", icon="📰")
if not GEMINI_API_KEY: st.warning("AI Assistant & Features disabled - Gemini API Key missing in secrets.", icon="🤖")


# --- Fetch Token Info Early ---
# Needs to be done after contract init but before tabs use it
if 'token_info' not in st.session_state: st.session_state.token_info = None
if rpc_ok and contract_ok and st.session_state.token_info is None:
     print("Attempting initial token info fetch...")
     st.session_state.token_info = get_token_info(pyusd_contract)
# Make token_info easily accessible
token_info = st.session_state.get('token_info')


# --- Sidebar ---
with st.sidebar:
    st.markdown("<h2 class='cyber-matrix-title'>🟢 System Status & Info</h2>", unsafe_allow_html=True)

    # Connection Status Metrics
    st.metric(label="🛰️ GCP RPC Status", value="Connected" if rpc_ok else "Disconnected")
    st.metric(label="📜 Contract Status", value="Initialized" if contract_ok else "Failed/Unavailable")
    st.metric(label="📰 NewsAPI Status", value="Active" if NEWSAPI_API_KEY else "Not Configured")
    st.metric(label="🤖 Gemini AI", value="Active" if gemini_model else "Not Configured")

    st.markdown("---")
    st.markdown("### PYUSD Token Details")
    # Display token info (fetched earlier)
    if token_info:
        st.metric(label=f"Name", value=token_info['name'])
        st.metric(label="Symbol", value=f"${token_info['symbol']}")
        st.metric(label="Decimals", value=str(token_info['decimals']))
        st.metric(label="Total Supply", value=f"{token_info['total_supply']:,.{token_info['decimals']}f}")
        st.metric(label="Contract", value=get_address_label(PYUSD_CONTRACT_ADDRESS))
    else:
        if rpc_ok and contract_ok: st.warning("⚠️ Token info fetch failed.")
        else: st.metric(label="Token Info", value="Unavailable")

    # --- Feature 3: Contract State ---
    st.markdown("---")
    st.markdown("### Contract State")
    if rpc_ok and contract_ok:
        contract_state = get_contract_state(pyusd_contract)
        if contract_state:
             owner_val = contract_state.get('Owner Tagged', contract_state.get('Owner', 'N/A'))
             st.metric(label="Contract Owner", value=owner_val)
             # Display other fetched state vars here
             # if "Paused Status" in contract_state: st.metric(label="Paused Status", value=contract_state["Paused Status"])
        else: st.warning("⚠️ Could not fetch contract state.")
    else: st.metric(label="Contract State", value="Unavailable")


    # Network Info
    st.markdown("---")
    st.markdown("### Network Status (Ethereum)")
    # ... (Keep existing network status logic) ...
    if rpc_ok:
        try:
            latest_block_num = w3.eth.block_number
            gas_price_gwei = w3.from_wei(w3.eth.gas_price, 'gwei')
            st.metric(label="⛽ Gas Price (Gwei)", value=f"{gas_price_gwei:.2f}")
            st.metric(label="🔗 Latest Block", value=f"{latest_block_num:,}")
        except Exception as e: st.warning(f"⚠️ Network status error (GCP RPC): {e}")
    else:
        st.metric(label="⛽ Gas Price (Gwei)", value="N/A")
        st.metric(label="🔗 Latest Block", value="N/A")


    # --- Feature 8: Address Watchlist ---
    st.markdown("---")
    st.markdown("### <0xF0><0x9F><0x9B><0x9E>️ Address Watchlist")
    if 'watchlist' not in st.session_state: st.session_state.watchlist = set()

    new_watch_addr = st.text_input("Add Address to Watchlist", placeholder="0x...", key="watch_addr_input")
    col_watch1, col_watch2 = st.columns([1,1])
    with col_watch1:
        if st.button("➕ Add", key="watch_add_btn"):
            if Web3.is_address(new_watch_addr):
                cs_addr = Web3.to_checksum_address(new_watch_addr.strip())
                if cs_addr not in st.session_state.watchlist:
                    st.session_state.watchlist.add(cs_addr)
                    st.success(f"Added {get_address_label(cs_addr)} to watchlist.")
                    st.rerun() # Update display
                else: st.info("Address already in watchlist.")
            elif new_watch_addr: st.error("Invalid address format.")
    with col_watch2:
         # Disable button if watchlist is empty or core components missing
         disable_check_watchlist = not st.session_state.watchlist or not (rpc_ok and contract_ok and token_info)
         if st.button("💰 Check Balances", key="watch_check_btn", disabled=disable_check_watchlist):
             if st.session_state.watchlist:
                 st.info("Checking balances for watched addresses...")
                 # Display balances temporarily (could be put in main panel)
                 results = {}
                 prog_watch = st.progress(0)
                 watch_list = list(st.session_state.watchlist) # Iterate over a copy
                 for i, addr in enumerate(watch_list):
                      bal = get_address_balance(pyusd_contract, addr)
                      results[addr] = bal if bal is not None else "Error"
                      prog_watch.progress((i+1)/len(watch_list))
                 prog_watch.empty()
                 # Display results (could be a table/expander)
                 exp = st.expander("Watchlist Balances", expanded=True)
                 for addr, bal in results.items():
                     label = get_address_label(addr)
                     if isinstance(bal, (int, float)):
                         exp.metric(label=label, value=f"{bal:,.{token_info['decimals']}f} ${token_info['symbol']}")
                     else: exp.metric(label=label, value=str(bal)) # Show 'Error' or 'None'

    if st.session_state.watchlist:
        st.markdown("###### Current Watchlist:")
        # Allow removing items
        watch_list_display = list(st.session_state.watchlist)
        address_to_remove = st.selectbox("Select address to remove", options=[""] + watch_list_display, format_func=lambda x: get_address_label(x) if x else " - ", key="watch_remove_select")
        if address_to_remove and st.button("➖ Remove Selected", key="watch_remove_btn"):
            st.session_state.watchlist.remove(address_to_remove)
            st.success(f"Removed {get_address_label(address_to_remove)}.")
            st.rerun() # Update display

        # Simple display of the list
        # for addr in st.session_state.watchlist:
        #     st.text(f"- {get_address_label(addr)}")
    else:
        st.caption("No addresses being watched.")


    # Resources Expander
    st.markdown("---")
    with st.expander("📚 Resources & Links", expanded=False):
        # ... (Keep existing resource links) ...
        display_address = PYUSD_CONTRACT_ADDRESS if contract_ok else PYUSD_CONTRACT_ADDRESS_NON_CHECKSUM
        st.markdown(f"- [PYUSD Etherscan](https://etherscan.io/token/{display_address})")
        st.markdown("- [PayPal PYUSD Info](https://www.paypal.com/us/digital-wallet/pyusd)")
        st.markdown("- [Paxos PYUSD Page](https://paxos.com/pyusd/)")
        st.markdown("- **[GCP Blockchain RPC](https://cloud.google.com/web3/blockchain-rpc)** `(Used Here)`")
        st.markdown("- **[NewsAPI.org](https://newsapi.org/)** `(Used for News Feed)`")
        st.markdown("- [Web3.py Docs](https://web3py.readthedocs.io/)")
        st.markdown("- [Streamlit Docs](https://docs.streamlit.io/)")
        st.markdown("- [Pyvis Docs](https://pyvis.readthedocs.io/en/latest/) `(Network Graph)`")
        st.markdown("- [GitHub Repo](https://github.com/MiChaelinzo/pyusd-transaction-insights/) `(Original Base)`")

    # Gemini AI Assistant (in Sidebar)
    st.markdown("---")
    st.markdown("<h3 class='ai-assistant-title'>🤖 Gemini AI Assistant v2.0</h3>", unsafe_allow_html=True)
    # ... (Keep existing Gemini chat logic using updated system instruction) ...
    if not gemini_model: st.warning("AI Assistant offline. Check API Key & logs.", icon="🔌")
    else:
        if "messages" not in st.session_state: st.session_state.messages = []
        if "gemini_chat" not in st.session_state:
             try:
                 st.session_state.gemini_chat = gemini_model.start_chat(history=[])
                 print("Gemini chat session started.")
             except Exception as chat_e:
                 st.error(f"Failed to start Gemini chat session: {chat_e}", icon="💬")
                 print(f"Error starting chat: {chat_e}")
                 st.session_state.gemini_chat = None

        chat_display_container = st.container()
        # chat_display_container.markdown('<div style="max-height: 400px; overflow-y: auto; padding-right: 10px;">', unsafe_allow_html=True) # Optional height limit
        with chat_display_container:
            for msg in st.session_state.messages:
                with st.chat_message(msg["role"]):
                    st.markdown(clean_markdown(msg["content"]), unsafe_allow_html=False) # Clean markdown output
        # chat_display_container.markdown('</div>', unsafe_allow_html=True) # Close scrolling div

        if prompt := st.chat_input("Ask about PYUSD, blockchain...", key="gemini_prompt", disabled=(not st.session_state.get("gemini_chat"))):
            if st.session_state.get("gemini_chat"):
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"): st.markdown(prompt)

            try:
                with st.spinner("🧠 Thinking..."):
                    resp = st.session_state.gemini_chat.send_message(prompt, stream=False)

                    # Safely extract response text, check for blockage
                    cleaned_txt = "⚠️ Response generation issue." # Default error

                    # --- CORRECTED LOGIC ---
                    # First, check if the top-level response indicates blocking
                    if resp.prompt_feedback and resp.prompt_feedback.block_reason:
                         cleaned_txt = f"⚠️ Response blocked: {resp.prompt_feedback.block_reason}"
                         if resp.prompt_feedback.safety_ratings: cleaned_txt += f" (Ratings: {resp.prompt_feedback.safety_ratings})"
                    # If not blocked at prompt level, check the candidates list
                    elif resp.candidates: # Check if the list exists and is not empty
                        candidate = resp.candidates[0] # Assign the first candidate object to the 'candidate' variable
                        # Now, check the content of this specific candidate
                        if candidate.content and candidate.content.parts:
                            raw_txt = candidate.content.parts[0].text
                            cleaned_txt = clean_markdown(raw_txt)
                        # If no content, check if the candidate finished for other reasons (e.g., safety)
                        elif candidate.finish_reason != "STOP":
                             cleaned_txt = f"⚠️ Response stopped: {candidate.finish_reason}"
                             # Add safety ratings from the candidate if available
                             if hasattr(candidate, 'safety_ratings') and candidate.safety_ratings:
                                 cleaned_txt += f" (Safety: {candidate.safety_ratings})"
                        # If candidate exists but has no content and finished normally (unlikely but possible)
                        else:
                             cleaned_txt = "⚠️ Received empty response from AI."

                    # --- END CORRECTED LOGIC ---
                    else: # Handle cases where response has no candidates or other unexpected issues
                         print(f"Gemini response issue: No valid candidates or prompt feedback found. Response: {resp}")
                         cleaned_txt = "⚠️ Unexpected response format from AI."


                # Display assistant response
                with st.chat_message("assistant"): st.markdown(cleaned_txt)
                # Add response to history
                st.session_state.messages.append({"role": "assistant", "content": cleaned_txt})

            except Exception as e_ai:
                st.error(f"AI Assistant Error: {e_ai}", icon="🔥")
                print(f"Error during Gemini interaction: {e_ai}")
                # Optionally add the error to the chat display for user visibility
                with st.chat_message("assistant"): st.error(f"An error occurred: {e_ai}")
                st.session_state.messages.append({"role": "assistant", "content": f"Error: {e_ai}"})
                
    # Sidebar Footer
    st.markdown("---")
    st.caption(f"© {datetime.now().year} CyberMatrix v2.0 | GCP {'OK' if rpc_ok else 'FAIL'} | Contract {'OK' if contract_ok else 'FAIL'} | NewsAPI {'OK' if NEWSAPI_API_KEY else 'NA'} | AI {'OK' if gemini_model else 'NA'}")


# --- Main Content Tabs ---
# Dynamically create tabs based on available services/connections
tab_list = []
if rpc_ok and contract_ok and token_info: # Need token info for most
    tab_list.extend(["📊 Live Transfers", "📈 Volume & Address Analysis", "🪙 Supply Events", "🛡️ Approvals", "💰 Balance Check"])
if rpc_ok: # Need only RPC for these
    tab_list.extend(["🧾 Tx Lookup", "🔬 Block Trace"])
if rpc_ok and contract_ok and token_info: # Add historical if base OK
     tab_list.append("🕰️ Historical Analysis")
if NEWSAPI_API_KEY: # Requires NewsAPI
    tab_list.append("📰 News Feed")
if rpc_ok and contract_ok: # Requires base RPC/Contract
    tab_list.append("💳 Implant Sim")

if not tab_list:
     st.error("🚨 No data tabs available. Check GCP RPC / Contract / NewsAPI Key / Token Info status in secrets & logs.", icon="❌")
else:
    tabs = st.tabs(tab_list)
    tab_map = {name: tab for name, tab in zip(tab_list, tabs)}

def get_tab(name): return tab_map.get(name)

# --- Tab Implementations ---

# --- Tab: Live Transfers ---
if tab_ctx := get_tab("📊 Live Transfers"):
    with tab_ctx:
        st.header("📊 Live PYUSD Transfer Feed & Viz")
        st.markdown("<p class='tab-description'>Shows recent `Transfer` events fetched via Google Cloud RPC. Includes address tagging and filtering.</p>", unsafe_allow_html=True)

        # --- Controls Row ---
        ctrl_cols = st.columns([1.5, 1, 1, 1.5, 1.5]) # Adjust ratios as needed
        with ctrl_cols[0]:
            transfer_blocks_scan = st.slider( "Blocks to Scan", min_value=1, max_value=5, value=5, # Range 1-10k, default 500
                key="transfer_blocks_viz", help="Number of recent blocks to scan for transfers. Larger ranges are slower.")
        with ctrl_cols[1]:
             # Feature 12: Auto-Refresh Toggle
             auto_refresh = st.toggle("Auto-Refresh", value=False, key="transfer_auto_refresh", help="Automatically refresh feed every ~30 seconds (causes rerun).")
        with ctrl_cols[2]:
            fetch_transfers_viz = st.button("🔄 Refresh Feed", key="fetch_transfers_viz",
                disabled=not (rpc_ok and contract_ok and token_info), help="Requires RPC, Contract & Token Info.")
        # Leave space or add other controls in ctrl_cols[3], ctrl_cols[4]

        results_placeholder_transfers_viz = st.empty()
        # Initialize state
        if 'transfers_df' not in st.session_state: st.session_state.transfers_df = None
        if 'fetch_transfers_viz_pressed' not in st.session_state: st.session_state.fetch_transfers_viz_pressed = False

        # Handle button press or auto-refresh trigger
        if fetch_transfers_viz or (auto_refresh and 'transfers_df' in st.session_state): # Refresh if button pressed OR auto-refresh is on and data exists
            if rpc_ok and contract_ok and token_info:
                st.session_state.fetch_transfers_viz_pressed = True # Mark that a fetch was initiated
                results_placeholder_transfers_viz.empty()
                with st.spinner(f"🛰️ Querying ~{transfer_blocks_scan} blocks for Transfer events..."):
                    # Use the generic event fetcher
                    events_df = get_recent_events_df(w3, pyusd_contract, "Transfer", _process_transfer_event, num_blocks=transfer_blocks_scan)
                    st.session_state.transfers_df = events_df # Store result (DataFrame, None, or empty DF)
            else: # Should be disabled, but safety check
                 results_placeholder_transfers_viz.warning("Cannot fetch: RPC/Contract/Token Info unavailable.", icon="🚫")
                 st.session_state.fetch_transfers_viz_pressed = False # Reset pressed state if fetch failed pre-condition


        # Display results based on session state
        df_transfers = st.session_state.get('transfers_df') # Get current data

        if df_transfers is not None: # Data has been fetched (or attempted)
            results_placeholder_transfers_viz.empty() # Ensure placeholder is clear
            if not df_transfers.empty and token_info:
                st.success(f"✅ Displaying {len(df_transfers)} transfers found in the last ~{transfer_blocks_scan} blocks scan.", icon="💻")

                # --- Feature 7: Filtering ---
                st.markdown("---")
                st.subheader("Filter Transfers")
                filter_cols = st.columns(3)
                with filter_cols[0]:
                     min_val_filter = st.number_input(f"Min Value (${token_info['symbol']})", value=0.0, min_value=0.0, step=10.0, key="transfer_min_val", format="%.6f")
                with filter_cols[1]:
                     address_filter = st.text_input("Filter by Address (From/To)", placeholder="0x... or Label", key="transfer_addr_filter")
                # Can add max_value filter in filter_cols[2] if needed

                # Apply filters
                df_filtered = df_transfers.copy()
                if min_val_filter > 0:
                     value_col = f"Value ({token_info['symbol']})"
                     df_filtered = df_filtered[pd.to_numeric(df_filtered[value_col], errors='coerce') >= min_val_filter]
                if address_filter:
                     address_filter_lower = address_filter.lower()
                     df_filtered = df_filtered[
                         df_filtered['From'].str.lower().contains(address_filter_lower) |
                         df_filtered['To'].str.lower().contains(address_filter_lower) |
                         df_filtered['From Tagged'].str.lower().contains(address_filter_lower) | # Check tags too
                         df_filtered['To Tagged'].str.lower().contains(address_filter_lower)
                     ]
                st.caption(f"Showing {len(df_filtered)} transfers after filtering.")
                st.markdown("---")

                # Layout for charts (using filtered data)
                if not df_filtered.empty:
                    chart_col1, chart_col2 = st.columns(2)
                    with chart_col1:
                         with st.spinner("Generating block count chart..."): fig_bar = plot_transfers_per_block(df_filtered, token_info['symbol'])
                         if fig_bar: st.plotly_chart(fig_bar, use_container_width=True)
                    with chart_col2:
                         with st.spinner("Generating value distribution chart..."): fig_hist = plot_transfer_value_distribution(df_filtered, token_info['symbol'])
                         if fig_hist: st.plotly_chart(fig_hist, use_container_width=True)
                else:
                     st.info("No transfers match current filter criteria.")


                st.subheader("Filtered Transfers Table")
                # Define columns including tagged versions (Feature 6)
                display_cols = ["Timestamp", "Block", "Tx Hash", "From Tagged", "To Tagged", f"Value ({token_info['symbol']})"]
                valid_display_cols = [col for col in display_cols if col in df_filtered.columns]
                st.dataframe(df_filtered[valid_display_cols].head(100), hide_index=True, use_container_width=True) # Show top 100 filtered

                # --- Feature 9: Data Export ---
                csv_data = df_filtered.to_csv(index=False).encode('utf-8')
                st.download_button(
                     label="📥 Download Filtered Transfers (CSV)",
                     data=csv_data,
                     file_name=f"pyusd_transfers_filtered_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                     mime='text/csv',
                     key='download_transfers_csv'
                 )

            elif df_transfers.empty:
                st.info(f"ℹ️ No PYUSD Transfer events found in the scanned {transfer_blocks_scan} blocks.")
            # else: Error during fetch handled by get_recent_events_df or preconditions

        elif st.session_state.fetch_transfers_viz_pressed:
             # Fetch was pressed, but df is still None -> indicates an error occurred during fetch
             st.warning("⚠️ Failed to fetch or process transfer data. Check logs or RPC status.", icon="📡")
        else:
             # Initial state before button press
             if rpc_ok and contract_ok and token_info: results_placeholder_transfers_viz.info("Click 'Refresh Feed' or enable Auto-Refresh to load transfer data.")
             else: results_placeholder_transfers_viz.warning("Cannot fetch: RPC/Contract/Token Info unavailable.", icon="🚫")

        # --- Feature 12: Auto-Refresh Logic ---
        if auto_refresh and df_transfers is not None: # Only rerun if toggle is on AND data exists/was fetched
            time.sleep(30) # Refresh interval
            try:
                 st.rerun()
            except Exception as e:
                 print(f"Rerun interrupted: {e}") # May happen if user interacts during sleep

# --- Tab: Volume & Address Analysis ---
if tab_ctx := get_tab("📈 Volume & Address Analysis"):
    with tab_ctx:
        st.header("📈 PYUSD Volume & Address Analysis")
        st.markdown("<p class='tab-description'>Analyzes transfer volume, top addresses (pie charts), and network flow (graph) over a block range.</p>", unsafe_allow_html=True)

        # --- Controls ---
        vol_ctrl_cols = st.columns([1.5, 1, 1, 2])
        with vol_ctrl_cols[0]:
            volume_blocks_scan = st.slider("Blocks for Analysis", min_value=1, max_value=5, value=5, # Range 1-25k, default 1k
                 key="volume_blocks_addr", help="Blocks for volume/address/graph analysis. Larger ranges are slower.")
        with vol_ctrl_cols[1]:
            top_n_addresses = st.number_input("Top N Addr (Pie)", min_value=3, max_value=20, value=10, step=1, key="top_n_pie")
        with vol_ctrl_cols[2]:
             graph_value_thresh = st.number_input("Graph Min Value ($)", min_value=0, value=1000, step=100, key="graph_thresh", help="Minimum transfer value to include in network graph.")
        with vol_ctrl_cols[3]:
            analyze_volume_addr = st.button("⚙️ Analyze Volume & Network", key="analyze_vol_addr",
                disabled=not (rpc_ok and contract_ok and token_info), help="Requires RPC, Contract & Token Info.")

        results_placeholder_volume_addr = st.empty()
        # Initialize state
        if 'volume_df' not in st.session_state: st.session_state.volume_df = None
        if 'analyze_volume_addr_pressed' not in st.session_state: st.session_state.analyze_volume_addr_pressed = False

        # Handle button press
        if analyze_volume_addr and rpc_ok and contract_ok and token_info:
            st.session_state.analyze_volume_addr_pressed = True
            results_placeholder_volume_addr.empty()
            with st.spinner(f"⚙️ Aggregating transfer data over ~{volume_blocks_scan} blocks..."):
                vol_df = get_recent_events_df(w3, pyusd_contract, "Transfer", _process_transfer_event, num_blocks=volume_blocks_scan)
                st.session_state.volume_df = vol_df # Store result

        # Display results from state
        df_volume = st.session_state.get('volume_df')
        if df_volume is not None:
             results_placeholder_volume_addr.empty()
             if not df_volume.empty and token_info:
                 # Calculate total volume
                 total_vol = calculate_transfer_volume_from_df(df_volume, token_info['symbol'])
                 st.metric(label=f"Total Volume ({token_info['symbol']}) | Last ~{volume_blocks_scan} Blocks",
                           value=f"{total_vol:,.{token_info['decimals']}f}",
                           help=f"Based on {len(df_volume):,} transfers found in the scan.")

                 # --- Feature 11: AI Summarization ---
                 if gemini_model and len(df_volume) > 5: # Only summarize if data & AI available
                     if st.button("🤖 Summarize Volume Insights", key="summarize_volume_btn"):
                         prompt = f"""Analyze the following PYUSD transfer data summary from the last {volume_blocks_scan} blocks and provide 2-3 key insights in a concise, cyberpunk-themed bulleted list:
                         - Total Transfers: {len(df_volume)}
                         - Total Volume: ${total_vol:,.2f} {token_info['symbol']}
                         - Top 3 Senders (by Volume): {plot_top_addresses_pie(df_volume, token_info['symbol'], 'From', 3).data[0]['labels'][:3] if plot_top_addresses_pie(df_volume, token_info['symbol'], 'From', 3) else 'N/A'}
                         - Top 3 Receivers (by Volume): {plot_top_addresses_pie(df_volume, token_info['symbol'], 'To', 3).data[0]['labels'][:3] if plot_top_addresses_pie(df_volume, token_info['symbol'], 'To', 3) else 'N/A'}
                         Focus on significant patterns or large movements. Be brief."""
                         try:
                             with st.spinner("🧠 Generating AI summary..."):
                                 response = gemini_model.generate_content(prompt)
                                 st.info("🤖 AI Summary:")
                                 st.markdown(clean_markdown(response.text))
                         except Exception as e_ai_sum:
                             st.error(f"AI Summary Error: {e_ai_sum}")

                 st.markdown("---")
                 # Layout for charts
                 chart_col1_vol, chart_col2_vol = st.columns(2)
                 with chart_col1_vol:
                     with st.spinner("Generating volume/block chart..."): fig_vol_bar = plot_volume_per_block(df_volume, token_info['symbol'])
                     if fig_vol_bar: st.plotly_chart(fig_vol_bar, use_container_width=True)

                     with st.spinner(f"Generating top {top_n_addresses} senders chart..."): fig_pie_from = plot_top_addresses_pie(df_volume, token_info['symbol'], 'From', top_n_addresses)
                     if fig_pie_from: st.plotly_chart(fig_pie_from, use_container_width=True)

                 with chart_col2_vol:
                     # Placeholder for second column charts or info
                     # Top Receivers Pie Chart
                     with st.spinner(f"Generating top {top_n_addresses} receivers chart..."): fig_pie_to = plot_top_addresses_pie(df_volume, token_info['symbol'], 'To', top_n_addresses)
                     if fig_pie_to: st.plotly_chart(fig_pie_to, use_container_width=True)


                 # --- Feature 5: Network Graph ---
                 st.markdown("---")
                 st.subheader("🕸️ PYUSD Transfer Network Graph")
                 st.caption(f"Showing top {top_n_addresses * 2} edges (approx) with volume >= ${graph_value_thresh:,.2f}. Interaction heavy.") # Adjust edge count estimate
                 with st.spinner("Generating network graph..."):
                     graph_html_file = plot_network_graph(df_volume, token_info['symbol'], value_threshold=graph_value_thresh, top_n_edges=top_n_addresses * 2) # Pass threshold

                 if graph_html_file:
                     try:
                         with open(graph_html_file, 'r', encoding='utf-8') as HtmlFile:
                             source_code = HtmlFile.read()
                             components.html(source_code, height=610) # Adjust height as needed
                     except FileNotFoundError:
                         st.error("❌ Graph HTML file not found after generation.")
                     except Exception as e_graph:
                         st.error(f"❌ Error displaying graph: {e_graph}")
                 else:
                     st.info("Could not generate network graph (check data volume and thresholds).")


                 # --- Feature 9: Data Export ---
                 st.markdown("---")
                 csv_data_vol = df_volume.to_csv(index=False).encode('utf-8')
                 st.download_button(
                      label="📥 Download Full Volume Analysis Data (CSV)",
                      data=csv_data_vol,
                      file_name=f"pyusd_volume_analysis_{volume_blocks_scan}blocks_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                      mime='text/csv',
                      key='download_volume_csv'
                  )

             elif df_volume.empty: st.info(f"ℹ️ No PYUSD Transfer events found in the scanned {volume_blocks_scan} blocks for analysis.")
             elif not token_info: st.warning("⚠️ Cannot analyze volume, token info missing.")
        elif st.session_state.analyze_volume_addr_pressed:
            st.warning("⚠️ Failed to fetch or process volume data. Check logs or RPC status.", icon="📡")
        else: # Initial state
             if rpc_ok and contract_ok and token_info: results_placeholder_volume_addr.info("Select block range and click 'Analyze Volume & Network'.")
             else: results_placeholder_volume_addr.warning("Cannot analyze: RPC/Contract/Token Info unavailable.", icon="🚫")

# --- Tab: Supply Events (Feature 1) ---
if tab_ctx := get_tab("🪙 Supply Events"):
    with tab_ctx:
        st.header("🪙 PYUSD Mint & Burn Events")
        st.markdown("<p class='tab-description'>Tracks PYUSD supply changes by monitoring `Mint` and `Burn` events via GCP RPC.</p>", unsafe_allow_html=True)
        st.warning("⚠️ Event names ('Mint', 'Burn') and parameters assumed. Verify against actual contract ABI.", icon="📜")

        supply_cols = st.columns([1.5, 1.5, 3])
        with supply_cols[0]:
             supply_blocks_scan = st.slider("Blocks to Scan", min_value=1, max_value=5, value=5, key="supply_blocks", help="Blocks for Mint/Burn scan.")
        with supply_cols[1]:
             fetch_supply = st.button("🔄 Refresh Supply Events", key="fetch_supply_btn", disabled=not (rpc_ok and contract_ok and token_info))

        # Initialize state
        if 'mint_df' not in st.session_state: st.session_state.mint_df = None
        if 'burn_df' not in st.session_state: st.session_state.burn_df = None

        if fetch_supply and rpc_ok and contract_ok and token_info:
            with st.spinner(f"Scanning ~{supply_blocks_scan} blocks for Mint/Burn events..."):
                 st.session_state.mint_df = get_recent_events_df(w3, pyusd_contract, "Mint", _process_mint_event, num_blocks=supply_blocks_scan)
                 st.session_state.burn_df = get_recent_events_df(w3, pyusd_contract, "Burn", _process_burn_event, num_blocks=supply_blocks_scan)

        mint_df = st.session_state.get('mint_df')
        burn_df = st.session_state.get('burn_df')

        if mint_df is not None and burn_df is not None: # Check if fetch was attempted
            col_m, col_b = st.columns(2)
            with col_m:
                st.subheader("Recent Mints")
                if not mint_df.empty:
                    st.dataframe(mint_df[["Timestamp", "Block", "Tx Hash", "Recipient Tagged", f"Amount ({token_info['symbol']})"]].head(50), hide_index=True, use_container_width=True)
                    # Export Mint Data
                    csv_mint = mint_df.to_csv(index=False).encode('utf-8')
                    st.download_button("📥 Download Mint Data (CSV)", csv_mint, f"pyusd_mints_{supply_blocks_scan}blocks.csv", 'text/csv', key='download_mint_csv')
                elif isinstance(mint_df, pd.DataFrame): st.info("No Mint events found in scan.")
                else: st.warning("Error fetching Mint events.") # If None was returned

            with col_b:
                 st.subheader("Recent Burns")
                 if not burn_df.empty:
                     st.dataframe(burn_df[["Timestamp", "Block", "Tx Hash", "Burner Tagged", f"Amount ({token_info['symbol']})"]].head(50), hide_index=True, use_container_width=True)
                     # Export Burn Data
                     csv_burn = burn_df.to_csv(index=False).encode('utf-8')
                     st.download_button("📥 Download Burn Data (CSV)", csv_burn, f"pyusd_burns_{supply_blocks_scan}blocks.csv", 'text/csv', key='download_burn_csv')
                 elif isinstance(burn_df, pd.DataFrame): st.info("No Burn events found in scan.")
                 else: st.warning("Error fetching Burn events.")

            # Net Supply Change Plot (Basic)
            if not mint_df.empty or not burn_df.empty:
                 st.markdown("---")
                 st.subheader("Net Supply Change in Scanned Blocks")
                 mint_amount_col = f"Amount ({token_info['symbol']})"
                 # Combine mints and burns with block numbers
                 mints = mint_df[['Block', mint_amount_col]].copy()
                 burns = burn_df[['Block', mint_amount_col]].copy()
                 mints['Change'] = pd.to_numeric(mints[mint_amount_col], errors='coerce')
                 burns['Change'] = -pd.to_numeric(burns[mint_amount_col], errors='coerce') # Negative for burns
                 supply_change = pd.concat([mints[['Block', 'Change']], burns[['Block', 'Change']]])
                 supply_change_grouped = supply_change.groupby('Block')['Change'].sum().reset_index()
                 supply_change_grouped.sort_values('Block', inplace=True)

                 if not supply_change_grouped.empty:
                      fig_supply = px.bar(supply_change_grouped, x='Block', y='Change',
                                           title=f"Net PYUSD Supply Change per Block (Last ~{supply_blocks_scan} Blocks)",
                                           labels={'Block': 'Block Number', 'Change': f'Net Change (${token_info["symbol"]})'},
                                           template='plotly_dark')
                      fig_supply.update_layout(bargap=0.2, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                      st.plotly_chart(fig_supply, use_container_width=True)
                 else: st.info("Could not calculate net supply change.")

        elif fetch_supply: # Button pressed but results still None
             st.warning("⚠️ Failed to fetch supply events. Check logs or RPC status.", icon="📡")
        else:
             if rpc_ok and contract_ok and token_info: st.info("Click 'Refresh Supply Events' to load data.")
             else: st.warning("Cannot fetch: RPC/Contract/Token Info unavailable.", icon="🚫")


# --- Tab: Approvals (Feature 2) ---
if tab_ctx := get_tab("🛡️ Approvals"):
    with tab_ctx:
        st.header("🛡️ PYUSD Approval Events")
        st.markdown("<p class='tab-description'>Monitors ERC20 `Approval` events via GCP RPC. Highlights potentially risky unlimited approvals.</p>", unsafe_allow_html=True)

        appr_cols = st.columns([1.5, 1.5, 3])
        with appr_cols[0]:
            appr_blocks_scan = st.slider("Blocks to Scan", min_value=1, max_value=5, value=5, key="appr_blocks", help="Blocks for Approval scan.")
        with appr_cols[1]:
            fetch_appr = st.button("🔄 Refresh Approvals", key="fetch_appr_btn", disabled=not (rpc_ok and contract_ok and token_info))

        if 'approval_df' not in st.session_state: st.session_state.approval_df = None

        if fetch_appr and rpc_ok and contract_ok and token_info:
             with st.spinner(f"Scanning ~{appr_blocks_scan} blocks for Approval events..."):
                 st.session_state.approval_df = get_recent_events_df(w3, pyusd_contract, "Approval", _process_approval_event, num_blocks=appr_blocks_scan)

        approval_df = st.session_state.get('approval_df')

        if approval_df is not None:
            if not approval_df.empty:
                 st.subheader("Recent Approvals")
                 # Highlight unlimited approvals
                 def highlight_unlimited(row):
                     return ['background-color: rgba(255, 100, 100, 0.3)'] * len(row) if row['Unlimited'] else [''] * len(row)

                 df_display_appr = approval_df[["Timestamp", "Block", "Tx Hash", "Owner Tagged", "Spender Tagged", f"Amount ({token_info['symbol']})", "Unlimited"]].head(100)
                 st.dataframe(
                     df_display_appr.style.apply(highlight_unlimited, axis=1), # Apply highlighting
                     hide_index=True, use_container_width=True
                 )
                 st.caption("Rows highlighted in red indicate unlimited approvals.")

                 # Export Approval Data
                 csv_appr = approval_df.to_csv(index=False).encode('utf-8')
                 st.download_button("📥 Download Approval Data (CSV)", csv_appr, f"pyusd_approvals_{appr_blocks_scan}blocks.csv", 'text/csv', key='download_appr_csv')

            elif isinstance(approval_df, pd.DataFrame): st.info("No Approval events found in scan.")
            else: st.warning("Error fetching Approval events.") # If None was returned
        elif fetch_appr:
             st.warning("⚠️ Failed to fetch approval events. Check logs or RPC status.", icon="📡")
        else:
             if rpc_ok and contract_ok and token_info: st.info("Click 'Refresh Approvals' to load data.")
             else: st.warning("Cannot fetch: RPC/Contract/Token Info unavailable.", icon="🚫")

# --- Tab: Balance Check ---
# (Keep existing Balance Check tab logic, it uses get_address_label now via get_address_balance)
if tab_ctx := get_tab("💰 Balance Check"):
    with tab_ctx:
        st.header("💰 Check PYUSD Address Balance")
        st.markdown("<p class='tab-description'>Queries the current PYUSD balance for a given address using Google Cloud RPC.</p>", unsafe_allow_html=True)
        address_to_check = st.text_input("Ethereum Address or Known Label", key="balance_address", placeholder="0x... or 'PYUSD Contract'", label_visibility="collapsed")

        disable_balance_check = not (rpc_ok and contract_ok and token_info)
        tooltip_balance = "Requires active RPC, Contract & Token Info" if disable_balance_check else "Query PYUSD balance"

        if st.button("Check Balance", key="check_balance_btn", disabled=disable_balance_check, help=tooltip_balance):
            address_input_cleaned = address_to_check.strip()
            target_address = None

            # Try to resolve known label first
            if address_input_cleaned:
                for addr, label in KNOWN_ADDRESSES.items():
                    if label.lower() == address_input_cleaned.lower():
                        target_address = addr
                        st.info(f"Checking balance for label '{label}' ({addr[:8]}...)")
                        break # Found label match

            # If not a known label, assume it's an address
            if not target_address and address_input_cleaned:
                 if Web3.is_address(address_input_cleaned):
                     target_address = address_input_cleaned
                 else:
                     st.error(f"❌ Invalid Address or Unknown Label: `{address_input_cleaned}`")

            if target_address: # If we have a valid address to check
                with st.spinner(f"🔍 Querying balance for `{get_address_label(target_address)}` via GCP RPC..."):
                    balance = get_address_balance(pyusd_contract, target_address)
                    if balance is not None:
                        label_display = get_address_label(target_address)
                        st.metric(label=f"Balance: {label_display}",
                                  value=f"{balance:,.{token_info['decimals']}f} ${token_info['symbol']}")
                    # Error/Warning displayed within get_address_balance function
            elif not address_input_cleaned: # No input provided
                st.warning("⚠️ Please enter an Ethereum address or known label.")

        if disable_balance_check: st.caption("⛔ Balance Check Disabled: Requires RPC, Contract & Token Info.")

# --- Tab: Transaction Lookup ---
# (Keep existing Tx Lookup tab logic)
if tab_ctx := get_tab("🧾 Tx Lookup"):
     with tab_ctx:
        st.header("🧾 Transaction Details Lookup")
        st.markdown("<p class='tab-description'>Retrieves Ethereum transaction details and receipt using Google Cloud RPC.</p>", unsafe_allow_html=True)
        tx_hash_lookup = st.text_input("Transaction Hash", key="tx_hash_lookup", placeholder="0x...", label_visibility="collapsed")

        disable_tx_lookup = not rpc_ok
        tooltip_tx = "Requires active GCP RPC Connection" if disable_tx_lookup else "Lookup Transaction Hash"

        if st.button("🔍 Lookup Tx", key="lookup_tx_btn", disabled=disable_tx_lookup, help=tooltip_tx):
            tx_hash_lookup_cleaned = tx_hash_lookup.strip()
            if tx_hash_lookup_cleaned and tx_hash_lookup_cleaned.startswith('0x') and len(tx_hash_lookup_cleaned) == 66:
                with st.spinner(f"⏳ Fetching details for `{tx_hash_lookup_cleaned[:10]}...` via GCP RPC..."):
                    tx_details = get_tx_details(w3, tx_hash_lookup_cleaned)

                if tx_details:
                    status = tx_details.get("Status", ""); short_hash = f"{tx_hash_lookup_cleaned[:10]}...{tx_hash_lookup_cleaned[-8:]}"
                    if status == "⏳ Pending": st.info(f"⏳ Tx `{short_hash}` is pending.", icon="🕒")
                    elif status == "✅ Success": st.success(f"✅ Tx `{short_hash}` details retrieved.")
                    elif status == "❌ Failed": st.error(f"❌ Tx `{short_hash}` failed execution.", icon="💥")
                    else: st.info(f"ℹ️ Tx `{short_hash}` details retrieved.")

                    # Display details using tagged addresses where relevant
                    display_details = {}
                    for k, v in tx_details.items():
                         val_str = str(v) if v is not None else "None"
                         # Tag addresses
                         if k in ["From", "To", "Contract Address Created"] and isinstance(v, str) and Web3.is_address(v):
                             display_details[f"{k} (Tagged)"] = get_address_label(v)
                         display_details[k] = val_str

                    with st.expander("Show Transaction Details", expanded=True):
                        cols_tx = st.columns(2); col_idx = 0
                        for k, v in display_details.items():
                             if v == "None" and k != "Contract Address Created": continue # Skip most Nones
                             # Prioritize showing tagged address if available
                             if k.endswith(" (Tagged)"): continue # Already handled by original key
                             tagged_key = f"{k} (Tagged)"
                             display_key = k
                             display_val = display_details.get(tagged_key, v) # Use tagged value if exists

                             cols_tx[col_idx % 2].text(f"{display_key}:")
                             cols_tx[col_idx % 2].code(display_val, language='text')
                             col_idx += 1
                    st.markdown(f"👀 [View Transaction on Etherscan](https://etherscan.io/tx/{tx_hash_lookup_cleaned})")
                # Error handled within get_tx_details
            elif tx_hash_lookup_cleaned: st.error(f"❌ Invalid Transaction Hash Format.")
            else: st.warning("⚠️ Please enter a Transaction Hash.")

        if disable_tx_lookup: st.caption("⛔ Transaction Lookup Disabled: Requires GCP RPC Connection.")


# --- Tab: Block Trace ---
# (Keep existing Block Trace tab logic)
if tab_ctx := get_tab("🔬 Block Trace"):
     with tab_ctx:
        # ... Keep implementation from v1.8 ...
        st.header("🔬 Block Trace Explorer (Advanced)")
        st.markdown("<p class='tab-description'>Uses Google Cloud RPC `debug_traceBlock*` methods to inspect executions within a block.</p>", unsafe_allow_html=True)
        st.warning("""⚠️ **Note:** Requires specific RPC support (e.g., enabling the `debug` namespace on your GCP endpoint). Tracing can be slow and resource-intensive. Results depend heavily on the chosen tracer.""", icon="🛠️")

        block_id_input = st.text_input(
            "Block Number / Hash / 'latest'",
            "latest",
            key="trace_block_id",
            help="Enter block number, hash (0x...), or a tag like 'latest'"
        )

        disable_trace = not rpc_ok
        tooltip_trace = "Requires active GCP RPC Connection" if disable_trace else "Request trace for the specified block"

        if st.button("🔬 Get Block Trace", key="get_trace_btn", disabled=disable_trace, help=tooltip_trace):
            block_id_input_cleaned = block_id_input.strip()
            if block_id_input_cleaned:
                with st.spinner(f"⏳ Requesting trace for block `{block_id_input_cleaned}` via GCP RPC..."):
                    block_trace = get_block_trace(w3, block_id_input_cleaned) # Assumes get_block_trace exists and is correct

                if block_trace is not None:
                    st.success(f"✅ Trace data received for block `{block_id_input_cleaned}`.")
                    # Display logic based on trace format
                    if isinstance(block_trace, list) and block_trace:
                         st.info(f"Found {len(block_trace)} items/transactions in the trace.")
                         collapse = st.checkbox("Collapse Trace JSON?", True, key="collapse_trace")
                         st.json(block_trace[:25], expanded=(not collapse)) # Show first few items
                         if len(block_trace) > 25: st.info(f"Showing first 25 / {len(block_trace)} trace items.")
                    elif isinstance(block_trace, dict):
                         collapse = st.checkbox("Collapse Trace JSON?", True, key="collapse_trace")
                         st.json(block_trace, expanded=(not collapse))
                    elif isinstance(block_trace, list):
                        st.info("ℹ️ Empty trace list received.")
                    else:
                        st.warning("⚠️ Unexpected trace data format received:"); st.json(block_trace)

                    # Download button
                    try:
                        trace_str = json.dumps(block_trace, indent=2, default=lambda o: f"<unserializable: {type(o).__name__}>")
                        st.download_button(label="📥 Download Full Trace (JSON)", data=trace_str, file_name=f"trace_{block_id_input_cleaned}.json", mime="application/json")
                    except Exception as json_e: st.error(f"Failed to prepare trace data for download: {json_e}")
                # Error messages handled within get_block_trace
            else: st.warning("⚠️ Please enter a block identifier.")

        if disable_trace: st.caption("⛔ Block Trace Disabled: Requires GCP RPC Connection.")

# --- Tab: Historical Analysis (Feature 4) ---
if tab_ctx := get_tab("🕰️ Historical Analysis"):
    with tab_ctx:
        st.header("🕰️ Historical PYUSD Analysis")
        st.markdown("<p class='tab-description'>Analyze PYUSD events over a specified block range. **Warning:** This uses direct RPC batching and can be very slow and resource-intensive for large ranges!</p>", unsafe_allow_html=True)

        # Inputs for block range
        hist_cols = st.columns(3)
        with hist_cols[0]:
             hist_start_block = st.number_input("Start Block", min_value=0, value=w3.eth.block_number - 5 if rpc_ok else 0, step=1, key="hist_start")
        with hist_cols[1]:
             hist_end_block = st.number_input("End Block", min_value=hist_start_block if hist_start_block else 0, value=w3.eth.block_number if rpc_ok else 0, step=1, key="hist_end")
        with hist_cols[2]:
             hist_batch_size = st.number_input("RPC Batch Size", min_value=50, max_value=5000, value=1000, step=50, key="hist_batch", help="Lower if hitting RPC limits, higher might be faster but riskier.")

        event_type_to_analyze = st.selectbox(
             "Select Event Type",
             options=["Transfer", "Mint", "Burn", "Approval"], # Add more if needed
             key="hist_event_type"
        )

        disable_hist = not (rpc_ok and contract_ok and token_info)
        if st.button("⏳ Analyze Historical Range", key="hist_analyze_btn", disabled=disable_hist):
            if hist_end_block >= hist_start_block:
                # Determine process function based on selected event type
                process_func = None
                if event_type_to_analyze == "Transfer": process_func = _process_transfer_event
                elif event_type_to_analyze == "Mint": process_func = _process_mint_event
                elif event_type_to_analyze == "Burn": process_func = _process_burn_event
                elif event_type_to_analyze == "Approval": process_func = _process_approval_event

                if process_func:
                     # Clear previous results for this type
                     session_key = f"historical_{event_type_to_analyze}_df"
                     st.session_state[session_key] = None # Clear before fetching

                     # Call the batched fetch function (will show spinner/warnings internally)
                     hist_df = get_historical_events_batched(
                         w3, pyusd_contract, event_type_to_analyze, process_func,
                         hist_start_block, hist_end_block, hist_batch_size
                     )
                     st.session_state[session_key] = hist_df # Store result (even if None or empty)
                else: st.error("Internal error: No processing function for selected event type.")
            else: st.error("End Block must be greater than or equal to Start Block.")

        # Display results if available in session state
        session_key = f"historical_{event_type_to_analyze}_df"
        hist_df_display = st.session_state.get(session_key)

        if hist_df_display is not None:
            st.markdown("---")
            st.subheader(f"Historical {event_type_to_analyze} Data ({hist_start_block} - {hist_end_block})")
            if not hist_df_display.empty:
                 st.dataframe(hist_df_display.head(200), hide_index=True, use_container_width=True) # Show sample
                 st.info(f"Displaying first 200 of {len(hist_df_display)} results.")

                 # Add basic plots for historical data if relevant (e.g., volume over time for Transfers)
                 if event_type_to_analyze == "Transfer" and 'Timestamp' in hist_df_display.columns:
                     try:
                         hist_df_display['Date'] = pd.to_datetime(hist_df_display['Timestamp']).dt.date
                         daily_volume = hist_df_display.groupby('Date')[f"Value ({token_info['symbol']})"].sum().reset_index()
                         fig_hist_vol = px.line(daily_volume, x='Date', y=f"Value ({token_info['symbol']})", title="Historical Daily Transfer Volume", template='plotly_dark')
                         st.plotly_chart(fig_hist_vol, use_container_width=True)
                     except Exception as e_hist_plot:
                         st.warning(f"Could not plot historical volume: {e_hist_plot}")

                 # Export Historical Data
                 csv_hist = hist_df_display.to_csv(index=False).encode('utf-8')
                 st.download_button(f"📥 Download Historical {event_type_to_analyze} Data (CSV)", csv_hist, f"pyusd_hist_{event_type_to_analyze}_{hist_start_block}-{hist_end_block}.csv", 'text/csv', key=f'download_hist_{event_type_to_analyze}_csv')

            elif isinstance(hist_df_display, pd.DataFrame): st.info("No events found in the specified historical range.")
            else: st.warning("Error occurred during historical data fetch.") # Fetch returned None

        if disable_hist: st.caption("⛔ Historical Analysis Disabled: Requires RPC, Contract & Token Info.")


# --- Tab: News Feed (Modified for Sentiment) ---
if tab_ctx := get_tab("📰 News Feed"):
    with tab_ctx:
        st.header("📰 Latest Blockchain & PYUSD News")
        st.markdown("<p class='tab-description'>Recent news with AI-powered sentiment analysis, fetched from NewsAPI.</p>", unsafe_allow_html=True)
        st.caption(f"News fetched around {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}. Data cached ~30 mins.")

        news_keywords = [
            "PYUSD", "PayPal Stablecoin", "blockchain", "ethereum",
            "stablecoin regulation", "crypto payments", "web3 adoption", "Paxos", "stablecoin", "digital dollar" # Expanded keywords
        ]
        st.info(f"**Searching NewsAPI for keywords:** `{', '.join(news_keywords)}`")

        news_refresh_disabled = not NEWSAPI_API_KEY
        news_refresh_tooltip = "NewsAPI Key missing." if news_refresh_disabled else "Fetch latest news (clears cache)"

        if st.button("🔄 Refresh News Feed", key="refresh_news_btn", disabled=news_refresh_disabled, help=news_refresh_tooltip):
             st.cache_data.clear() # Clear all data cache (simplest)
             st.success("News cache cleared. Fetching fresh results...", icon="🔄")
             st.rerun()

        if news_refresh_disabled:
            st.warning("News feed disabled. Configure NewsAPI key.", icon="🔒")
        else:
            with st.spinner("📰 Loading news feed from NewsAPI & analyzing sentiment..."):
                news_items = fetch_news_from_newsapi(NEWSAPI_API_KEY, news_keywords) # Now includes sentiment

            if news_items:
                st.markdown(f"Found **{len(news_items)}** relevant news articles:")
                st.markdown("---")
                for item in news_items:
                     # Display sentiment emoji (Feature 10)
                     sentiment = item.get('sentiment', '⚪')
                     st.markdown(f"""
                     <div class="news-item">
                         <h3>{sentiment} <a href="{item['link']}" target="_blank" title="{item.get('snippet', 'Click to read more')}">{item['title']}</a></h3>
                         <p>{item.get('snippet', 'No snippet available.')}</p>
                         <div class="news-date">📅 Published: {item.get('date', 'Date unavailable')}</div>
                     </div>
                     """, unsafe_allow_html=True)
                     st.markdown("---")
                st.caption("Sentiment (🟢/⚪/🔴) is AI-generated and approximate.")
            elif NEWSAPI_API_KEY:
                 st.info("No recent news items found matching keywords.")


# --- Tab: Simulated Implant Payment ---
# (Keep existing Implant Sim tab logic)
if tab_ctx := get_tab("💳 Implant Sim"):
     with tab_ctx:
        st.header("💳 Simulate Bio-Implant Payment")
        st.markdown("<p class='tab-description'>Conceptual simulation of a PYUSD payment initiated via biochip. Uses GCP RPC for network data and contract info.</p>", unsafe_allow_html=True)
        st.info(f"Simulating payment for Implant ID: `{SIMULATED_IMPLANT_ID}`", icon="🆔")

        col1_sim, col2_sim = st.columns(2)
        with col1_sim:
            merchant_addr = st.text_input("Merchant Wallet Address (Simulated Recipient)", "0x6c3ea9036406852006290770bedfcaba0e23a0e8", key="merchant_sim", help="Enter the Ethereum address of the simulated merchant.")
            display_decimals = token_info['decimals'] if token_info else 6
            amount_sim = st.number_input(f"Amount (PYUSD - {display_decimals} decimals)", min_value= (1 / (10**display_decimals)) if token_info else 0.000001, value=1.50, step= 1.0 / (10**(display_decimals-1)) if token_info else 0.01, format=f"%.{display_decimals}f", key="amount_sim", help="Enter the amount of PYUSD to simulate sending.")
        with col2_sim:
            st.markdown("<br/>", unsafe_allow_html=True)
            disable_sim = not (rpc_ok and contract_ok and token_info)
            tooltip_sim = "Requires active RPC, Contract & Token Info" if disable_sim else "Simulate Implant Tap & Authorize Payment"

            if st.button("⚡ Tap Implant & Authorize Payment (Sim)", key="simulate_pay_btn", disabled=disable_sim, help=tooltip_sim):
                implant_id = simulate_nfc_read()
                user_wallet = get_user_wallet_address(implant_id)
                merchant_valid = Web3.is_address(merchant_addr.strip())
                amount_valid = isinstance(amount_sim, (int, float)) and amount_sim > 0

                if user_wallet and merchant_valid and amount_valid:
                    cs_merchant = Web3.to_checksum_address(merchant_addr.strip())
                    tx_sim = simulate_transaction_creation(user_wallet, cs_merchant, amount_sim, w3, pyusd_contract) # Assumes function exists

                    if tx_sim:
                        st.success("✅ Sim Auth & Transaction Compilation Sequence Complete!")
                        with st.expander("Simulated Transaction Data", expanded=True): st.json(tx_sim)
                        trace_sim = simulate_gcp_trace_transaction(tx_sim) # Assumes function exists
                        with st.expander("Simulated GCP RPC Trace Result", expanded=False):
                            try:
                                 trace_sim_str = json.dumps(trace_sim, indent=2, default=lambda o: f"<unserializable: {type(o).__name__}>")
                                 st.code(trace_sim_str, language="json")
                                 st.caption("Note: Trace structure is a simplified representation.")
                            except Exception as json_e_sim: st.error(f"Cannot display simulated trace: {json_e_sim}"); st.json(trace_sim)
                elif not user_wallet: pass
                elif not merchant_valid: st.error(f"❌ Invalid Merchant Address Format: `{merchant_addr}`")
                elif not amount_valid: st.error(f"❌ Invalid or Zero Amount Entered.")

            elif disable_sim: st.caption("⛔ Simulation Disabled: Requires RPC, Contract & Token Info.")

        st.markdown("---")
        st.caption("Disclaimer: This is a conceptual simulation only.")


# --- Footer ---
st.markdown("---")
st.markdown(f"<p style='text-align:center; font-size: 0.9em; opacity: 0.7;'>© {datetime.now().year} PYUSD CyberMatrix v2.0 | Developed based on MiChaelinzo's v1.8 | Enhanced Features</p>", unsafe_allow_html=True)

# --- End of Streamlit App Script ---
print("Streamlit app script v2.0 finished loading.")
