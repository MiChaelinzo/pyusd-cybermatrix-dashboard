# -*- coding: utf-8 -*-
"""
Enhanced PYUSD Analytics Dashboard 📊🔗 powered by Google Cloud Blockchain RPC
Integrates News API for Direct News Fetching, plus Visualizations, Gemini Chat & Feed
(Version 1.8 - Restored v1.3 Sidebar Style - Error Fixes Included)
"""

# --- Imports ---
import streamlit as st
from web3 import Web3
import json         # For pretty printing JSON output
import time         # For simulated delays
from datetime import datetime, timezone # For timestamp conversion and formatting news dates
import pandas as pd # For data manipulation
import plotly.express as px # For interactive charts
from collections import Counter # For counting addresses
import google.generativeai as genai # For Gemini Chat
import re           # For cleaning markdown
import requests     # NEWS API CHANGE: Added for making HTTP requests
from requests.exceptions import HTTPError, RequestException # Error handling for RPC and API calls

# --- Early Configuration: MUST BE FIRST STREAMLIT COMMAND ---
st.set_page_config(
    page_title="PYUSD CyberMatrix [GCP RPC + NewsAPI] 🔗 v1.8", # Updated version
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="🧬"
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

# NEWS API CHANGE: Fetch News API Key
try:
    NEWSAPI_API_KEY = st.secrets["newsapi"]["api_key"]
    if not NEWSAPI_API_KEY: raise KeyError
    print("✅ NewsAPI Key found.")
except (AttributeError, KeyError):
    st.error("🚨 **Config Error:** NewsAPI Key (`newsapi.api_key`) missing/empty. News Feed disabled.", icon="⚙️")
    NEWSAPI_API_KEY = None


PYUSD_CONTRACT_ADDRESS_NON_CHECKSUM = "0x6c3ea9036406852006290770bedfcaba0e23a0e8"
SIMULATED_IMPLANT_ID = "implant_user_cyber_777"

# **Expanded PYUSD ABI** (Keep as is)
PYUSD_ABI_EXPANDED = [
    {"anonymous": False,"inputs": [{"indexed": True, "internalType": "address", "name": "from", "type": "address"},{"indexed": True, "internalType": "address", "name": "to", "type": "address"},{"indexed": False, "internalType": "uint256", "name": "value", "type": "uint256"}],"name": "Transfer","type": "event"},
    {"constant": True,"inputs": [],"name": "name","outputs": [{"name": "", "type": "string"}],"payable": False,"stateMutability": "view","type": "function"},
    {"constant": True,"inputs": [],"name": "symbol","outputs": [{"name": "", "type": "string"}],"payable": False,"stateMutability": "view","type": "function"},
    {"constant": True,"inputs": [],"name": "decimals","outputs": [{"name": "", "type": "uint8"}],"payable": False,"stateMutability": "view","type": "function"},
    {"constant": True,"inputs": [],"name": "totalSupply","outputs": [{"name": "", "type": "uint256"}],"payable": False,"stateMutability": "view","type": "function"},
    {"constant": True,"inputs": [{"name": "account", "type": "address"}],"name": "balanceOf","outputs": [{"name": "", "type": "uint256"}],"payable": False,"stateMutability": "view","type": "function"},
]

# --- System Instruction for Gemini ---
# (Keep SYSTEM_INSTRUCTION as is - it already covers explaining dashboard features)
SYSTEM_INSTRUCTION = f"""You are the PYUSD CyberMatrix AI Assistant, integrated into a Streamlit dashboard that utilizes Google Cloud Platform's Blockchain RPC for Ethereum data and NewsAPI for news feeds.
Your purpose is to provide helpful and informative responses regarding PayPal USD (PYUSD), blockchain technology (especially Ethereum via GCP RPC), stablecoins, and potentially relate answers back to the functionalities of the dashboard when relevant.
Dashboard functionalities include: viewing live PYUSD transfers, analyzing volume/addresses, checking balances, looking up transactions, tracing blocks (advanced), viewing blockchain/PYUSD news (from NewsAPI), and simulating a bio-implant payment (conceptual). Blockchain data is sourced via GCP Blockchain RPC.
Be concise, accurate, and maintain a helpful, slightly cyberpunk/tech-focused tone consistent with the 'CyberMatrix' theme.
Do NOT invent information or transaction details. If asked about specific live data visible *only* on the dashboard (like current transfer feed details or a specific balance check result), explain that you don't have direct real-time access to the dashboard's *current state* but can explain *how* the user can find that information using the dashboard's tabs which query the GCP RPC, or provide *general* information about PYUSD/blockchain based on your knowledge.
You can answer general questions about:
- What PYUSD is, how it works, its issuer (Paxos/PayPal), backing, and features.
- Ethereum concepts (blocks, transactions, gas, contracts, events, ERC-20 tokens, Proof-of-Stake). Explain that the dashboard gets this data via GCP Blockchain RPC.
- Stablecoins in general (types, use cases, risks, regulation trends based on recent news from NewsAPI).
- How the different dashboard tabs (Live Transfers, Volume Analysis, Balance Check, Tx Lookup, Block Trace, News Feed, Implant Sim) function conceptually, noting their reliance on the GCP RPC for blockchain interactions and NewsAPI for news.
- Potential applications or implications of stablecoins like PYUSD.
Keep responses well-formatted, using markdown where appropriate.
Today's date is {datetime.now().strftime('%A, %B %d, %Y')}. Use this date for context.
"""

# --- Initialize Web3 Connection using GCP RPC ---
@st.cache_resource
def get_web3_connection(rpc_endpoint):
    if not rpc_endpoint: return None
    print(f"Attempting connection via RPC: {rpc_endpoint[:30]}...")
    try:
        # --- FIX: Example of setting timeout at provider level ---
        # Increased timeout to 60 seconds for potentially slow calls like tracing
        request_kwargs = {'timeout': 60}
        provider = Web3.HTTPProvider(rpc_endpoint, request_kwargs=request_kwargs)
        # --- END OF FIX ---
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

# --- Initialize PYUSD Contract ---
rpc_ok = w3 and w3.is_connected()
contract_ok = False
token_info = None # Initialize token_info

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
@st.cache_data(ttl=60)
def get_token_info(_contract):
    """Safely gets token info via the configured GCP RPC endpoint."""
    if not _contract or not w3 or not w3.is_connected(): return None
    try:
        name = _contract.functions.name().call()
        symbol = _contract.functions.symbol().call()
        decimals = _contract.functions.decimals().call()
        total_supply_raw = _contract.functions.totalSupply().call()
        total_supply = total_supply_raw / (10**decimals)
        return {"name": name, "symbol": symbol, "decimals": decimals, "total_supply": total_supply}
    except Exception as e:
        st.warning(f"⚠️ Token info fetch error (GCP RPC): {e}", icon="🔢")
        return None

@st.cache_data(ttl=30)
def get_address_balance(_contract, _address):
    """Safely gets PYUSD balance for an address via the configured GCP RPC endpoint."""
    if not _contract or not w3 or not w3.is_connected(): return None
    if not Web3.is_address(_address): st.error(f"❌ Invalid Address Format: {_address}"); return None
    try:
        cs_addr = Web3.to_checksum_address(_address)
        token_data_local = get_token_info(_contract)
        if not token_data_local: st.error("❌ Balance failed: Token info missing (via GCP RPC)."); return None
        decimals = token_data_local['decimals']
        balance_raw = _contract.functions.balanceOf(cs_addr).call()
        return balance_raw / (10**decimals)
    except Exception as e:
        st.warning(f"⚠️ Balance fetch error (GCP RPC) for {cs_addr[:10]}...: {e}", icon="💰")
        return None

def clean_markdown(text):
    """Removes specific markdown code block specifiers."""
    text = re.sub(r"```json\n", "```\n", text)
    # Add more cleaning rules if needed
    return text

@st.cache_resource
def configure_gemini(api_key):
    """Configures and returns the Gemini Generative Model."""
    if not api_key: return None
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash-latest', system_instruction=SYSTEM_INSTRUCTION,
                                   generation_config=genai.GenerationConfig(temperature=0.7)) # Safety defaults apply
        print("✅ Gemini model configured.")
        return model
    except Exception as e: st.error(f"🚨 **Gemini Error:** Config failed: {e}", icon="🔥"); return None

gemini_model = configure_gemini(GEMINI_API_KEY)

# NEWS API CHANGE: New function to fetch news from NewsAPI
@st.cache_data(ttl=1800) # Cache news for 30 minutes
def fetch_news_from_newsapi(api_key, keywords):
    """Fetches news from NewsAPI based on keywords."""
    if not api_key:
        st.warning("⚠️ NewsAPI key is missing. Cannot fetch news.", icon="📰")
        return []

    base_url = "https://newsapi.org/v2/everything"
    # Combine keywords for the 'q' parameter, use OR, quote phrases if needed
    query = " OR ".join(f'"{k}"' if " " in k else k for k in keywords)

    params = {
        'q': query,
        'apiKey': api_key,
        'language': 'en',
        'sortBy': 'publishedAt', # Get latest news first
        'pageSize': 25  # Limit number of results
    }
    print(f"Querying NewsAPI with parameters: {params}")

    processed_news = []
    try:
        response = requests.get(base_url, params=params, timeout=10) # Added timeout
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        data = response.json()

        if data.get("status") == "ok":
            articles = data.get("articles", [])
            print(f"NewsAPI returned {len(articles)} articles.")
            for article in articles:
                # Safely get data, provide defaults
                title = article.get('title', 'No Title Provided')
                link = article.get('url', '#')
                # Use 'description' as snippet, fallback to empty string
                snippet = article.get('description', article.get('content', 'No snippet available.'))
                if snippet and len(snippet) > 250: # Truncate long snippets
                     snippet = snippet[:247] + "..."

                publish_date_str = "Date unavailable"
                raw_date = article.get('publishedAt') # e.g., "2024-04-04T18:30:00Z"
                if raw_date:
                    try:
                        # Parse ISO 8601 format, make timezone-aware (UTC)
                        parsed_date_utc = datetime.strptime(raw_date, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
                        # Optional: Convert to local time if desired, otherwise display as UTC
                        # parsed_date_local = parsed_date_utc.astimezone(tz=None)
                        publish_date_str = parsed_date_utc.strftime('%B %d, %Y %H:%M UTC')
                    except (ValueError, TypeError):
                         # Fallback to raw string if parsing fails
                        publish_date_str = raw_date
                        print(f"Warning: Could not parse news date '{raw_date}'")


                processed_news.append({
                    'title': title,
                    'link': link,
                    'snippet': snippet,
                    'date': publish_date_str
                })
            print(f"Processed {len(processed_news)} news items from NewsAPI.")
            return processed_news
        else:
            # Handle API-specific errors (e.g., rate limit, bad key)
            api_message = data.get('message', 'Unknown API error')
            st.error(f"❌ NewsAPI Error: {api_message} (Code: {data.get('code', 'N/A')})", icon="📰")
            print(f"NewsAPI Error: Status={data.get('status')}, Code={data.get('code')}, Message={api_message}")
            return []

    except HTTPError as http_err:
        st.error(f"❌ HTTP Error fetching news: {http_err}", icon="📡")
        print(f"HTTP Error during NewsAPI request: {http_err}")
        return []
    except RequestException as req_err:
        st.error(f"❌ Network Error fetching news: {req_err}", icon="📡")
        print(f"RequestException during NewsAPI request: {req_err}")
        return []
    except Exception as e:
        st.error(f"❌ Error processing news feed: {e}", icon="📰")
        print(f"Exception during NewsAPI fetch/processing: {e}")
        import traceback
        traceback.print_exc()
        return []


@st.cache_data(ttl=600) # Cache events for 10 minutes
def get_recent_transfer_events_as_df(_w3, _contract, num_blocks=100):
    """Fetches recent Transfer events via GCP RPC and returns DataFrame."""
    if not _w3 or not _w3.is_connected() or not _contract:
        print("Event fetch precondition failed (w3/contract missing/disconnected).")
        return None
    token_data = get_token_info(_contract)
    if not token_data:
        st.error("❌ Cannot process events: Token info unavailable (via GCP RPC).")
        return None
    decimals = token_data['decimals']
    symbol = token_data['symbol']

    try:
        latest_block = _w3.eth.block_number
        from_block = max(0, latest_block - num_blocks + 1) # Fetch 'num_blocks' blocks
        to_block = latest_block
        print(f"Fetching 'Transfer' events from block {from_block} to {to_block}...")

        # --- FIX: Use snake_case arguments and remove request_kwargs ---
        transfer_events = _contract.events.Transfer.get_logs(
            from_block=from_block,  # Use snake_case
            to_block=to_block      # Use snake_case
            # Timeout is typically handled at the provider level, not here
        )
        # --- END OF FIX ---

        if not transfer_events:
            print(f"No 'Transfer' events found in blocks {from_block}-{to_block}.")
            return pd.DataFrame() # Return empty DataFrame if no events

        print(f"Found {len(transfer_events)} 'Transfer' events.")
        # Process events into a list of dictionaries
        event_list = []
        timestamps_cache = {} # Cache timestamps

        # Fetch unique block timestamps efficiently
        unique_block_nums = sorted(list(set(event['blockNumber'] for event in transfer_events)), reverse=True)
        print(f"Fetching timestamps for {len(unique_block_nums)} unique blocks...")
        with st.spinner(f"Fetching timestamps for {len(unique_block_nums)} blocks..."):
             for block_num in unique_block_nums:
                 if block_num not in timestamps_cache:
                     try:
                         # --- FIX: Remove request_kwargs ---
                         block = _w3.eth.get_block(block_num)
                         # --- END OF FIX ---
                         timestamps_cache[block_num] = datetime.utcfromtimestamp(block['timestamp']) if block and 'timestamp' in block else None
                     except Exception as ts_e:
                         print(f"Warn: Timestamp fetch error block {block_num}: {ts_e}")
                         timestamps_cache[block_num] = None # Mark as None on error

        print("Processing event details...")
        for event in transfer_events:
            value_pyusd = event['args']['value'] / (10**decimals)
            block_num = event['blockNumber']
            timestamp = timestamps_cache.get(block_num) # Use cached timestamp

            event_list.append({
                "Timestamp": timestamp,
                "Block": block_num,
                "Tx Hash": event['transactionHash'].hex(),
                "From": event['args']['from'],
                "To": event['args']['to'],
                f"Value ({symbol})": value_pyusd
                # Optional: Keep raw value if needed later
                # "Value_Raw": event['args']['value']
            })

        df = pd.DataFrame(event_list)
        if not df.empty:
            df.sort_values(by="Block", ascending=False, inplace=True) # Ensure sorted
            print(f"Created DataFrame with {len(df)} rows.")
        return df

    except HTTPError as http_err:
        st.error(f"❌ HTTP Error fetching events (Blocks {from_block}-{to_block}): {http_err}", icon="📡")
        try: st.error(f"Response: {http_err.response.text}")
        except Exception: pass
        return None
    except Exception as e:
        st.error(f"❌ Error processing events (Blocks {from_block}-{to_block}): {e} (Type: {type(e).__name__})", icon="🔥")
        print(f"Exception during event fetch/processing: {e}")
        import traceback
        traceback.print_exc()
        return None


def calculate_transfer_volume_from_df(df, symbol):
    """Calculates total PYUSD volume from the DataFrame, handling potential errors."""
    value_col = f"Value ({symbol})"
    if df is None or df.empty or value_col not in df.columns:
        return 0
    try:
        # Ensure column is numeric, coerce errors to NaN, then sum (NaNs are ignored)
        return pd.to_numeric(df[value_col], errors='coerce').sum()
    except Exception as e:
        print(f"Error calculating volume: {e}")
        return 0


# --- Plotting Functions ---
# Using updated plot functions from v1.5

def plot_transfers_per_block(df, symbol):
    """Generates a bar chart of transfer counts per block."""
    if df is None or df.empty or 'Block' not in df.columns: return None
    try:
        block_counts = df.groupby('Block').size().reset_index(name='Transfer Count')
        block_counts.sort_values('Block', inplace=True) # Sort by block number for chart
        fig = px.bar(block_counts, x='Block', y='Transfer Count',
                    title=f'PYUSD Transfer Count per Block (Last ~{df["Block"].nunique()} Blocks)',
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
                           title=f'Distribution of PYUSD Transfer Values (Last {len(df)} Transfers Scan)',
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
                    title=f'PYUSD Volume per Block (Last ~{df["Block"].nunique()} Blocks Scan)',
                    labels={'Block': 'Block Number', value_col: f'Volume (${symbol})'},
                    template='plotly_dark')
        fig.update_layout(bargap=0.2, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        fig.update_traces(marker_color='#ff9933', marker_line_color='#ccff00', marker_line_width=1.5, opacity=0.8)
        return fig
    except Exception as e: print(f"Error plotting volume per block: {e}"); return None

def plot_top_addresses_pie(df, symbol, direction='From', top_n=10):
    """Generates a pie chart for top sender or receiver addresses by volume."""
    value_col = f"Value ({symbol})"
    if df is None or df.empty or direction not in df.columns or value_col not in df.columns: return None
    token_data_local = get_token_info(pyusd_contract) # Needed for hover decimals
    if not token_data_local: token_data_local = {'decimals': 6} # Fallback decimals

    try:
        df[value_col] = pd.to_numeric(df[value_col], errors='coerce')
        df_clean = df.dropna(subset=[value_col, direction])
        # Group by address and sum the volume
        address_volume = df_clean.groupby(direction)[value_col].sum().reset_index()
        # Filter out zero/negative volume entries if any
        address_volume = address_volume[address_volume[value_col] > 0]
        address_volume.sort_values(value_col, ascending=False, inplace=True)
        if address_volume.empty: return None

        # Aggregate smaller amounts into 'Other'
        if len(address_volume) > top_n:
            top_df = address_volume.head(top_n)
            other_sum = address_volume.iloc[top_n:][value_col].sum()
            # Only add 'Other' if its value is significant enough to display
            if other_sum > 1e-9: # Threshold to avoid tiny 'Other' slices
                other_df = pd.DataFrame([{direction: 'Other Addresses', value_col: other_sum}])
                final_df = pd.concat([top_df, other_df], ignore_index=True)
            else: final_df = top_df
        else: final_df = address_volume

        # Create a display column with shortened addresses for the pie labels
        def shorten_address(addr):
            if isinstance(addr, str) and addr.startswith('0x') and len(addr) > 12: return f"{addr[:6]}...{addr[-4:]}"
            elif addr == 'Other Addresses': return addr
            return str(addr) # Handle potential non-address strings gracefully
        final_df[f'{direction} (Display)'] = final_df[direction].apply(shorten_address)

        direction_label = "Sender" if direction == 'From' else "Recipient"
        fig = px.pie(final_df, names=f'{direction} (Display)', values=value_col,
                    hover_data=[direction], # Show full address on hover
                    hole=0.3, # Donut chart
                    template='plotly_dark',
                    title=f'Top {min(top_n, len(address_volume))} {direction_label} Addresses by Volume (${symbol})')

        # Define a cyberpunk color sequence
        cyberpunk_colors = ['#00ffff', '#ff9933', '#99ffcc', '#ccff00', '#ff00ff', '#ffff00', '#ff4500', '#00ff7f', '#8a2be2', '#ffa500', '#ff69b4']
        fig.update_traces(textposition='inside', textinfo='percent', insidetextorientation='radial', # Show percentage inside
                          marker_colors=cyberpunk_colors, pull=[0.05] * len(final_df), # Pull slices slightly
                          # Custom hover template for better info display
                          hovertemplate = f"<b>Address:</b> %{{customdata[0]}}<br><b>Volume ({symbol}):</b> %{{value:,.{token_data_local['decimals']}f}}<br><b>Percentage:</b> %{{percent}}<extra></extra>")
        fig.update_layout(legend_title_text=f'{direction_label}s (Top {min(top_n, len(final_df))})', paper_bgcolor='rgba(0,0,0,0)',
                          legend=dict(traceorder="reversed", title=f'{direction_label}s', font=dict(size=10), itemsizing='constant'), # Improve legend appearance
                          uniformtext_minsize=8, uniformtext_mode='hide') # Auto-hide small text labels
        return fig
    except Exception as e:
        print(f"Error plotting top addresses pie: {e}"); import traceback; traceback.print_exc(); return None


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


# --- Streamlit App Layout ---
st.markdown("<h1 class='title'>🧬 PYUSD CyberMatrix Analytics 🔗</h1>", unsafe_allow_html=True)
# Updated subtitle to mention GCP RPC
st.markdown("<p class='gcp-subtitle'>Real-time insights, visualizations & sim bio-payments via Google Cloud Platform Blockchain RPC & NewsAPI</p>", unsafe_allow_html=True)


# Critical component checks
if not rpc_ok: st.warning("GCP RPC connection failed. Blockchain features unavailable.", icon="🚫")
elif not contract_ok: st.warning("PYUSD Contract initialization failed (via GCP RPC). Check address and ABI.", icon="📜")
else: st.success(f"✅ Connected via Google Cloud Platform Blockchain RPC & PYUSD contract initialized ({PYUSD_CONTRACT_ADDRESS[:10]}...).", icon="🔌")

if not NEWSAPI_API_KEY: st.warning("News Feed disabled - NewsAPI Key missing in secrets.", icon="📰")
if not GEMINI_API_KEY: st.warning("AI Assistant disabled - Gemini API Key missing in secrets.", icon="🤖")

# --- Sidebar ---
with st.sidebar:
    # Sidebar Title using the specific class from CSS
    st.markdown("<h2 class='cyber-matrix-title'>🟢 System Status & Info</h2>", unsafe_allow_html=True)

    # --- Connection Status Metrics ---
    st.metric(label="🛰️ GCP RPC Status", value="Connected" if rpc_ok else "Disconnected", label_visibility="visible") # Use the specific styled label
    st.metric(label="📰 NewsAPI Status", value="Active" if NEWSAPI_API_KEY else "Not Configured")
    st.metric(label="🤖 Gemini AI", value="Active" if gemini_model else "Not Configured")


    # --- Token Info (fetched once if possible) ---
    st.markdown("---")
    st.markdown("### PYUSD Token Details")
    if 'token_info' not in st.session_state: st.session_state.token_info = None
    if rpc_ok and contract_ok and st.session_state.token_info is None:
         print("Fetching token info for sidebar...")
         st.session_state.token_info = get_token_info(pyusd_contract) # Fetch and store

    token_info_sidebar = st.session_state.get('token_info') # Use stored value
    if token_info_sidebar:
        st.metric(label=f"Name", value=token_info_sidebar['name'])
        st.metric(label="Symbol", value=f"${token_info_sidebar['symbol']}")
        st.metric(label="Decimals", value=str(token_info_sidebar['decimals']))
        st.metric(label="Total Supply", value=f"{token_info_sidebar['total_supply']:,.{token_info_sidebar['decimals']}f} ${token_info_sidebar['symbol']}")
    else:
        if rpc_ok and contract_ok: st.warning("⚠️ Token info fetch failed.")
        else: st.metric(label="Token Info", value="Unavailable")


    # --- Network Info ---
    st.markdown("---")
    st.markdown("### Network Status (Ethereum)")
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

    # --- Resources Expander ---
    st.markdown("---")
    with st.expander("📚 Resources & Links", expanded=False):
        display_address = PYUSD_CONTRACT_ADDRESS if contract_ok else PYUSD_CONTRACT_ADDRESS_NON_CHECKSUM
        st.markdown(f"- [PYUSD Etherscan](https://etherscan.io/token/{display_address})")
        st.markdown("- [PayPal PYUSD Info](https://www.paypal.com/us/digital-wallet/pyusd)")
        st.markdown("- [Paxos PYUSD Page](https://paxos.com/pyusd/)")
        st.markdown("- **[GCP Blockchain RPC](https://cloud.google.com/web3/blockchain-rpc)** `(Used Here)`") # Emphasize GCP
        st.markdown("- **[NewsAPI.org](https://newsapi.org/)** `(Used for News Feed)`") # Add NewsAPI link
        st.markdown("- [Web3.py Docs](https://web3py.readthedocs.io/)")
        st.markdown("- [Streamlit Docs](https://docs.streamlit.io/)")
        st.markdown("- [GitHub Repo](https://github.com/MiChaelinzo/pyusd-transaction-insights/)")

    # --- Gemini AI Assistant (in Sidebar) ---
    st.markdown("---")
    st.markdown("<h3 class='ai-assistant-title'>🤖 Gemini AI Assistant</h3>", unsafe_allow_html=True)
    if not gemini_model: st.warning("AI Assistant offline. Check API Key & logs.", icon="🔌")
    else:
        # Initialize chat history and session state safely
        if "messages" not in st.session_state: st.session_state.messages = []
        if "gemini_chat" not in st.session_state:
             try:
                 st.session_state.gemini_chat = gemini_model.start_chat(history=[])
                 print("Gemini chat session started.")
             except Exception as chat_e:
                 st.error(f"Failed to start Gemini chat session: {chat_e}", icon="💬")
                 print(f"Error starting chat: {chat_e}")
                 st.session_state.gemini_chat = None

        # Display past messages within the sidebar context
        # Wrap in a container with a max height to make it scrollable if content overflows
        chat_display_container = st.container()
        # Optional: Set a fixed height for the chat history display area
        # chat_display_container.markdown('<div style="max-height: 400px; overflow-y: auto; padding-right: 10px;">', unsafe_allow_html=True)
        with chat_display_container:
            for msg in st.session_state.messages:
                with st.chat_message(msg["role"]):
                    # Use markdown, allow unsafe HTML ONLY if trusted content or necessary formatting
                    st.markdown(msg["content"], unsafe_allow_html=False) # Safer default
        # chat_display_container.markdown('</div>', unsafe_allow_html=True) # Close scrolling div if used

        # Chat input field - positioned at the bottom of the container naturally
        if prompt := st.chat_input("Ask about PYUSD, blockchain...", key="gemini_prompt", disabled=(not st.session_state.get("gemini_chat"))):
            if st.session_state.get("gemini_chat"):
                # Add user message to history and display immediately
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"): st.markdown(prompt)

                # Send prompt to Gemini and handle response
                try:
                    with st.spinner("🧠 Thinking..."):
                       # Use stream=False for simpler handling (waits for full response)
                        resp = st.session_state.gemini_chat.send_message(prompt, stream=False)

                        # Safely extract response text, check for blockage
                        cleaned_txt = "⚠️ Response generation issue." # Default error
                        finish_reason = "UNKNOWN"
                        safety_ratings = []
                        if resp.candidates:
                            candidate = resp.candidates[0]
                            finish_reason = candidate.finish_reason
                            safety_ratings = candidate.safety_ratings
                            if candidate.content and candidate.content.parts:
                                raw_txt = candidate.content.parts[0].text
                                cleaned_txt = clean_markdown(raw_txt)
                            elif finish_reason == 'SAFETY':
                                cleaned_txt = "⚠️ Response blocked likely due to safety filters."
                            # TODO: Add handling for other finish_reasons if necessary (e.g., RECITATION, MAX_TOKENS)

                        else: # Handle cases where response might be empty or malformed
                            print(f"Gemini response issue: No candidates found. Response: {resp}")

                        print(f"Gemini Finish Reason: {finish_reason}, Safety Ratings: {safety_ratings}")


                    # Display assistant response
                    with st.chat_message("assistant"): st.markdown(cleaned_txt)
                    # Add response to history
                    st.session_state.messages.append({"role": "assistant", "content": cleaned_txt})

                    # Rerun can sometimes help UI updates but can also clear input focus
                    # Consider carefully if needed. Maybe not needed if chat_input handles updates correctly.
                    # st.rerun() # Use st.rerun instead of experimental

                except Exception as e_ai:
                    st.error(f"AI Assistant Error: {e_ai}", icon="🔥")
                    print(f"Error during Gemini interaction: {e_ai}")
            else: st.error("Chat session is not available. Cannot send message.", icon="💬")


    # --- Sidebar Footer ---
    st.markdown("---")
    # Updated caption to be more informative
    st.caption(f"© {datetime.now().year} CyberMatrix v1.8 | GCP RPC {'OK' if rpc_ok else 'FAIL'} | NewsAPI {'OK' if NEWSAPI_API_KEY else 'NA'} | AI {'OK' if gemini_model else 'NA'}")


# --- Main Content Tabs ---
# Dynamically create tabs based on available services/connections
tab_list = []
if rpc_ok and contract_ok: tab_list.extend(["📊 Live Transfers", "📈 Volume & Address Analysis", "💰 Balance Check"])
if rpc_ok: tab_list.extend(["🧾 Tx Lookup", "🔬 Block Trace"])
if NEWSAPI_API_KEY: tab_list.append("📰 News Feed")
if rpc_ok and contract_ok: tab_list.append("💳 Implant Sim") # Keep Sim if base RPC/Contract OK

if not tab_list:
     st.error("🚨 No data tabs available. Check GCP RPC / Contract / NewsAPI Key status in secrets & logs.", icon="❌")
else:
    # Create the tabs
    tabs = st.tabs(tab_list)
    # Create a dictionary to easily access tabs by name
    tab_map = {name: tab for name, tab in zip(tab_list, tabs)}

# Helper function to safely get a tab context
def get_tab(name): return tab_map.get(name)

# Cache token info globally if fetched successfully for use in tabs
token_info = st.session_state.get('token_info') if 'token_info' in st.session_state else None
if token_info is None and rpc_ok and contract_ok: # Attempt fetch if sidebar missed it
    token_info = get_token_info(pyusd_contract)
    st.session_state['token_info'] = token_info

# --- Tab Implementations ---

# --- Tab: Live Transfers ---
if tab_ctx := get_tab("📊 Live Transfers"):
    with tab_ctx:
        # Using v1.5 implementation with session state, placeholders, button disabling
        st.header("📊 Live PYUSD Transfer Feed & Viz")
        st.markdown("<p class='tab-description'>Shows recent `Transfer` events fetched via Google Cloud RPC.</p>", unsafe_allow_html=True)

        col1_t, col2_t, col3_t = st.columns([1.5, 1.5, 3])
        with col1_t:
            # Increased max range slightly, adjusted step for finer control
            transfer_blocks_scan = st.slider(
                "Blocks to Scan", min_value=1, max_value=5, value=5, step=10, # Increased max/default
                key="transfer_blocks_viz", help="Number of recent blocks to scan for transfers. Larger ranges are slower."
            )
        with col2_t:
            # Disable button if core components aren't ready
            fetch_transfers_viz = st.button(
                 "🔄 Refresh Feed & Charts", key="fetch_transfers_viz",
                 disabled=not (rpc_ok and contract_ok), help="Requires active GCP RPC and PYUSD Contract."
            )
        with col3_t:
             # Display disabled status clearly
             if not (rpc_ok and contract_ok): st.caption("⛔ Disabled: Needs RPC & Contract")

        results_placeholder_transfers_viz = st.empty()
        # Initialize state variables if they don't exist
        if 'transfers_df' not in st.session_state: st.session_state.transfers_df = None
        if 'fetch_transfers_viz_pressed' not in st.session_state: st.session_state.fetch_transfers_viz_pressed = False

        # Show initial message or warning
        if not st.session_state.fetch_transfers_viz_pressed and st.session_state.transfers_df is None:
             if rpc_ok and contract_ok: results_placeholder_transfers_viz.info("Click 'Refresh' to load transfer data.")
             else: results_placeholder_transfers_viz.warning("Cannot fetch: RPC/Contract unavailable.", icon="🚫")

        # Handle button press: fetch data and update state
        if fetch_transfers_viz and rpc_ok and contract_ok:
            st.session_state.fetch_transfers_viz_pressed = True
            results_placeholder_transfers_viz.empty() # Clear placeholder
            with st.spinner(f"🛰️ Querying ~{transfer_blocks_scan} blocks for Transfer events via GCP RPC..."):
                events_df = get_recent_transfer_events_as_df(w3, pyusd_contract, num_blocks=transfer_blocks_scan)
                # Store result (even if None or empty) in session state
                st.session_state.transfers_df = events_df

        # Display results based on session state
        if st.session_state.fetch_transfers_viz_pressed or st.session_state.transfers_df is not None:
            df_transfers = st.session_state.get('transfers_df')
            if df_transfers is not None:
                results_placeholder_transfers_viz.empty() # Ensure placeholder is clear
                if not df_transfers.empty and token_info:
                    st.success(f"✅ Displaying {len(df_transfers)} transfers found in the last ~{transfer_blocks_scan} blocks scan.", icon="💻")
                    # Layout for charts
                    chart_col1, chart_col2 = st.columns(2)
                    with chart_col1:
                        with st.spinner("Generating block count chart..."): fig_bar = plot_transfers_per_block(df_transfers, token_info['symbol'])
                        if fig_bar: st.plotly_chart(fig_bar, use_container_width=True)
                        else: st.info("Not enough data or error generating block count chart.")
                    with chart_col2:
                        with st.spinner("Generating value distribution chart..."): fig_hist = plot_transfer_value_distribution(df_transfers, token_info['symbol'])
                        if fig_hist: st.plotly_chart(fig_hist, use_container_width=True)
                        else: st.info("Not enough data or error generating value distribution chart.")

                    st.markdown("---")
                    st.subheader("Recent Transfers Table")
                    # Define columns to display, ensure they exist
                    display_cols = ["Timestamp", "Block", "Tx Hash", "From", "To", f"Value ({token_info['symbol']})"]
                    valid_display_cols = [col for col in display_cols if col in df_transfers.columns]
                    # Create a copy for display modifications
                    df_display = df_transfers[valid_display_cols].head(50).copy()
                    # Format timestamp column if present
                    if "Timestamp" in valid_display_cols:
                         try: df_display['Timestamp'] = pd.to_datetime(df_display['Timestamp'], errors='coerce').dt.strftime('%Y-%m-%d %H:%M:%S UTC')
                         except Exception: pass # Ignore formatting errors
                    # Display dataframe
                    st.dataframe(df_display, hide_index=True, use_container_width=True)

                elif df_transfers.empty: st.info(f"ℹ️ No PYUSD Transfer events found in the scanned {transfer_blocks_scan} blocks.")
                elif not token_info: st.warning("⚠️ Cannot display values/charts correctly, token info missing.")
            # else: Error during fetch handled by get_recent_transfer_events_as_df


# --- Tab: Volume & Address Analysis ---
if tab_ctx := get_tab("📈 Volume & Address Analysis"):
    with tab_ctx:
        # Using v1.5 implementation logic
        st.header("📈 PYUSD Volume & Address Analysis")
        st.markdown("<p class='tab-description'>Analyzes transfer volume and top addresses over a block range using Google Cloud RPC.</p>", unsafe_allow_html=True)

        col1_vol, col2_vol, col3_vol = st.columns([1.5, 1.5, 3])
        with col1_vol:
            volume_blocks_scan = st.slider(
                "Blocks for Analysis", min_value=1, max_value=5, value=5, step=50, # Increased range
                key="volume_blocks_addr", help="Blocks for volume/address analysis. Larger ranges are slower."
            )
        with col2_vol:
            top_n_addresses = st.number_input("Top N Addresses (Pie)", min_value=3, max_value=15, value=7, step=1, key="top_n_pie")
        with col3_vol:
            analyze_volume_addr = st.button(
                "⚙️ Analyze Volume & Addresses", key="analyze_vol_addr",
                disabled=not (rpc_ok and contract_ok), help="Requires active GCP RPC and PYUSD Contract."
            )
            if not (rpc_ok and contract_ok): st.caption("⛔ Disabled: Needs RPC & Contract")

        results_placeholder_volume_addr = st.empty()
        # Initialize state
        if 'volume_df' not in st.session_state: st.session_state.volume_df = None
        if 'analyze_volume_addr_pressed' not in st.session_state: st.session_state.analyze_volume_addr_pressed = False

        # Initial message
        if not st.session_state.analyze_volume_addr_pressed and st.session_state.volume_df is None:
             if rpc_ok and contract_ok: results_placeholder_volume_addr.info("Select block range and click 'Analyze'.")
             else: results_placeholder_volume_addr.warning("Cannot analyze: RPC/Contract unavailable.", icon="🚫")

        # Handle button press
        if analyze_volume_addr and rpc_ok and contract_ok:
            st.session_state.analyze_volume_addr_pressed = True
            results_placeholder_volume_addr.empty()
            with st.spinner(f"⚙️ Aggregating transfer data over ~{volume_blocks_scan} blocks..."):
                # Fetch data - use the same function as the live feed
                vol_df = get_recent_transfer_events_as_df(w3, pyusd_contract, num_blocks=volume_blocks_scan)
                st.session_state.volume_df = vol_df # Store result

        # Display results from state
        if st.session_state.analyze_volume_addr_pressed or st.session_state.volume_df is not None:
            df_volume = st.session_state.get('volume_df')
            if df_volume is not None:
                 results_placeholder_volume_addr.empty()
                 if not df_volume.empty and token_info:
                     # Calculate total volume
                     total_vol = calculate_transfer_volume_from_df(df_volume, token_info['symbol'])
                     st.metric(label=f"Total Volume ({token_info['symbol']}) | Last ~{volume_blocks_scan} Blocks",
                               value=f"{total_vol:,.{token_info['decimals']}f}",
                               help=f"Based on {len(df_volume):,} transfers found in the scan.")
                     st.markdown("---")

                     # Layout for charts
                     chart_col1_vol, chart_col2_vol = st.columns(2)
                     with chart_col1_vol:
                         # Volume per Block Bar Chart
                         with st.spinner("Generating volume/block chart..."): fig_vol_bar = plot_volume_per_block(df_volume, token_info['symbol'])
                         if fig_vol_bar: st.plotly_chart(fig_vol_bar, use_container_width=True)
                         else: st.info("No data or error generating volume/block chart.")
                         # Top Senders Pie Chart
                         with st.spinner(f"Generating top {top_n_addresses} senders chart..."): fig_pie_from = plot_top_addresses_pie(df_volume, token_info['symbol'], 'From', top_n_addresses)
                         if fig_pie_from: st.plotly_chart(fig_pie_from, use_container_width=True)
                         else: st.info("No data or error generating top senders chart.")

                     with chart_col2_vol:
                         # Top Receivers Pie Chart
                         with st.spinner(f"Generating top {top_n_addresses} receivers chart..."): fig_pie_to = plot_top_addresses_pie(df_volume, token_info['symbol'], 'To', top_n_addresses)
                         if fig_pie_to: st.plotly_chart(fig_pie_to, use_container_width=True)
                         else: st.info("No data or error generating top receivers chart.")
                         # Placeholder for potential future chart
                         st.empty()

                 elif df_volume.empty: st.info(f"ℹ️ No PYUSD Transfer events found in the scanned {volume_blocks_scan} blocks.")
                 elif not token_info: st.warning("⚠️ Cannot calculate volume or generate charts, token info missing.")
            # else: Error handled by fetch function


# --- Tab: Address Balance ---
if tab_ctx := get_tab("💰 Balance Check"):
    with tab_ctx:
        # Using v1.5 implementation logic
        st.header("💰 Check PYUSD Address Balance")
        st.markdown("<p class='tab-description'>Queries the current PYUSD balance for a given address using Google Cloud RPC.</p>", unsafe_allow_html=True)
        address_to_check = st.text_input("Ethereum Address", key="balance_address", placeholder="0x...", label_visibility="collapsed")

        # Button disabled if prerequisites not met
        disable_balance_check = not (rpc_ok and contract_ok and token_info)
        tooltip_balance = "Requires active RPC, Contract & Token Info" if disable_balance_check else "Query PYUSD balance"

        if st.button("Check Balance", key="check_balance_btn", disabled=disable_balance_check, help=tooltip_balance):
            address_to_check_cleaned = address_to_check.strip() # Remove leading/trailing whitespace
            if address_to_check_cleaned and Web3.is_address(address_to_check_cleaned):
                with st.spinner(f"🔍 Querying balance for `{address_to_check_cleaned[:10]}...` via GCP RPC..."):
                    # Use the helper function which includes error handling
                    balance = get_address_balance(pyusd_contract, address_to_check_cleaned)
                    if balance is not None: # Check if function returned a value (not None on error)
                         cs_addr_disp = Web3.to_checksum_address(address_to_check_cleaned) # Show checksummed address
                         st.metric(label=f"Balance: {cs_addr_disp}",
                                   value=f"{balance:,.{token_info['decimals']}f} ${token_info['symbol']}")
                    # Error/Warning displayed within get_address_balance function
            elif address_to_check_cleaned: # Input provided but invalid format
                st.error(f"❌ Invalid Ethereum Address Format: `{address_to_check}`")
            else: # No input provided
                st.warning("⚠️ Please enter an Ethereum address.")

        # Show disabled status clearly
        if disable_balance_check: st.caption("⛔ Balance Check Disabled: Requires RPC, Contract & Token Info.")


# --- Tab: Transaction Lookup ---
if tab_ctx := get_tab("🧾 Tx Lookup"):
    with tab_ctx:
        # Using v1.5 implementation logic
        st.header("🧾 Transaction Details Lookup")
        st.markdown("<p class='tab-description'>Retrieves Ethereum transaction details and receipt using Google Cloud RPC.</p>", unsafe_allow_html=True)
        tx_hash_lookup = st.text_input("Transaction Hash", key="tx_hash_lookup", placeholder="0x...", label_visibility="collapsed")

        # Disable button if RPC is not available
        disable_tx_lookup = not rpc_ok
        tooltip_tx = "Requires active GCP RPC Connection" if disable_tx_lookup else "Lookup Transaction Hash"

        if st.button("🔍 Lookup Tx", key="lookup_tx_btn", disabled=disable_tx_lookup, help=tooltip_tx):
            tx_hash_lookup_cleaned = tx_hash_lookup.strip() # Clean input
            # Validate format before sending to helper
            if tx_hash_lookup_cleaned and isinstance(tx_hash_lookup_cleaned, str) and tx_hash_lookup_cleaned.startswith('0x') and len(tx_hash_lookup_cleaned) == 66:
                with st.spinner(f"⏳ Fetching details for `{tx_hash_lookup_cleaned[:10]}...` via GCP RPC..."):
                    # Use helper function which includes error handling and pending state
                    tx_details = get_tx_details(w3, tx_hash_lookup_cleaned)

                if tx_details:
                    # Display status message based on receipt status
                    status = tx_details.get("Status", ""); short_hash = f"{tx_hash_lookup_cleaned[:10]}...{tx_hash_lookup_cleaned[-8:]}"
                    if status == "⏳ Pending": st.info(f"⏳ Tx `{short_hash}` is pending confirmation.", icon="🕒")
                    elif status == "✅ Success": st.success(f"✅ Tx `{short_hash}` details retrieved successfully.")
                    elif status == "❌ Failed": st.error(f"❌ Tx `{short_hash}` failed execution.", icon="💥")
                    else: st.info(f"ℹ️ Tx `{short_hash}` details retrieved (Status: {status}).") # Fallback for unexpected status

                    # Display details in an expander
                    with st.expander("Show Transaction Details", expanded=True):
                        cols_tx = st.columns(2); col_idx = 0
                        for k, v in tx_details.items():
                             # Skip None values except for 'Contract Address Created' which can be None
                             if v is None and k != "Contract Address Created": continue
                             display_val = str(v) if v is not None else "None" # Ensure string conversion
                             # Distribute items between two columns
                             cols_tx[col_idx % 2].text(f"{k}:")
                             cols_tx[col_idx % 2].code(display_val, language='text')
                             col_idx += 1
                    # Add Etherscan link
                    st.markdown(f"👀 [View Transaction on Etherscan](https://etherscan.io/tx/{tx_hash_lookup_cleaned})")
                # Error is handled within get_tx_details function
            elif tx_hash_lookup_cleaned: # Input provided but invalid format
                st.error(f"❌ Invalid Transaction Hash Format. Should start with '0x' and be 66 chars long.")
            else: # No input provided
                st.warning("⚠️ Please enter a Transaction Hash.")

        # Display disabled status clearly
        if disable_tx_lookup: st.caption("⛔ Transaction Lookup Disabled: Requires GCP RPC Connection.")


# --- Tab: Block Trace Explorer ---
if tab_ctx := get_tab("🔬 Block Trace"):
    with tab_ctx:
        # Using v1.5 implementation logic
        st.header("🔬 Block Trace Explorer (Advanced)")
        st.markdown("<p class='tab-description'>Uses Google Cloud RPC `debug_traceBlock*` methods to inspect executions within a block.</p>", unsafe_allow_html=True)
        st.warning("""⚠️ **Note:** Requires specific RPC support (e.g., enabling the `debug` namespace on your GCP endpoint). Tracing can be slow and resource-intensive. Results depend heavily on the chosen tracer.""", icon="🛠️")

        # --- FIX: Remove label_visibility parameter to show the label ---
        block_id_input = st.text_input(
            "Block Number / Hash / 'latest'", # Label will now be visible
            "latest",
            key="trace_block_id",
            # label_visibility="collapsed", # REMOVED THIS LINE
            help="Enter block number, hash (0x...), or a tag like 'latest'"
        )
        # --- END OF FIX ---

        # Disable button if RPC not available
        disable_trace = not rpc_ok        
        tooltip_trace = "Requires active GCP RPC Connection" if disable_trace else "Request trace for the specified block"

        if st.button("🔬 Get Block Trace", key="get_trace_btn", disabled=disable_trace, help=tooltip_trace):
            block_id_input_cleaned = block_id_input.strip()
            if block_id_input_cleaned:
                with st.spinner(f"⏳ Requesting trace for block `{block_id_input_cleaned}` via GCP RPC..."):
                    # Use helper function which includes input validation and error handling
                    block_trace = get_block_trace(w3, block_id_input_cleaned)

                if block_trace is not None:
                    st.success(f"✅ Trace data received for block `{block_id_input_cleaned}`.")
                    # Display structure depends on the tracer used (e.g., callTracer returns nested calls, structTracer returns steps)
                    if isinstance(block_trace, list) and block_trace:
                         st.info(f"Found {len(block_trace)} items/transactions in the trace.")
                         collapse = st.checkbox("Collapse Trace JSON?", True, key="collapse_trace")
                         st.json(block_trace[:25], expanded=(not collapse)) # Show first few items
                         if len(block_trace) > 25: st.info(f"Showing first 25 / {len(block_trace)} trace items.")
                    elif isinstance(block_trace, dict): # Some tracers might return a single dict
                         collapse = st.checkbox("Collapse Trace JSON?", True, key="collapse_trace")
                         st.json(block_trace, expanded=(not collapse))
                    elif isinstance(block_trace, list): # Empty list case
                        st.info("ℹ️ Empty trace list received (e.g., no transactions in block or tracer issue).")
                    else: # Unexpected format
                        st.warning("⚠️ Unexpected trace data format received:"); st.json(block_trace)

                    # Add download button for the full trace
                    try:
                        # Handle potential unserializable types during JSON dump
                        trace_str = json.dumps(block_trace, indent=2, default=lambda o: f"<unserializable: {type(o).__name__}>")
                        st.download_button(label="📥 Download Full Trace (JSON)", data=trace_str, file_name=f"trace_{block_id_input_cleaned}.json", mime="application/json")
                    except Exception as json_e: st.error(f"Failed to prepare trace data for download: {json_e}")
                # Error messages are handled within get_block_trace function
            else: st.warning("⚠️ Please enter a block identifier (number, hash, or tag).")

        # Display disabled status clearly
        if disable_trace: st.caption("⛔ Block Trace Disabled: Requires GCP RPC Connection.")


# --- Tab: News Feed --- NEWS API CHANGE: Updated Implementation
if tab_ctx := get_tab("📰 News Feed"): # Check if tab exists (depends on API Key)
    with tab_ctx:
        st.header("📰 Latest Blockchain & PYUSD News")
        st.markdown("<p class='tab-description'>Recent news related to PYUSD, stablecoins, and blockchain, fetched directly from NewsAPI.</p>", unsafe_allow_html=True)
        st.caption(f"News fetched around {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}. Data cached for 30 minutes.")

        # Define keywords for NewsAPI - consider making these adjustable if desired
        news_keywords = [
            "PYUSD", "PayPal Stablecoin", "blockchain", "ethereum",
            "stablecoin regulation", "crypto payments", "web3 adoption", "Paxos"
        ]
        st.info(f"**Searching NewsAPI for keywords:** `{', '.join(news_keywords)}`")

        # --- Refresh Button ---
        # Tooltip explains functionality or disabled state
        news_refresh_disabled = not NEWSAPI_API_KEY
        news_refresh_tooltip = "NewsAPI Key missing in secrets. Add 'newsapi.api_key'." if news_refresh_disabled else "Fetch latest news from NewsAPI (clears cache)"

        if st.button("🔄 Refresh News Feed", key="refresh_news_btn", disabled=news_refresh_disabled, help=news_refresh_tooltip):
             # Clear relevant cache(s). Clearing all data cache is simplest.
             st.cache_data.clear()
             st.success("News cache cleared. Fetching fresh results from NewsAPI...", icon="🔄")
             # Rerun to trigger the fetch below with cleared cache
             st.rerun() # Use st.rerun instead of experimental version

        # --- Display Feed ---
        if news_refresh_disabled:
            st.warning("News feed disabled. Please configure your NewsAPI key in Streamlit secrets to enable this feature.", icon="🔒")
        else:
            # Fetch news using the dedicated function
            with st.spinner("📰 Loading news feed from NewsAPI..."):
                news_items = fetch_news_from_newsapi(NEWSAPI_API_KEY, news_keywords)

            # Display the fetched news items
            if news_items:
                st.markdown(f"Found **{len(news_items)}** relevant news articles:")
                st.markdown("---") # Divider before first item
                for item in news_items:
                     # Use markdown with custom CSS classes for styling
                     st.markdown(f"""
                     <div class="news-item">
                         <h3><a href="{item['link']}" target="_blank" title="{item.get('snippet', 'Click to read more')}">{item['title']}</a></h3>
                         <p>{item.get('snippet', 'No snippet available.')}</p>
                         <div class="news-date">📅 Published: {item.get('date', 'Date unavailable')}</div>
                     </div>
                     """, unsafe_allow_html=True)
                     st.markdown("---") # Divider between items
            elif NEWSAPI_API_KEY: # Only show 'no results' if the key IS present but API returned nothing
                 st.info("No recent news items found matching the specified keywords from NewsAPI. Try refreshing later or adjust keywords.")
            # If API key was missing, the button and initial warning cover the disabled state.


# --- Tab: Simulated Implant Payment ---
if tab_ctx := get_tab("💳 Implant Sim"):
     with tab_ctx:
        st.header("💳 Simulate Bio-Implant Payment")
        st.markdown("<p class='tab-description'>Conceptual simulation of a PYUSD payment initiated via biochip. Uses Google Cloud RPC for network data (gas, nonce) and contract info.</p>", unsafe_allow_html=True)
        st.info(f"Simulating payment for Implant ID: `{SIMULATED_IMPLANT_ID}`", icon="🆔")

        col1_sim, col2_sim = st.columns(2)
        with col1_sim:
            merchant_addr = st.text_input(
                 "Merchant Wallet Address (Simulated Recipient)",
                 "0x6c3ea9036406852006290770bedfcaba0e23a0e8", # Example address
                 key="merchant_sim", help="Enter the Ethereum address of the simulated merchant."
            )
            # Ensure number input uses appropriate precision based on decimals
            display_decimals = token_info['decimals'] if token_info else 6
            amount_sim = st.number_input(
                 f"Amount (PYUSD - {display_decimals} decimals)",
                 min_value= (1 / (10**display_decimals)) if token_info else 0.000001, # Smallest possible unit
                 value=1.50,
                 step= 1.0 / (10**(display_decimals-1)) if token_info else 0.01, # Step appropriate for decimals
                 format=f"%.{display_decimals}f", # Format according to token decimals
                 key="amount_sim",
                 help="Enter the amount of PYUSD to simulate sending."
             )
        with col2_sim:
            st.markdown("<br/>", unsafe_allow_html=True) # Vertical spacing
            # Button disabled if prerequisites not met
            disable_sim = not (rpc_ok and contract_ok and token_info)
            tooltip_sim = "Requires active RPC, Contract & Token Info" if disable_sim else "Simulate Implant Tap & Authorize Payment"

            if st.button("⚡ Tap Implant & Authorize Payment (Sim)", key="simulate_pay_btn", disabled=disable_sim, help=tooltip_sim):
                # --- Simulation Steps ---
                implant_id = simulate_nfc_read()
                user_wallet = get_user_wallet_address(implant_id)

                # Validate inputs before proceeding
                merchant_valid = Web3.is_address(merchant_addr.strip())
                amount_valid = isinstance(amount_sim, (int, float)) and amount_sim > 0

                if user_wallet and merchant_valid and amount_valid:
                    cs_merchant = Web3.to_checksum_address(merchant_addr.strip()) # Use checksummed, cleaned address
                    # Call simulation function which includes spinner & info messages
                    tx_sim = simulate_transaction_creation(user_wallet, cs_merchant, amount_sim, w3, pyusd_contract)

                    if tx_sim: # Check if simulation was successful
                        st.success("✅ Sim Auth & Transaction Compilation Sequence Complete!")
                        # Display simulated transaction details
                        with st.expander("Simulated Transaction Data (Ready for Signing)", expanded=True): st.json(tx_sim)
                        # Simulate the trace based on the compiled Tx
                        trace_sim = simulate_gcp_trace_transaction(tx_sim)
                        with st.expander("Simulated GCP RPC Trace (`debug_traceTransaction` Result)", expanded=False):
                            try:
                                 # Dump trace to JSON string for display
                                 trace_sim_str = json.dumps(trace_sim, indent=2, default=lambda o: f"<unserializable: {type(o).__name__}>")
                                 st.code(trace_sim_str, language="json")
                                 st.caption("Note: Trace structure is a simplified representation.")
                            except Exception as json_e_sim: st.error(f"Cannot display simulated trace: {json_e_sim}"); st.json(trace_sim) # Fallback display
                # --- Handle Validation Errors ---
                elif not user_wallet: pass # Error is shown by get_user_wallet_address
                elif not merchant_valid: st.error(f"❌ Invalid Merchant Address Format: `{merchant_addr}`")
                elif not amount_valid: st.error(f"❌ Invalid or Zero Amount Entered.")

            # Display disabled status clearly
            elif disable_sim: st.caption("⛔ Simulation Disabled: Requires RPC, Contract & Token Info.")

        st.markdown("---")
        st.caption("Disclaimer: This is a conceptual simulation only. No real assets are transferred, and no actual transaction is sent to the network.")

# --- Footer ---
st.markdown("---")
# Updated footer version with year and credit
st.markdown(f"<p style='text-align:center; font-size: 0.9em; opacity: 0.7;'>© {datetime.now().year} PYUSD CyberMatrix | Developed by MiChaelinzo | Dashboard v1.8 [GCP RPC + NewsAPI + v1.3 Sidebar Style]</p>", unsafe_allow_html=True)
# --- End of Streamlit App Script ---
print("Streamlit app script finished loading.")
