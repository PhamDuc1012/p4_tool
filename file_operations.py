"""
File operations for LMKD and Chimera properties
Handles file reading, writing, and property extraction
"""
import os
import shutil
from datetime import datetime

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

def validate_properties_exist(file_path):
    """Check if LMKD and Chimera properties exist in file"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        has_lmkd = "# LMKD property" in content or "# DHA property" in content
        has_chimera = "# Chimera property" in content
        
        return has_lmkd, has_chimera
    except:
        return False, False

def replace_block(target_lines, block_lines, start_header, next_header_list):
    """Replace block in target lines with new block"""
    start = end = None
    for idx, line in enumerate(target_lines):
        if line.strip() == start_header:
            start = idx
            break
    if start is None:
        return target_lines

    for idx in range(start + 1, len(target_lines)):
        if target_lines[idx].strip() in next_header_list:
            end = idx
            break
    if end is None:
        end = len(target_lines)

    return target_lines[:start] + block_lines + target_lines[end:]

def update_lmkd_chimera(vince_path, target_path, log_callback):
    """Update LMKD and Chimera properties in target file"""
    target_name = "BENI" if "beni" in target_path.lower() else "FLUMEN" if "flumen" in target_path.lower() else "TARGET"
    log_callback(f"[STEP 3] Updating LMKD and Chimera properties in {target_name}...")
    
    with open(vince_path, "r", encoding="utf-8") as f:
        vince_lines = f.readlines()
    with open(target_path, "r", encoding="utf-8") as f:
        target_lines = f.readlines()

    lmkd_block = extract_block(vince_lines, "# LMKD property", ["# Chimera property", "# DHA property"])
    if not lmkd_block:
        lmkd_block = extract_block(vince_lines, "# DHA property", ["# Chimera property"])
    chimera_block = extract_block(vince_lines, "# Chimera property", ["# Nandswap", "#", ""])

    updated_target = replace_block(target_lines, lmkd_block, "# LMKD property", ["# Chimera property", "# DHA property"])
    updated_target = replace_block(updated_target, chimera_block, "# Chimera property", ["# Nandswap", "#", ""])

    backup_path = target_path + ".bak_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copyfile(target_path, backup_path)
    with open(target_path, "w", encoding="utf-8") as f:
        f.writelines(updated_target)
    log_callback(f"[OK] Updated {target_name} file. Backup saved at: {backup_path}")

def create_backup(file_path):
    """Create backup of file with timestamp"""
    backup_path = file_path + ".bak_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copyfile(file_path, backup_path)
    return backup_path

def extract_properties_from_file(file_path):
    """Extract LMKD and Chimera properties from file and return as dictionary"""
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

def update_properties_in_file(file_path, properties_dict):
    """Update properties in file with new values while preserving format"""
    try:
        # Create backup first
        backup_path = create_backup(file_path)
        
        # Read current file
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        # Update LMKD properties
        if "LMKD" in properties_dict and properties_dict["LMKD"]:
            lines = update_properties_block_preserve_format(lines, properties_dict["LMKD"], 
                                          "# LMKD property", ["# Chimera property", "# DHA property"])
            if not any("# LMKD property" in line for line in lines):
                # Try with DHA property if LMKD not found
                lines = update_properties_block_preserve_format(lines, properties_dict["LMKD"], 
                                              "# DHA property", ["# Chimera property"])
        
        # Update Chimera properties
        if "Chimera" in properties_dict and properties_dict["Chimera"]:
            lines = update_properties_block_preserve_format(lines, properties_dict["Chimera"], 
                                          "# Chimera property", ["# Nandswap", "#", ""])
        
        # Write updated file
        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(lines)
        
        return True, backup_path
        
    except Exception as e:
        return False, str(e)

import re

# def update_properties_block_preserve_format(lines, new_properties, start_header, next_header_list):
#     """Update properties block while preserving original format and comments - FIXED VERSION"""
#     # Find block boundaries
#     start = end = None
#     for idx, line in enumerate(lines):
#         if line.strip() == start_header:
#             start = idx
#             break
#     if start is None:
#         return lines  # Block not found

#     for idx in range(start + 1, len(lines)):
#         if lines[idx].strip() in next_header_list:
#             end = idx
#             break
#     if end is None:
#         end = len(lines)

#     # Extract original block
#     original_lines = lines[start:end]
#     new_block = [lines[start]]  # Keep header

#     remaining_properties = new_properties.copy()
#     last_property_line_idx = 1  # Position after header for inserting new properties

#     # Process each line in original block
#     for idx, line in enumerate(original_lines[1:], start=start + 1):
#         stripped_line = line.strip()

#         # Keep comments and empty lines as-is
#         if not stripped_line or stripped_line.startswith("#"):
#             new_block.append(line)
#             continue

#         # Handle PRODUCT_PROPERTY_OVERRIDES line - PRESERVE EXACT FORMAT INCLUDING SPACES
#         if "PRODUCT_PROPERTY_OVERRIDES" in stripped_line and "+=" in stripped_line:
#             new_block.append(line)  # Keep original formatting exactly (with spaces)
#             continue

#         # Handle property lines (not PRODUCT_PROPERTY_OVERRIDES)
#         if "=" in stripped_line and "PRODUCT_PROPERTY_OVERRIDES" not in stripped_line:
#             key, old_value = stripped_line.split("=", 1)
#             key = key.strip()

#             # Preserve original indentation
#             indent = len(line) - len(line.lstrip())
#             indent_str = line[:indent]

#             trailing_comment = ""
#             if "#" in old_value:
#                 value_part, comment_part = old_value.split("#", 1)
#                 trailing_comment = " #" + comment_part.rstrip()

#             # Update with new value if exists
#             if key in remaining_properties:
#                 new_value = remaining_properties[key]
#                 new_line = f"{indent_str}{key}={new_value}{trailing_comment}\n"
#                 new_block.append(new_line)
#                 del remaining_properties[key]
#             else:
#                 new_block.append(line)

#             # Track position for inserting new properties
#             last_property_line_idx = len(new_block)
#         else:
#             # Keep other lines unchanged
#             new_block.append(line)

#     # Add remaining new properties with proper format
#     if remaining_properties:
#         # Find correct indentation (4 spaces for properties)
#         default_indent = "    "  # Default 4 spaces
#         for line in original_lines:
#             if "=" in line and not line.strip().startswith("#") and "PRODUCT_PROPERTY_OVERRIDES" not in line:
#                 default_indent = line[:len(line) - len(line.lstrip())]
#                 break

#         # Create new property lines
#         new_props_lines = []
#         for key, value in remaining_properties.items():
#             new_props_lines.append(f"{default_indent}{key}={value}\n")

#         # Insert at correct position (after last property)
#         new_block = new_block[:last_property_line_idx] + new_props_lines + new_block[last_property_line_idx:]

#     return lines[:start] + new_block + lines[end:]

def update_properties_block_preserve_format(lines, new_properties, start_header, next_header_list):
    """Update properties block while preserving original format and comments"""
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
    
    # Track state for PRODUCT_PROPERTY_OVERRIDES blocks
    in_product_override_block = False
    current_override_properties = []  # Track properties in current override block
    last_regular_property_line_idx = 1  # Start after header
    
    # Process each line in original block
    line_idx = 1  # Start after header
    while line_idx < len(original_lines):
        line = original_lines[line_idx]
        stripped_line = line.strip()
        
        # Keep comments and empty lines as-is
        if not stripped_line or stripped_line.startswith("#"):
            new_block.append(line)
            line_idx += 1
            continue
        
        # Handle PRODUCT_PROPERTY_OVERRIDES line - start of a new override block
        if "PRODUCT_PROPERTY_OVERRIDES" in stripped_line and "+=" in stripped_line:
            new_block.append(line)  # Keep original formatting exactly
            in_product_override_block = True
            current_override_properties = []
            line_idx += 1
            
            # Process all properties in this override block
            while line_idx < len(original_lines):
                prop_line = original_lines[line_idx]
                prop_stripped = prop_line.strip()
                
                # If empty line or comment, keep as-is
                if not prop_stripped or prop_stripped.startswith("#"):
                    new_block.append(prop_line)
                    line_idx += 1
                    continue
                
                # If this line contains a property and ends with backslash
                if "=" in prop_stripped and prop_stripped.endswith("\\"):
                    # Extract property name and value
                    prop_content = prop_stripped[:-1].strip()  # Remove backslash
                    if "=" in prop_content:
                        key, old_value = prop_content.split("=", 1)
                        key = key.strip()
                        
                        # Preserve original indentation
                        indent = len(prop_line) - len(prop_line.lstrip())
                        indent_str = prop_line[:indent]
                        
                        # Update with new value if exists, otherwise keep original
                        if key in remaining_properties:
                            new_value = remaining_properties[key]
                            new_line = f"{indent_str}{key}={new_value} \\\n"
                            new_block.append(new_line)
                            current_override_properties.append(key)
                            # Remove this key so we don't add it again
                            del remaining_properties[key]
                        else:
                            # Keep original line unchanged
                            new_block.append(prop_line)
                            current_override_properties.append(key)
                    else:
                        new_block.append(prop_line)
                    
                    line_idx += 1
                    
                # If this line contains a property but doesn't end with backslash (last property in block)
                elif "=" in prop_stripped and not prop_stripped.endswith("\\"):
                    # Extract property name and value
                    if "=" in prop_stripped:
                        key, old_value = prop_stripped.split("=", 1)
                        key = key.strip()
                        
                        # Preserve original indentation
                        indent = len(prop_line) - len(prop_line.lstrip())
                        indent_str = prop_line[:indent]
                        
                        # Update with new value if exists, otherwise keep original
                        if key in remaining_properties:
                            new_value = remaining_properties[key]
                            # Check if there are more properties to add
                            if any(prop_key not in current_override_properties for prop_key in remaining_properties.keys()):
                                new_line = f"{indent_str}{key}={new_value} \\\n"
                            else:
                                new_line = f"{indent_str}{key}={new_value}\n"
                            new_block.append(new_line)
                            current_override_properties.append(key)
                            del remaining_properties[key]
                        else:
                            # Check if we need to add new properties
                            remaining_for_this_block = {k: v for k, v in remaining_properties.items() 
                                                      if k not in current_override_properties}
                            if remaining_for_this_block:
                                # Change last property to have backslash
                                new_line = f"{indent_str}{key}={old_value.strip()} \\\n"
                                new_block.append(new_line)
                            else:
                                # Keep original line unchanged
                                new_block.append(prop_line)
                            current_override_properties.append(key)
                    else:
                        new_block.append(prop_line)
                    
                    # Add any remaining properties for this block
                    remaining_for_this_block = {k: v for k, v in remaining_properties.items() 
                                              if k not in current_override_properties}
                    if remaining_for_this_block:
                        # Find appropriate indentation
                        default_indent = indent_str if 'indent_str' in locals() else "    "
                        
                        prop_items = list(remaining_for_this_block.items())
                        for idx, (key, value) in enumerate(prop_items):
                            if idx == len(prop_items) - 1:  # Last property
                                new_block.append(f"{default_indent}{key}={value}\n")
                            else:
                                new_block.append(f"{default_indent}{key}={value} \\\n")
                            del remaining_properties[key]
                    
                    in_product_override_block = False
                    line_idx += 1
                    break
                    
                else:
                    # Not a property line, end of override block
                    new_block.append(prop_line)
                    in_product_override_block = False
                    line_idx += 1
                    break
            continue
            
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
            
            last_regular_property_line_idx = len(new_block)
            line_idx += 1
            
        else:
            # Keep other lines unchanged
            new_block.append(line)
            line_idx += 1
    
    # Add any remaining new properties as regular properties (shouldn't happen if logic is correct)
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
        new_block = new_block[:last_regular_property_line_idx] + new_props_lines + new_block[last_regular_property_line_idx:]
    
    # Replace the block
    return lines[:start] + new_block + lines[end:]

def update_properties_block(lines, new_properties, start_header, next_header_list):
    """Update properties block in file lines"""
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
    
    # Build new block
    new_block = [lines[start]]  # Keep header line
    
    # Add properties
    for key, value in new_properties.items():
        new_block.append(f"{key}={value}\n")
    
    # Add empty line before next section if needed
    if end < len(lines) and lines[end].strip():
        new_block.append("\n")
    
    # Replace the block
    return lines[:start] + new_block + lines[end:]

def compare_properties_between_files(file1_path, file2_path):
    """Compare properties between two files and return differences"""
    try:
        props1 = extract_properties_from_file(file1_path)
        props2 = extract_properties_from_file(file2_path)
        
        if not props1 or not props2:
            return None
        
        differences = []
        
        # Compare LMKD properties
        lmkd1 = props1.get("LMKD", {})
        lmkd2 = props2.get("LMKD", {})
        lmkd_diffs = compare_property_dict(lmkd1, lmkd2, "LMKD")
        differences.extend(lmkd_diffs)
        
        # Compare Chimera properties
        chimera1 = props1.get("Chimera", {})
        chimera2 = props2.get("Chimera", {})
        chimera_diffs = compare_property_dict(chimera1, chimera2, "Chimera")
        differences.extend(chimera_diffs)
        
        return differences
        
    except Exception:
        return None

def compare_property_dict(dict1, dict2, category):
    """Compare two property dictionaries"""
    differences = []
    
    all_keys = set(dict1.keys()) | set(dict2.keys())
    
    for key in all_keys:
        val1 = dict1.get(key, "<missing>")
        val2 = dict2.get(key, "<missing>")
        
        if val1 != val2:
            differences.append(f"{category}.{key}: File1='{val1}' vs File2='{val2}'")
    
    return differences