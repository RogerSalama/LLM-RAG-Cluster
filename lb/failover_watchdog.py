import time
import subprocess
import ctypes
import sys
import os

# --- CONFIGURATION (UPDATE THESE) ---
MASTER_A_IP = "10.2.213.176"
VIRTUAL_IP = "10.2.213.200"
# Use the full name you found: "ZeroTier One [154a350c86...]"
INTERFACE_NAME = "ZeroTier One [154a350c86abc123]" 

# --- TUNING FOR 1000+ USERS ---
# How many missed pings before we claim the IP? 
# Under 1k load, we use a higher number to avoid "false failovers".
FAIL_THRESHOLD = 3
# How often to check (seconds)
CHECK_INTERVAL = 0.5 

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def ping_master_a():
    """
    Sends a single ping with a 500ms timeout.
    """
    # -n 1: One packet, -w 500: Wait 500ms for reply
    result = subprocess.run(
        ["ping", "-n", "1", "-w", "500", MASTER_A_IP], 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE
    )
    return result.returncode == 0

def claim_virtual_ip():
    print(f"\n[!!!] FAILOVER TRIGGERED [!!!]")
    print(f"Master A ({MASTER_A_IP}) is unresponsive. Claiming {VIRTUAL_IP}...")
    
    # The command to bind the "Mask" to this laptop
    cmd = f'netsh interface ipv4 add address name="{INTERFACE_NAME}" address={VIRTUAL_IP} mask=255.255.255.0'
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"[SUCCESS] Cluster Mask {VIRTUAL_IP} is now active on this node.")
        print("Master B is now the PRIMARY Master.")
    else:
        print(f"[ERROR] Failed to claim IP. Reason: {result.stderr}")

def start_monitor():
    if not is_admin():
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("ERROR: This script MUST be run as ADMINISTRATOR.")
        print("Right-click PowerShell and select 'Run as Administrator'.")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        return

    print(f"--- RAG CLUSTER WATCHDOG STARTED ---")
    print(f"Monitoring: {MASTER_A_IP}")
    print(f"Interface:  {INTERFACE_NAME}")
    print(f"Threshold:  {FAIL_THRESHOLD} missed pings")
    print(f"------------------------------------")

    failed_pings = 0
    
    while True:
        if ping_master_a():
            # ANTI-FLAP LOGIC:
            # If we get a success, we don't reset to 0 immediately.
            # We decrement by 2. This way, if the connection is 
            # "jittery," we stay close to the threshold.
            if failed_pings > 0:
                failed_pings = max(0, failed_pings - 2)
        else:
            failed_pings += 1
            print(f"[WARNING] Heartbeat missed. Status: ({failed_pings}/{FAIL_THRESHOLD})")
            
        if failed_pings >= FAIL_THRESHOLD:
            claim_virtual_ip()
            break # Failover complete, exit monitoring loop
            
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    try:
        start_monitor()
    except KeyboardInterrupt:
        print("\nWatchdog stopped by user.")