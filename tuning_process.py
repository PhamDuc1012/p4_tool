"""
Tuning process implementation
Handles property loading, comparison, and modification  
"""
import re
from core.p4_operations import (
    validate_depot_path, create_changelist_silent, map_single_depot,
    map_two_depots_silent, sync_file_silent, checkout_file_silent
)
from core.file_operations import create_backup
from config.p4_config import depot_to_local_path

def load_properties_for_tuning(beni_depot_path, flumen_depot_path, 
                              progress_callback=None, error_callback=None, info_callback=None):
    """Load and compare properties from BENI and FLUMEN files"""
    try:
        # Validate paths first
        process_beni = False
        process_flumen = False
        
        if beni_depot_path and beni_depot_path.startswith("//"):
            if validate_depot_path(beni_depot_path):
                process_beni = True
            else:
                if error_callback:
                    error_callback("Path Not Found", f"BENI depot path does not exist: {beni_depot_path}")
                return None
        
        if flumen_depot_path and flumen_depot_path.startswith("//"):
            if validate_depot_path(flumen_depot_path):
                process_flumen = True
            else:
                if error_callback:
                    error_callback("Path Not Found", f"FLUMEN depot path does not exist: {flumen_depot_path}")
                return None
        
        if not process_beni and not process_flumen:
            if error_callback:
                error_callback("No Valid Paths", "At least one valid depot path is required.")
            return None
        
        if progress_callback:
            progress_callback(20)
        
        # Map and sync files (NO changelist creation here)
        if process_beni and process_flumen:
            map_two_depots_silent(beni_depot_path, flumen_depot_path)
            sync_file_silent(beni_depot_path)
            sync_file_silent(flumen_depot_path)
        elif process_beni:
            map_single_depot(beni_depot_path)
            sync_file_silent(beni_depot_path)
        elif process_flumen:
            map_single_depot(flumen_depot_path)
            sync_file_silent(flumen_depot_path)
        
        if progress_callback:
            progress_callback(60)
        
        # Get local paths and extract properties
        properties_data = {}
        
        if process_beni:
            beni_local = depot_to_local_path(beni_depot_path)
            beni_properties = extract_properties_from_file(beni_local)
            if not beni_properties:
                if error_callback:
                    error_callback("Properties Not Found", "BENI file does not contain LMKD or Chimera properties")
                return None
            properties_data["BENI"] = beni_properties
        
        if process_flumen:
            flumen_local = depot_to_local_path(flumen_depot_path)
            flumen_properties = extract_properties_from_file(flumen_local)
            if not flumen_properties:
                if error_callback:
                    error_callback("Properties Not Found", "FLUMEN file does not contain LMKD or Chimera properties")
                return None
            properties_data["FLUMEN"] = flumen_properties
        
        if progress_callback:
            progress_callback(80)
        
        # Compare properties if both files exist
        if process_beni and process_flumen:
            differences = compare_properties(properties_data["BENI"], properties_data["FLUMEN"])
            if differences:
                diff_message = "Properties differ between BENI and FLUMEN:\n\n" + "\n".join(differences)
                if info_callback:
                    info_callback("Properties Comparison", diff_message)
        
        # Return the properties from the first available file for editing
        result_properties = properties_data.get("BENI", properties_data.get("FLUMEN", {}))
        
        if progress_callback:
            progress_callback(100)
        
        return result_properties
        
    except Exception as e:
        if error_callback:
            error_callback("Load Properties Error", str(e))
        return None

def extract_properties_from_file(file_path):
    """Extract LMKD and Chimera properties from file"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        properties = {"LMKD": {}, "Chimera": {}}
        
        # Extract LMKD properties
        lmkd_block = extract_block(lines, "# LMKD property", ["# Chimera property", "# DHA property"])
        if not lmkd_block:
            lmkd_block = extract_block(lines, "# DHA property", ["# Chimera property"])
        
        if lmkd_block:
            lmkd_props = parse_properties_block(lmkd_block)
            properties["LMKD"] = lmkd_props
        
        # Extract Chimera properties
        chimera_block = extract_block(lines, "# Chimera property", ["# Nandswap", "#", ""])
        if chimera_block:
            chimera_props = parse_properties_block(chimera_block)
            properties["Chimera"] = chimera_props
        
        # Return None if no properties found
        if not properties["LMKD"] and not properties["Chimera"]:
            return None
        
        return properties
        
    except Exception:
        return None

def extract_block(lines, start_header, next_header_list):
    """Extract block of lines between headers"""
    start = end = None
    for idx, line in enumerate(lines):
        if line.strip() == start_header:
            start = idx
            break
    if start is None:
        return []

    for idx in range(start + 1, len(lines)):
        if lines[idx].strip() in next_header_list:
            end = idx
            break
    if end is None:
        end = len(lines)
    return lines[start:end]

def parse_properties_block(block_lines):
    """Parse property block and extract key-value pairs"""
    properties = {}
    
    for line in block_lines:
        line = line.strip()
        # Skip comments and empty lines  
        if not line or line.startswith("#"):
            continue
        
        # Look for property=value pattern
        if "=" in line:
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            
            # Remove any trailing comments
            if "#" in value:
                value = value.split("#")[0].strip()
            
            properties[key] = value
    
    return properties

def compare_properties(beni_props, flumen_props):
    """Compare properties between BENI and FLUMEN files"""
    differences = []
    
    # Compare LMKD properties
    beni_lmkd = beni_props.get("LMKD", {})
    flumen_lmkd = flumen_props.get("LMKD", {})
    
    lmkd_diffs = compare_property_dict(beni_lmkd, flumen_lmkd, "LMKD")
    differences.extend(lmkd_diffs)
    
    # Compare Chimera properties
    beni_chimera = beni_props.get("Chimera", {})
    flumen_chimera = flumen_props.get("Chimera", {})
    
    chimera_diffs = compare_property_dict(beni_chimera, flumen_chimera, "Chimera")
    differences.extend(chimera_diffs)
    
    return differences

def compare_property_dict(dict1, dict2, category):
    """Compare two property dictionaries"""
    differences = []
    
    all_keys = set(dict1.keys()) | set(dict2.keys())
    
    for key in all_keys:
        val1 = dict1.get(key, "<missing>")
        val2 = dict2.get(key, "<missing>")
        
        if val1 != val2:
            differences.append(f"{category}.{key}: BENI='{val1}' vs FLUMEN='{val2}'")
    
    return differences

def run_tuning_process(beni_depot_path, vince_depot_path, flumen_depot_path, properties,
                      progress_callback=None, error_callback=None, info_callback=None):
    """Execute the tuning process to apply property changes"""
    try:
        # Determine which files to process
        process_beni = beni_depot_path and beni_depot_path.startswith("//")
        process_flumen = flumen_depot_path and flumen_depot_path.startswith("//")
        
        if not process_beni and not process_flumen:
            if error_callback:
                error_callback("No Valid Paths", "At least one valid depot path is required.")
            return
        
        if progress_callback:
            progress_callback(10)
        
        # Create changelist for editing files (MOVED HERE - only when applying changes)
        changelist_id = create_changelist_for_tuning()
        
        if progress_callback:
            progress_callback(30)
        
        # Checkout files for editing
        if process_beni:
            checkout_file_silent(beni_depot_path, changelist_id)
        if process_flumen:
            checkout_file_silent(flumen_depot_path, changelist_id)
        
        if progress_callback:
            progress_callback(50)
        
        # Apply changes to local files
        files_updated = []
        
        if process_beni:
            beni_local = depot_to_local_path(beni_depot_path)
            if apply_properties_to_file(beni_local, properties):
                files_updated.append("BENI")
        
        if process_flumen:
            flumen_local = depot_to_local_path(flumen_depot_path)
            if apply_properties_to_file(flumen_local, properties):
                files_updated.append("FLUMEN")
        
        if progress_callback:
            progress_callback(80)
        
        if files_updated:
            success_message = f"Properties successfully updated in: {', '.join(files_updated)}\n\nChangelist {changelist_id} is ready for submission."
            if info_callback:
                info_callback("Tuning Complete", success_message)
        else:
            if error_callback:
                error_callback("Update Failed", "No files were updated.")
        
        if progress_callback:
            progress_callback(100)
        
    except Exception as e:
        if error_callback:
            error_callback("Tuning Process Error", str(e))
        if progress_callback:
            progress_callback(0)

def create_changelist_for_tuning():
    """Create changelist for applying tuning changes"""
    return create_changelist_silent("Apply tuning changes to LMKD/Chimera properties")

def apply_properties_to_file(file_path, properties):
    """Apply property changes to a file while preserving format"""
    try:
        # Create backup
        backup_path = create_backup(file_path)
        
        # Read file
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        # Update LMKD properties while preserving format
        if "LMKD" in properties and properties["LMKD"]:
            lines = update_properties_block_preserve_format(lines, properties["LMKD"], "# LMKD property", 
                                          ["# Chimera property", "# DHA property"])
            if not any("# LMKD property" in line for line in lines):
                # Try DHA property if LMKD not found
                lines = update_properties_block_preserve_format(lines, properties["LMKD"], "# DHA property", 
                                              ["# Chimera property"])
        
        # Update Chimera properties while preserving format
        if "Chimera" in properties and properties["Chimera"]:
            lines = update_properties_block_preserve_format(lines, properties["Chimera"], "# Chimera property", 
                                          ["# Nandswap", "#", ""])
        
        # Write updated file
        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(lines)
        
        return True
        
    except Exception:
        return False

def update_properties_block_preserve_format(lines, new_properties, start_header, next_header_list):
    """Update properties block while preserving original format and comments - FIXED VERSION"""
    # Find block boundaries
    start = end = None
    for idx, line in enumerate(lines):
        if line.strip() == start_header:
            start = idx
            break
    
    if start is None:
        return lines  # Block not found
    
    for idx in range(start + 1, len(lines)):
        if lines[idx].strip() in next_header_list:
            end = idx
            break
    if end is None:
        end = len(lines)
    
    # Extract original block to preserve formatting
    original_lines = lines[start:end]
    new_block = [lines[start]]  # Keep header line
    
    # Create a copy of new_properties to track what we've processed
    remaining_properties = new_properties.copy()
    
    # Find PRODUCT_PROPERTY_OVERRIDES block
    override_start = None
    override_properties = {}
    non_override_properties = {}
    
    # First pass: identify structure and extract all properties
    for line_idx in range(1, len(original_lines)):
        line = original_lines[line_idx]
        stripped_line = line.strip()
        
        # Skip comments and empty lines
        if not stripped_line or stripped_line.startswith("#"):
            continue
            
        # Find PRODUCT_PROPERTY_OVERRIDES line
        if "PRODUCT_PROPERTY_OVERRIDES" in stripped_line and "+=" in stripped_line:
            override_start = line_idx
            continue
            
        # Extract properties
        if "=" in stripped_line and not "PRODUCT_PROPERTY_OVERRIDES" in stripped_line:
            # Clean the line - remove backslash and whitespace
            prop_content = stripped_line.rstrip(" \\").strip()
            if "=" in prop_content:
                key, value = prop_content.split("=", 1)
                key = key.strip()
                value = value.strip()
                
                if override_start is not None:
                    # This is inside PRODUCT_PROPERTY_OVERRIDES block
                    override_properties[key] = value
                else:
                    # This is a regular property
                    non_override_properties[key] = value
    
    # Update properties with new values - ONLY keep properties that exist in new_properties
    # This ensures deletion works correctly
    updated_override_properties = {}
    updated_non_override_properties = {}
    
    # Process properties that should be kept/updated
    for key, value in new_properties.items():
        if key in override_properties:
            # This property belongs to override block
            updated_override_properties[key] = value
        elif key in non_override_properties:
            # This property belongs to non-override section
            updated_non_override_properties[key] = value
        else:
            # New property - add to override block by default
            updated_override_properties[key] = value
    
    override_properties = updated_override_properties
    non_override_properties = updated_non_override_properties
    remaining_properties = {}  # All properties are now processed
    
    # Second pass: rebuild the block
    processed_override = False
    
    for line_idx in range(1, len(original_lines)):
        line = original_lines[line_idx]
        stripped_line = line.strip()
        
        # Keep comments and empty lines as-is
        if not stripped_line or stripped_line.startswith("#"):
            new_block.append(line)
            continue
        
        # Handle PRODUCT_PROPERTY_OVERRIDES line
        if "PRODUCT_PROPERTY_OVERRIDES" in stripped_line and "+=" in stripped_line and not processed_override:
            # Add the PRODUCT_PROPERTY_OVERRIDES line
            new_block.append(line)
            
            # Add all properties in override block with proper formatting
            if override_properties:
                # Get indentation from original properties
                default_indent = "    "  # Default 4 spaces
                for check_idx in range(line_idx + 1, len(original_lines)):
                    check_line = original_lines[check_idx]
                    if "=" in check_line.strip() and not check_line.strip().startswith("#"):
                        default_indent = check_line[:len(check_line) - len(check_line.lstrip())]
                        break
                
                # Build list of properties maintaining some original order if possible
                prop_items = []
                
                # Add properties in a logical order: existing first, then new ones
                original_keys = []
                for check_idx in range(line_idx + 1, len(original_lines)):
                    check_line = original_lines[check_idx]
                    check_stripped = check_line.strip()
                    if "=" in check_stripped and not check_stripped.startswith("#") and not "PRODUCT_PROPERTY_OVERRIDES" in check_stripped:
                        prop_content = check_stripped.rstrip(" \\").strip()
                        if "=" in prop_content:
                            key = prop_content.split("=", 1)[0].strip()
                            if key in override_properties:
                                original_keys.append(key)
                
                # Add properties in specific order for better formatting
                # First, add original properties in their original order
                for key in original_keys:
                    if key in override_properties and key != "test":  # Skip test for now
                        prop_items.append((key, override_properties[key]))
                        del override_properties[key]
                
                # Add new non-test properties 
                new_props = []
                test_props = []
                for key, value in override_properties.items():
                    if key == "test":
                        test_props.append((key, value))
                    else:
                        new_props.append((key, value))
                
                # Add new non-test properties first
                prop_items.extend(new_props)
                
                # Add test properties near the end (before the last property if possible)
                if test_props and prop_items:
                    # Insert test properties before the last property
                    last_prop = prop_items.pop() if prop_items else None
                    prop_items.extend(test_props)
                    if last_prop:
                        prop_items.append(last_prop)
                elif test_props:
                    # If no other properties, just add test properties
                    prop_items.extend(test_props)
                
                # Write properties with proper backslash formatting
                for idx, (key, value) in enumerate(prop_items):
                    if idx == len(prop_items) - 1:  # Last property - no backslash
                        new_block.append(f"{default_indent}{key}={value}\n")
                    else:  # Not last property - add backslash
                        new_block.append(f"{default_indent}{key}={value} \\\n")
            
            processed_override = True
            continue
        
        # Skip original property lines inside PRODUCT_PROPERTY_OVERRIDES (we already processed them)
        if override_start is not None and line_idx > override_start and ("=" in stripped_line and not "PRODUCT_PROPERTY_OVERRIDES" in stripped_line):
            continue
        
        # Handle regular property lines (not in PRODUCT_PROPERTY_OVERRIDES)
        if "=" in stripped_line and not "PRODUCT_PROPERTY_OVERRIDES" in stripped_line and override_start is None:
            prop_content = stripped_line.rstrip(" \\").strip()
            if "=" in prop_content:
                key = prop_content.split("=", 1)[0].strip()
                
                if key in non_override_properties:
                    # Preserve original indentation
                    indent = len(line) - len(line.lstrip())
                    indent_str = line[:indent]
                    
                    # Get trailing comment if exists
                    trailing_comment = ""
                    if "#" in line:
                        line_parts = line.split("#", 1)
                        if len(line_parts) > 1:
                            trailing_comment = " #" + line_parts[1].rstrip()
                    
                    new_value = non_override_properties[key]
                    new_line = f"{indent_str}{key}={new_value}{trailing_comment}\n"
                    new_block.append(new_line)
                    continue
        
        # Keep other lines unchanged
        new_block.append(line)
    
    # Replace the block
    return lines[:start] + new_block + lines[end:]