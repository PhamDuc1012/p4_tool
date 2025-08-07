"""
P4 command operations
Handles all Perforce commands and validations
"""
import subprocess
import re
from config.p4_config import get_client_name

def run_cmd(cmd, input_text=None):
    """Execute command and return output"""
    result = subprocess.run(cmd, input=input_text, capture_output=True, text=True, shell=True)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {cmd}\n{result.stderr}")
    return result.stdout.strip()

def validate_depot_path(depot_path):
    """Validate if depot path exists in Perforce"""
    try:
        result = subprocess.run(f"p4 files {depot_path}", capture_output=True, text=True, shell=True)
        if result.returncode != 0 or "no such file" in result.stderr.lower():
            return False
        return True
    except:
        return False

def create_changelist(log_callback):
    """Create pending changelist"""
    log_callback("[STEP 1] Creating pending changelist...")
    changelist_spec = run_cmd("p4 change -o")
    new_spec = re.sub(r"<enter description here>", "Auto changelist - Sync and update LMKD/Chimera", changelist_spec)
    changelist_result = run_cmd("p4 change -i", input_text=new_spec)
    changelist_id = re.search(r"Change (\d+)", changelist_result).group(1)
    log_callback(f"[OK] Created changelist {changelist_id}")
    return changelist_id

def create_changelist_silent(description="Auto changelist"):
    """Create pending changelist without logging"""
    changelist_spec = run_cmd("p4 change -o")
    new_spec = re.sub(r"<enter description here>", description, changelist_spec)
    changelist_result = run_cmd("p4 change -i", input_text=new_spec)
    changelist_id = re.search(r"Change (\d+)", changelist_result).group(1)
    return changelist_id

def map_client(beni_depot, vince_depot, flumen_depot, log_callback):
    """Map multiple depots to client spec"""
    client_name = get_client_name()
    if not client_name:
        raise RuntimeError("Client name not initialized. Please check P4 configuration.")
    
    log_callback("[STEP 2] Mapping BENI, VINCE and FLUMEN to client spec...")
    client_spec = run_cmd("p4 client -o")
    lines = client_spec.splitlines()
    new_lines = []
    for line in lines:
        if beni_depot in line or vince_depot in line or flumen_depot in line:
            continue
        new_lines.append(line)
    new_lines.append(f"\t{beni_depot}\t//{client_name}/{beni_depot[2:]}")
    new_lines.append(f"\t{vince_depot}\t//{client_name}/{vince_depot[2:]}")
    new_lines.append(f"\t{flumen_depot}\t//{client_name}/{flumen_depot[2:]}")
    new_spec = "\n".join(new_lines)
    run_cmd("p4 client -i", input_text=new_spec)
    log_callback("[OK] Mapping completed.")

def map_client_two_paths(target_depot, vince_depot, log_callback):
    """Map two depots to client spec"""
    client_name = get_client_name()
    if not client_name:
        raise RuntimeError("Client name not initialized. Please check P4 configuration.")
    
    target_name = "BENI" if "beni" in target_depot.lower() else "FLUMEN" if "flumen" in target_depot.lower() else "TARGET"
    log_callback(f"[STEP 2] Mapping {target_name} and VINCE to client spec...")
    client_spec = run_cmd("p4 client -o")
    lines = client_spec.splitlines()
    new_lines = []
    for line in lines:
        if target_depot in line or vince_depot in line:
            continue
        new_lines.append(line)
    new_lines.append(f"\t{target_depot}\t//{client_name}/{target_depot[2:]}")
    new_lines.append(f"\t{vince_depot}\t//{client_name}/{vince_depot[2:]}")
    new_spec = "\n".join(new_lines)
    run_cmd("p4 client -i", input_text=new_spec)
    log_callback("[OK] Mapping completed.")

def map_single_depot(depot_path, log_callback=None):
    """Map single depot to client spec"""
    client_name = get_client_name()
    if not client_name:
        raise RuntimeError("Client name not initialized. Please check P4 configuration.")
    
    depot_name = "BENI" if "beni" in depot_path.lower() else "FLUMEN" if "flumen" in depot_path.lower() else "DEPOT"
    if log_callback:
        log_callback(f"[MAPPING] Mapping {depot_name} to client spec...")
    
    client_spec = run_cmd("p4 client -o")
    lines = client_spec.splitlines()
    new_lines = []
    for line in lines:
        if depot_path in line:
            continue
        new_lines.append(line)
    new_lines.append(f"\t{depot_path}\t//{client_name}/{depot_path[2:]}")
    new_spec = "\n".join(new_lines)
    run_cmd("p4 client -i", input_text=new_spec)
    
    if log_callback:
        log_callback("[OK] Mapping completed.")

def map_two_depots_silent(depot1, depot2):
    """Map two depots to client spec without logging"""
    client_name = get_client_name()
    if not client_name:
        raise RuntimeError("Client name not initialized. Please check P4 configuration.")
    
    client_spec = run_cmd("p4 client -o")
    lines = client_spec.splitlines()
    new_lines = []
    for line in lines:
        if depot1 in line or depot2 in line:
            continue
        new_lines.append(line)
    new_lines.append(f"\t{depot1}\t//{client_name}/{depot1[2:]}")
    new_lines.append(f"\t{depot2}\t//{client_name}/{depot2[2:]}")
    new_spec = "\n".join(new_lines)
    run_cmd("p4 client -i", input_text=new_spec)

def sync_file(depot_path, log_callback):
    """Sync file from depot"""
    log_callback(f"[SYNC] Syncing {depot_path}...")
    run_cmd(f"p4 sync {depot_path}")
    log_callback("[OK] Synced.")

def sync_file_silent(depot_path):
    """Sync file from depot without logging"""
    run_cmd(f"p4 sync {depot_path}")

def checkout_file(depot_path, changelist_id, log_callback):
    """Checkout file for editing"""
    log_callback(f"[CHECKOUT] Checking out {depot_path}...")
    run_cmd(f"p4 edit -c {changelist_id} {depot_path}")
    log_callback("[OK] Checked out.")

def checkout_file_silent(depot_path, changelist_id):
    """Checkout file for editing without logging"""
    run_cmd(f"p4 edit -c {changelist_id} {depot_path}")