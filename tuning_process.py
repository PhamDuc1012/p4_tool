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
    
    # Track PRODUCT_PROPERTY_OVERRIDES blocks and their properties
    current_override_start = None
    current_override_properties = []
    last_property_line_idx = 1  # Start after header
    
    # First pass: identify all PRODUCT_PROPERTY_OVERRIDES blocks and their properties
    override_blocks = []
    i = 1
    while i < len(original_lines):
        line = original_lines[i]
        stripped_line = line.strip()
        
        if "PRODUCT_PROPERTY_OVERRIDES" in stripped_line and "+=" in stripped_line:
            # Start of new override block
            block_start = i
            block_properties = []
            block_lines = [i]  # Store line indices
            i += 1
            
            # Collect all properties in this block
            while i < len(original_lines):
                prop_line = original_lines[i]
                prop_stripped = prop_line.strip()
                
                if not prop_stripped or prop_stripped.startswith("#"):
                    block_lines.append(i)
                    i += 1
                    continue
                
                if "=" in prop_stripped:
                    # Extract property name
                    if prop_stripped.endswith("\\"):
                        prop_content = prop_stripped[:-1].strip()
                    else:
                        prop_content = prop_stripped
                    
                    if "=" in prop_content:
                        key = prop_content.split("=", 1)[0].strip()
                        block_properties.append(key)
                    
                    block_lines.append(i)
                    
                    # If line doesn't end with backslash, this is end of block
                    if not prop_stripped.endswith("\\"):
                        i += 1
                        break
                    i += 1
                else:
                    # Non-property line, end of block
                    break
            
            override_blocks.append({
                'start': block_start,
                'properties': block_properties,
                'lines': block_lines
            })
        else:
            i += 1
    
    # Second pass: rebuild the block with updates
    processed_lines = set()
    
    for line_idx in range(1, len(original_lines)):  # Skip header
        if line_idx in processed_lines:
            continue
            
        line = original_lines[line_idx]
        stripped_line = line.strip()
        
        # Keep comments and empty lines as-is
        if not stripped_line or stripped_line.startswith("#"):
            new_block.append(line)
            continue
        
        # Handle PRODUCT_PROPERTY_OVERRIDES blocks
        current_block = None
        for block in override_blocks:
            if line_idx == block['start']:
                current_block = block
                break
        
        if current_block:
            # Process entire PRODUCT_PROPERTY_OVERRIDES block
            new_block.append(original_lines[current_block['start']])  # Add PRODUCT_PROPERTY_OVERRIDES line
            processed_lines.add(current_block['start'])
            
            # Get indentation from existing properties
            default_indent = "    "
            for idx in current_block['lines'][1:]:  # Skip PRODUCT_PROPERTY_OVERRIDES line
                if idx < len(original_lines):
                    prop_line = original_lines[idx]
                    if "=" in prop_line.strip() and not prop_line.strip().startswith("#"):
                        default_indent = prop_line[:len(prop_line) - len(prop_line.lstrip())]
                        break
            
            # Collect all properties for this block (existing + new)
            block_props = {}
            
            # Add existing properties
            for idx in current_block['lines'][1:]:  # Skip PRODUCT_PROPERTY_OVERRIDES line
                if idx < len(original_lines):
                    prop_line = original_lines[idx]
                    prop_stripped = prop_line.strip()
                    
                    if not prop_stripped or prop_stripped.startswith("#"):
                        continue
                        
                    if "=" in prop_stripped:
                        prop_content = prop_stripped[:-1].strip() if prop_stripped.endswith("\\") else prop_stripped
                        if "=" in prop_content:
                            key, value = prop_content.split("=", 1)
                            key = key.strip()
                            
                            # Use new value if exists, otherwise keep original
                            if key in remaining_properties:
                                block_props[key] = remaining_properties[key]
                                del remaining_properties[key]
                            else:
                                block_props[key] = value.strip()
            
            # Add any remaining new properties to this block
            for key, value in list(remaining_properties.items()):
                block_props[key] = value
                del remaining_properties[key]
            
            # Write all properties in this block
            prop_items = list(block_props.items())
            for idx, (key, value) in enumerate(prop_items):
                if idx == len(prop_items) - 1:  # Last property - no backslash
                    new_block.append(f"{default_indent}{key}={value}\n")
                else:  # Not last property - add backslash
                    new_block.append(f"{default_indent}{key}={value} \\\n")
            
            # Mark all lines in this block as processed
            for idx in current_block['lines']:
                processed_lines.add(idx)
            
            last_property_line_idx = len(new_block)
            
        # Handle regular property lines (not in PRODUCT_PROPERTY_OVERRIDES block)
        elif "=" in stripped_line and not "PRODUCT_PROPERTY_OVERRIDES" in stripped_line:
            key, old_value = stripped_line.split("=", 1)
            key = key.strip()
            
            # Preserve original indentation
            indent = len(line) - len(line.lstrip())
            indent_str = line[:indent]
            
            # Get trailing comment if exists
            trailing_comment = ""
            if "#" in old_value:
                value_part, comment_part = old_value.split("#", 1)
                trailing_comment = " #" + comment_part.rstrip()
            
            # Update with new value if exists, otherwise keep original
            if key in remaining_properties:
                new_value = remaining_properties[key]
                new_line = f"{indent_str}{key}={new_value}{trailing_comment}\n"
                new_block.append(new_line)
                # Remove this key so we don't add it again
                del remaining_properties[key]
            else:
                # Keep original line unchanged
                new_block.append(line)
            
            last_property_line_idx = len(new_block)
            
        else:
            # Keep other lines unchanged
            new_block.append(line)
    
    # Add any remaining new properties as regular properties (if no PRODUCT_PROPERTY_OVERRIDES blocks)
    if remaining_properties:
        # Find appropriate indentation from existing properties
        default_indent = "    "  # Default 4 spaces for properties
        for line in original_lines:
            if "=" in line and not line.strip().startswith("#") and not "PRODUCT_PROPERTY_OVERRIDES" in line:
                default_indent = line[:len(line) - len(line.lstrip())]
                break
        
        # Insert new properties at the correct position (after last property)
        new_props_lines = []
        for key, value in remaining_properties.items():
            new_props_lines.append(f"{default_indent}{key}={value}\n")
        
        # Insert new properties after the last property line
        new_block = new_block[:last_property_line_idx] + new_props_lines + new_block[last_property_line_idx:]
    
    # Replace the block
    return lines[:start] + new_block + lines[end:]