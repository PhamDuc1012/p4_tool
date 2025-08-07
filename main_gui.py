"""
Main GUI implementation
Handles all user interface components and interactions
"""
import tkinter as tk
from tkinter import ttk, messagebox
import threading
from config.p4_config import initialize_p4_config, get_client_name, get_workspace_root
from processes.bringup_process import run_bringup_process
from processes.tuning_process import run_tuning_process

class BringupToolGUI:
    """Main GUI class for the Tuning Tool"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Bringup Tool - LMKD & Chimera Sync")
        self.root.geometry("1000x700")
        self.root.minsize(900, 600)
        
        # Current mode
        self.current_mode = tk.StringVar(value="bringup")
        
        # Initialize P4 configuration silently
        initialize_p4_config()
        
        # Create GUI components
        self.create_navbar()
        self.create_main_content()
        
        # Set default mode
        self.switch_mode("bringup")
    
    def create_navbar(self):
        """Create navigation tabs"""
        # Create navbar frame
        navbar_frame = ttk.Frame(self.root)
        navbar_frame.pack(fill="x", padx=10, pady=(10, 0))
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(navbar_frame)
        self.notebook.pack(fill="x")
        
        # Create frames for each tab
        self.bringup_tab = ttk.Frame(self.notebook)
        self.tuning_tab = ttk.Frame(self.notebook)
        
        # Add tabs to notebook
        self.notebook.add(self.bringup_tab, text="Bring up")
        self.notebook.add(self.tuning_tab, text="Tuning value")
        
        # Bind tab change event
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
    
    def create_main_content(self):
        """Create main content area"""
        # Main content frame
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create content for both modes
        self.create_bringup_content()
        self.create_tuning_content()
        
        # Status bar
        self.create_status_bar()
    
    def create_bringup_content(self):
        """Create content for bringup mode"""
        self.bringup_frame = ttk.Frame(self.main_frame)
        
        # Input fields frame
        input_frame = ttk.LabelFrame(self.bringup_frame, text="Configuration", padding=10)
        input_frame.pack(fill="x", pady=(0, 10))
        
        # BENI Path
        ttk.Label(input_frame, text="BENI Depot Path:").grid(column=0, row=0, sticky="w", pady=2)
        self.bringup_beni_entry = ttk.Entry(input_frame, width=70)
        self.bringup_beni_entry.grid(column=1, row=0, padx=5, pady=2, sticky="ew")
        
        # VINCE Path
        ttk.Label(input_frame, text="VINCE Depot Path:").grid(column=0, row=1, sticky="w", pady=2)
        self.bringup_vince_entry = ttk.Entry(input_frame, width=70)
        self.bringup_vince_entry.grid(column=1, row=1, padx=5, pady=2, sticky="ew")
        
        # FLUMEN Path
        ttk.Label(input_frame, text="FLUMEN Depot Path:").grid(column=0, row=2, sticky="w", pady=2)
        self.bringup_flumen_entry = ttk.Entry(input_frame, width=70)
        self.bringup_flumen_entry.grid(column=1, row=2, padx=5, pady=2, sticky="ew")
        
        # Configure grid weights
        input_frame.columnconfigure(1, weight=1)
        
        # Control frame
        control_frame = ttk.Frame(input_frame)
        control_frame.grid(column=1, row=3, pady=10, sticky="e")
        
        # Progress bar
        self.bringup_progress = ttk.Progressbar(control_frame, length=200, mode='determinate')
        self.bringup_progress.pack(side="left", padx=(0, 10))
        
        # Start button
        self.bringup_start_btn = ttk.Button(control_frame, text="Start Bring up", command=self.on_bringup_start)
        self.bringup_start_btn.pack(side="right")
        
        # Log output frame
        log_frame = ttk.LabelFrame(self.bringup_frame, text="Process Log", padding=5)
        log_frame.pack(fill="both", expand=True)
        
        # Create text widget with scrollbar
        text_frame = ttk.Frame(log_frame)
        text_frame.pack(fill="both", expand=True)
        
        self.bringup_log_text = tk.Text(text_frame, height=20, wrap="word", 
                               bg="#1e1e1e", fg="#00ff88", font=("Consolas", 9))
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=self.bringup_log_text.yview)
        self.bringup_log_text.configure(yscrollcommand=scrollbar.set)
        
        self.bringup_log_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def create_tuning_content(self):
        """Create content for tuning mode"""
        self.tuning_frame = ttk.Frame(self.main_frame)
        
        # Input fields frame
        input_frame = ttk.LabelFrame(self.tuning_frame, text="Configuration", padding=10)
        input_frame.pack(fill="x", pady=(0, 10))
        
        # BENI Path
        ttk.Label(input_frame, text="BENI Depot Path:").grid(column=0, row=0, sticky="w", pady=2)
        self.tuning_beni_entry = ttk.Entry(input_frame, width=70)
        self.tuning_beni_entry.grid(column=1, row=0, padx=5, pady=2, sticky="ew")
        
        # FLUMEN Path
        ttk.Label(input_frame, text="FLUMEN Depot Path:").grid(column=0, row=1, sticky="w", pady=2)
        self.tuning_flumen_entry = ttk.Entry(input_frame, width=70)
        self.tuning_flumen_entry.grid(column=1, row=1, padx=5, pady=2, sticky="ew")
        
        # Configure grid weights
        input_frame.columnconfigure(1, weight=1)
        
        # Control frame
        control_frame = ttk.Frame(input_frame)
        control_frame.grid(column=1, row=2, pady=10, sticky="e")
        
        # Load Properties button
        self.load_properties_btn = ttk.Button(control_frame, text="Load Properties", command=self.on_load_properties)
        self.load_properties_btn.pack(side="left", padx=(0, 10))
        
        # Progress bar
        self.tuning_progress = ttk.Progressbar(control_frame, length=200, mode='determinate')
        self.tuning_progress.pack(side="left", padx=(0, 10))
        
        # Tuning button
        self.tuning_start_btn = ttk.Button(control_frame, text="Apply Tuning", command=self.on_tuning_start)
        self.tuning_start_btn.pack(side="right")
        self.tuning_start_btn.configure(state="disabled")
        
        # Properties table frame
        table_frame = ttk.LabelFrame(self.tuning_frame, text="LMKD & Chimera Properties", padding=5)
        table_frame.pack(fill="both", expand=True)
        
        # Create treeview for properties table
        self.create_properties_table(table_frame)
    
    def create_properties_table(self, parent):
        """Create properties table with treeview"""
        # Table frame with scrollbars
        table_container = ttk.Frame(parent)
        table_container.pack(fill="both", expand=True)
        
        # Create treeview
        columns = ("Category", "Property", "Value")
        self.properties_tree = ttk.Treeview(table_container, columns=columns, show="tree headings", height=15)
        
        # Configure columns
        self.properties_tree.heading("#0", text="", anchor="w")
        self.properties_tree.column("#0", width=0, stretch=False)
        
        self.properties_tree.heading("Category", text="Category")
        self.properties_tree.column("Category", width=100, anchor="w")
        
        self.properties_tree.heading("Property", text="Property")
        self.properties_tree.column("Property", width=300, anchor="w")
        
        self.properties_tree.heading("Value", text="Value")
        self.properties_tree.column("Value", width=200, anchor="w")
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(table_container, orient="vertical", command=self.properties_tree.yview)
        h_scrollbar = ttk.Scrollbar(table_container, orient="horizontal", command=self.properties_tree.xview)
        self.properties_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack treeview and scrollbars
        self.properties_tree.pack(side="left", fill="both", expand=True)
        v_scrollbar.pack(side="right", fill="y")
        h_scrollbar.pack(side="bottom", fill="x")
        
        # Buttons frame
        buttons_frame = ttk.Frame(parent)
        buttons_frame.pack(fill="x", pady=5)
        
        # Table control buttons
        ttk.Button(buttons_frame, text="Add LMKD Property", command=lambda: self.add_property("LMKD")).pack(side="left", padx=5)
        ttk.Button(buttons_frame, text="Add Chimera Property", command=lambda: self.add_property("Chimera")).pack(side="left", padx=5)
        ttk.Button(buttons_frame, text="Edit Selected", command=self.edit_property).pack(side="left", padx=5)
        ttk.Button(buttons_frame, text="Delete Selected", command=self.delete_property).pack(side="left", padx=5)
        
        # Bind double-click to edit
        self.properties_tree.bind("<Double-1>", lambda e: self.edit_property())
        
        # Store original properties for comparison
        self.original_properties = {}
    
    def create_status_bar(self):
        """Create status bar"""
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill="x", side="bottom")
        
        # Status label (left side)
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(status_frame, textvariable=self.status_var, relief="sunken")
        status_label.pack(side="left", fill="x", expand=True)
        
        # Clear button (right side)
        clear_btn = ttk.Button(status_frame, text="Clear", command=self.on_clear)
        clear_btn.pack(side="right", padx=5, pady=2)
    
    def on_tab_changed(self, event):
        """Handle tab change events"""
        selected_tab = self.notebook.select()
        tab_text = self.notebook.tab(selected_tab, "text")
        
        if tab_text == "Bring up":
            self.switch_mode("bringup")
        elif tab_text == "Tuning value":
            self.switch_mode("tuning")
    
    def switch_mode(self, mode):
        """Switch between different modes"""
        self.current_mode.set(mode)
        
        # Hide all frames first
        for widget in self.main_frame.winfo_children():
            widget.pack_forget()
        
        if mode == "bringup":
            self.bringup_frame.pack(fill="both", expand=True)
            self.status_var.set("Mode: Bring up - VINCE is mandatory, BENI and FLUMEN are optional")
        elif mode == "tuning":
            self.tuning_frame.pack(fill="both", expand=True)
            self.status_var.set("Mode: Tuning value - Load properties first, then modify values as needed")
    
    def bringup_log_callback(self, msg):
        """Thread-safe logging for bringup mode"""
        def update_log():
            self.bringup_log_text.insert(tk.END, msg + "\n")
            self.bringup_log_text.see(tk.END)
            self.root.update_idletasks()
        
        self.root.after(0, update_log)
    
    def bringup_progress_callback(self, value):
        """Thread-safe progress update for bringup mode"""
        def update_progress():
            self.bringup_progress['value'] = value
            self.root.update_idletasks()
        
        self.root.after(0, update_progress)
    
    def tuning_progress_callback(self, value):
        """Thread-safe progress update for tuning mode"""
        def update_progress():
            self.tuning_progress['value'] = value
            self.root.update_idletasks()
        
        self.root.after(0, update_progress)
    
    def error_callback(self, title, message):
        """Thread-safe error dialog"""
        def show_error():
            messagebox.showerror(title, message)
        
        self.root.after(0, show_error)
    
    def info_callback(self, title, message):
        """Thread-safe info dialog"""
        def show_info():
            messagebox.showinfo(title, message)
        
        self.root.after(0, show_info)
    
    def on_clear(self):
        """Clear all input fields based on current mode"""
        if self.current_mode.get() == "bringup":
            # Clear bringup input fields
            self.bringup_beni_entry.delete(0, tk.END)
            self.bringup_vince_entry.delete(0, tk.END)
            self.bringup_flumen_entry.delete(0, tk.END)
            
            # Clear log output
            self.bringup_log_text.delete("1.0", tk.END)
            
            # Reset progress bar
            self.bringup_progress['value'] = 0
            
            self.bringup_log_callback("[INFO] All fields and logs cleared.")
            self.status_var.set("Mode: Bring up - VINCE is mandatory, BENI and FLUMEN are optional")
            
        elif self.current_mode.get() == "tuning":
            # Clear tuning input fields
            self.tuning_beni_entry.delete(0, tk.END)
            self.tuning_flumen_entry.delete(0, tk.END)
            
            # Clear properties table
            for item in self.properties_tree.get_children():
                self.properties_tree.delete(item)
            
            # Reset progress bar and buttons
            self.tuning_progress['value'] = 0
            self.tuning_start_btn.configure(state="disabled")
            self.original_properties = {}
            
            self.status_var.set("Mode: Tuning value - Load properties first, then modify values as needed")
    
    def on_bringup_start(self):
        """Handle bringup start button click"""
        beni_path = self.bringup_beni_entry.get().strip()
        vince_path = self.bringup_vince_entry.get().strip()
        flumen_path = self.bringup_flumen_entry.get().strip()
        
        # Validation - VINCE is mandatory
        if not vince_path.startswith("//"):
            messagebox.showerror("Invalid Path", "VINCE depot path is mandatory and must start with //depot/...")
            return
        
        # Check if at least one target (BENI or FLUMEN) is provided
        has_beni = beni_path and beni_path.startswith("//")
        has_flumen = flumen_path and flumen_path.startswith("//")
        
        if not has_beni and not has_flumen:
            messagebox.showerror("No Target Paths", "At least one target path (BENI or FLUMEN) must be provided and start with //depot/...")
            return
        
        self._run_bringup_process(beni_path, vince_path, flumen_path)
    
    def _run_bringup_process(self, beni_path, vince_path, flumen_path):
        """Run bringup process in separate thread"""
        # Clear log and reset progress
        self.bringup_log_text.delete("1.0", tk.END)
        self.bringup_progress['value'] = 0
        
        # Log P4 configuration info
        client_name = get_client_name()
        workspace_root = get_workspace_root()
        if client_name and workspace_root:
            self.bringup_log_callback(f"[CONFIG] Using P4 Client: {client_name}")
            self.bringup_log_callback(f"[CONFIG] Using Workspace: {workspace_root}")
        
        # Disable start button during processing
        self.bringup_start_btn.configure(state="disabled")
        
        def run_process_thread():
            try:
                self.status_var.set("Processing: Running bring up operation...")
                run_bringup_process(beni_path, vince_path, flumen_path, 
                                  self.bringup_log_callback, self.bringup_progress_callback, self.error_callback)
            finally:
                # Re-enable button when done
                self.root.after(0, lambda: self.bringup_start_btn.configure(state="normal"))
                self.root.after(0, lambda: self.status_var.set("Mode: Bring up - Operation completed"))
        
        # Start the process in a separate thread
        thread = threading.Thread(target=run_process_thread, daemon=True)
        thread.start()
    
    def on_load_properties(self):
        """Handle load properties button click"""
        beni_path = self.tuning_beni_entry.get().strip()
        flumen_path = self.tuning_flumen_entry.get().strip()
        
        # Validation - at least one path is required
        has_beni = beni_path and beni_path.startswith("//")
        has_flumen = flumen_path and flumen_path.startswith("//")
        
        if not has_beni and not has_flumen:
            messagebox.showerror("No Paths", "At least one depot path (BENI or FLUMEN) must be provided and start with //depot/...")
            return
        
        self._load_properties(beni_path if has_beni else "", flumen_path if has_flumen else "")
    
    def _load_properties(self, beni_path, flumen_path):
        """Load properties in separate thread"""
        # Clear table and reset progress
        for item in self.properties_tree.get_children():
            self.properties_tree.delete(item)
        self.tuning_progress['value'] = 0
        
        # Disable buttons during processing
        self.load_properties_btn.configure(state="disabled")
        self.tuning_start_btn.configure(state="disabled")
        
        def load_thread():
            try:
                self.status_var.set("Processing: Loading properties...")
                from processes.tuning_process import load_properties_for_tuning
                properties_data = load_properties_for_tuning(
                    beni_path, flumen_path, self.tuning_progress_callback, 
                    self.error_callback, self.info_callback
                )
                
                if properties_data:
                    # Store original properties
                    self.original_properties = properties_data.copy()
                    
                    # Populate table
                    self.root.after(0, lambda: self._populate_properties_table(properties_data))
                    self.root.after(0, lambda: self.tuning_start_btn.configure(state="normal"))
                    self.root.after(0, lambda: self.status_var.set("Properties loaded successfully. You can now modify values."))
                else:
                    self.root.after(0, lambda: self.status_var.set("Failed to load properties."))
                    
            finally:
                # Re-enable button when done
                self.root.after(0, lambda: self.load_properties_btn.configure(state="normal"))
        
        # Start loading in separate thread
        thread = threading.Thread(target=load_thread, daemon=True)
        thread.start()
    
    def _populate_properties_table(self, properties_data):
        """Populate the properties table with loaded data"""
        # Clear existing items
        for item in self.properties_tree.get_children():
            self.properties_tree.delete(item)
        
        # Add LMKD properties
        if "LMKD" in properties_data and properties_data["LMKD"]:
            lmkd_parent = self.properties_tree.insert("", "end", text="LMKD", values=("LMKD", "", ""))
            for prop, value in properties_data["LMKD"].items():
                self.properties_tree.insert(lmkd_parent, "end", values=("LMKD", prop, value))
        
        # Add Chimera properties
        if "Chimera" in properties_data and properties_data["Chimera"]:
            chimera_parent = self.properties_tree.insert("", "end", text="Chimera", values=("Chimera", "", ""))
            for prop, value in properties_data["Chimera"].items():
                self.properties_tree.insert(chimera_parent, "end", values=("Chimera", prop, value))
        
        # Expand all nodes
        for item in self.properties_tree.get_children():
            self.properties_tree.item(item, open=True)
    
    def add_property(self, category):
        """Add new property to the table"""
        dialog = PropertyDialog(self.root, f"Add {category} Property", "", "")
        if dialog.result:
            prop_name, prop_value = dialog.result
            
            # Find or create category parent
            parent_item = None
            for item in self.properties_tree.get_children():
                if self.properties_tree.item(item, "values")[0] == category:
                    parent_item = item
                    break
            
            if not parent_item:
                parent_item = self.properties_tree.insert("", "end", text=category, values=(category, "", ""))
                self.properties_tree.item(parent_item, open=True)
            
            # Add new property
            self.properties_tree.insert(parent_item, "end", values=(category, prop_name, prop_value))
    
    def edit_property(self):
        """Edit selected property"""
        selected = self.properties_tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a property to edit.")
            return
        
        item = selected[0]
        values = self.properties_tree.item(item, "values")
        
        # Don't edit category headers
        if len(values) < 3 or not values[1]:
            return
        
        category, prop_name, prop_value = values
        dialog = PropertyDialog(self.root, f"Edit {category} Property", prop_name, prop_value)
        if dialog.result:
            new_prop_name, new_prop_value = dialog.result
            self.properties_tree.item(item, values=(category, new_prop_name, new_prop_value))
    
    def delete_property(self):
        """Delete selected property - FIXED VERSION"""
        selected = self.properties_tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a property to delete.")
            return
        
        item = selected[0]
        values = self.properties_tree.item(item, "values")
        
        # Check if it's a category header
        if len(values) >= 3 and values[0] and not values[1]:  # Category header has category but no property name
            # Check if category has children
            children = self.properties_tree.get_children(item)
            if children:
                messagebox.showwarning("Cannot Delete", "Cannot delete category headers that contain properties. Delete all properties first.")
                return
            else:
                # Empty category can be deleted
                if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete the empty '{values[0]}' category?"):
                    self.properties_tree.delete(item)
                return
        
        # Check if it's a property (has both category and property name)
        if len(values) >= 3 and values[1]:
            if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete property '{values[1]}'?"):
                self.properties_tree.delete(item)
                return
        
        # If we get here, selection is invalid
        messagebox.showwarning("Invalid Selection", "Please select a valid property to delete.")
    
    def on_tuning_start(self):
        """Handle tuning start button click"""
        # Get current properties from table
        current_properties = self._get_table_properties()
        
        # Get paths
        beni_path = self.tuning_beni_entry.get().strip()
        flumen_path = self.tuning_flumen_entry.get().strip()
        
        has_beni = beni_path and beni_path.startswith("//")
        has_flumen = flumen_path and flumen_path.startswith("//")
        
        if not has_beni and not has_flumen:
            messagebox.showerror("No Paths", "At least one depot path must be provided.")
            return
        
        self._run_tuning_process(beni_path if has_beni else "", flumen_path if has_flumen else "", current_properties)
    
    def _get_table_properties(self):
        """Extract properties from the table"""
        properties = {"LMKD": {}, "Chimera": {}}
        
        for parent in self.properties_tree.get_children():
            parent_values = self.properties_tree.item(parent, "values")
            category = parent_values[0]
            
            if category in properties:
                for child in self.properties_tree.get_children(parent):
                    child_values = self.properties_tree.item(child, "values")
                    if len(child_values) >= 3 and child_values[1]:
                        properties[category][child_values[1]] = child_values[2]
        
        return properties
    
    def _run_tuning_process(self, beni_path, flumen_path, properties):
        """Run tuning process in separate thread"""
        self.tuning_progress['value'] = 0
        
        # Disable button during processing
        self.tuning_start_btn.configure(state="disabled")
        
        def run_process_thread():
            try:
                self.status_var.set("Processing: Applying tuning changes...")
                run_tuning_process(beni_path, "", flumen_path, properties,
                                 self.tuning_progress_callback, self.error_callback, self.info_callback)
            finally:
                # Re-enable button when done
                self.root.after(0, lambda: self.tuning_start_btn.configure(state="normal"))
                self.root.after(0, lambda: self.status_var.set("Mode: Tuning - Operation completed"))
        
        # Start the process in a separate thread
        thread = threading.Thread(target=run_process_thread, daemon=True)
        thread.start()
    
    def run(self):
        """Start the GUI main loop"""
        self.root.mainloop()


class PropertyDialog:
    """Dialog for adding/editing properties"""
    
    def __init__(self, parent, title, prop_name="", prop_value=""):
        self.result = None
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("400x200")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
        
        # Property name
        ttk.Label(self.dialog, text="Property Name:").pack(pady=5)
        self.name_entry = ttk.Entry(self.dialog, width=50)
        self.name_entry.pack(pady=5)
        self.name_entry.insert(0, prop_name)
        
        # Property value
        ttk.Label(self.dialog, text="Property Value:").pack(pady=5)
        self.value_entry = ttk.Entry(self.dialog, width=50)
        self.value_entry.pack(pady=5)
        self.value_entry.insert(0, prop_value)
        
        # Buttons
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text="OK", command=self.ok_clicked).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.cancel_clicked).pack(side="left", padx=5)
        
        # Focus on name entry
        self.name_entry.focus()
        
        # Bind Enter key
        self.dialog.bind('<Return>', lambda e: self.ok_clicked())
        self.dialog.bind('<Escape>', lambda e: self.cancel_clicked())
        
        # Wait for dialog to close
        self.dialog.wait_window()
    
    def ok_clicked(self):
        """Handle OK button click"""
        prop_name = self.name_entry.get().strip()
        prop_value = self.value_entry.get().strip()
        
        if not prop_name:
            messagebox.showerror("Invalid Input", "Property name cannot be empty.")
            return
        
        self.result = (prop_name, prop_value)
        self.dialog.destroy()
    
    def cancel_clicked(self):
        """Handle Cancel button click"""
        self.result = None
        self.dialog.destroy()


def create_gui():
    """Create and run the GUI application"""
    try:
        app = BringupToolGUI()
        app.run()
    except Exception as e:
        # Show error dialog if GUI creation fails
        root = tk.Tk()
        root.withdraw()  # Hide the empty window
        messagebox.showerror("Application Error", f"Failed to start application: {e}")
        root.destroy()