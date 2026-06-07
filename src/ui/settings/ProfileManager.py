"""
ProfileManager - UI interface for profile management

Provides a graphical interface for creating, editing, switching,
and managing user profiles.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict, Any, Optional, List
import copy

from src.core.ProfileService import ProfileService, Profile


class ProfileManager:
    """UI window for managing user profiles"""

    def __init__(self, parent, config_manager, on_profile_change=None):
        """
        Initialize the profile manager window.

        Args:
            parent: Parent window
            config_manager: ConfigManager instance
            on_profile_change: Callback function when profile changes
        """
        self.parent = parent
        self.config_manager = config_manager
        self.on_profile_change = on_profile_change
        self.profile_service = ProfileService()

        self.window = None
        self.current_profile_var = None
        self.profile_listbox = None
        self.create_profile_window()

    def create_profile_window(self):
        """Create the profile management window"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("Profile Manager")
        self.window.geometry("800x600")
        self.window.resizable(True, True)

        # Make window modal
        self.window.transient(self.parent)
        self.window.grab_set()

        # Create main frame
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)

        # Current profile section
        self.create_current_profile_section(main_frame)

        # Profile list section
        self.create_profile_list_section(main_frame)

        # Action buttons
        self.create_action_buttons(main_frame)

        # Load profiles
        self.refresh_profile_list()
        self.update_current_profile_display()

        # Center window on parent
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (self.window.winfo_width() // 2)
        y = (self.window.winfo_screenheight() // 2) - (self.window.winfo_height() // 2)
        self.window.geometry(f"+{x}+{y}")

    def create_current_profile_section(self, parent):
        """Create current profile display section"""
        frame = ttk.LabelFrame(parent, text="Current Profile", padding="10")
        frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))

        self.current_profile_var = tk.StringVar()
        ttk.Label(frame, text="Active Profile:").grid(row=0, column=0, sticky=tk.W)
        current_label = ttk.Label(frame, textvariable=self.current_profile_var,
                                 font=("TkDefaultFont", 10, "bold"))
        current_label.grid(row=0, column=1, sticky=tk.W, padx=(10, 0))

    def create_profile_list_section(self, parent):
        """Create profile list and details section"""
        # Left side - Profile list
        list_frame = ttk.LabelFrame(parent, text="Profiles", padding="10")
        list_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        # Profile listbox with scrollbar
        list_container = ttk.Frame(list_frame)
        list_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        list_container.columnconfigure(0, weight=1)
        list_container.rowconfigure(0, weight=1)

        scrollbar = ttk.Scrollbar(list_container)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        self.profile_listbox = tk.Listbox(list_container, yscrollcommand=scrollbar.set,
                                         selectmode=tk.SINGLE)
        self.profile_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.config(command=self.profile_listbox.yview)

        self.profile_listbox.bind('<<ListboxSelect>>', self.on_profile_select)

        # Right side - Profile details
        details_frame = ttk.LabelFrame(parent, text="Profile Details", padding="10")
        details_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))
        details_frame.columnconfigure(1, weight=1)

        # Profile name
        ttk.Label(details_frame, text="Name:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.profile_name_var = tk.StringVar()
        self.profile_name_entry = ttk.Entry(details_frame, textvariable=self.profile_name_var)
        self.profile_name_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=(0, 5))

        # Profile description
        ttk.Label(details_frame, text="Description:").grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
        self.profile_desc_text = tk.Text(details_frame, height=4, width=40)
        self.profile_desc_text.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 5))

        # Profile info
        info_frame = ttk.Frame(details_frame)
        info_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))

        self.created_label = ttk.Label(info_frame, text="Created: N/A", font=("TkDefaultFont", 8))
        self.created_label.grid(row=0, column=0, sticky=tk.W)

        self.modified_label = ttk.Label(info_frame, text="Modified: N/A", font=("TkDefaultFont", 8))
        self.modified_label.grid(row=1, column=0, sticky=tk.W)

        self.active_label = ttk.Label(info_frame, text="Status: Inactive", font=("TkDefaultFont", 8))
        self.active_label.grid(row=2, column=0, sticky=tk.W)

    def create_action_buttons(self, parent):
        """Create action buttons frame"""
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))

        # Left buttons
        left_frame = ttk.Frame(button_frame)
        left_frame.grid(row=0, column=0, sticky=tk.W)

        ttk.Button(left_frame, text="New Profile", command=self.create_new_profile).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(left_frame, text="Switch To", command=self.switch_to_profile).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(left_frame, text="Save Changes", command=self.save_profile_changes).pack(side=tk.LEFT, padx=(0, 5))

        # Right buttons
        right_frame = ttk.Frame(button_frame)
        right_frame.grid(row=0, column=1, sticky=tk.E)

        ttk.Button(right_frame, text="Import", command=self.import_profile).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(right_frame, text="Export", command=self.export_profile).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(right_frame, text="Delete", command=self.delete_profile).pack(side=tk.RIGHT, padx=(5, 0))

    def refresh_profile_list(self):
        """Refresh the profile list display"""
        try:
            # Clear current list
            self.profile_listbox.delete(0, tk.END)

            # Get profiles
            profiles = self.profile_service.load_all_profiles()
            current_profile = self.profile_service.get_current_profile()

            # Add profiles to listbox
            for profile_name in sorted(profiles.keys()):
                profile = profiles[profile_name]
                display_name = profile_name
                if profile.is_active:
                    display_name += " ✓"
                self.profile_listbox.insert(tk.END, display_name)

                # Highlight current profile
                if current_profile and profile_name == current_profile.name:
                    self.profile_listbox.selection_set(tk.END)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh profiles: {e}")

    def update_current_profile_display(self):
        """Update the current profile display"""
        try:
            current_profile = self.profile_service.get_current_profile()
            if current_profile:
                self.current_profile_var.set(current_profile.name)
            else:
                self.current_profile_var.set("None")
        except Exception as e:
            self.current_profile_var.set("Error")

    def on_profile_select(self, event):
        """Handle profile selection"""
        try:
            selection = self.profile_listbox.curselection()
            if not selection:
                return

            # Get profile name (remove ✓ if present)
            profile_name = self.profile_listbox.get(selection[0]).replace(" ✓", "")
            profile = self.profile_service.get_profile(profile_name)

            if profile:
                self.load_profile_details(profile)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load profile: {e}")

    def load_profile_details(self, profile: Profile):
        """Load profile details into the UI"""
        try:
            self.profile_name_var.set(profile.name)
            self.profile_desc_text.delete(1.0, tk.END)
            self.profile_desc_text.insert(1.0, profile.description)

            # Update info labels
            if profile.created_at:
                self.created_label.config(text=f"Created: {profile.created_at[:10]}")
            else:
                self.created_label.config(text="Created: N/A")

            if profile.modified_at:
                self.modified_label.config(text=f"Modified: {profile.modified_at[:10]}")
            else:
                self.modified_label.config(text="Modified: N/A")

            status = "Active" if profile.is_active else "Inactive"
            self.active_label.config(text=f"Status: {status}")

            # Disable editing for default profile
            is_default = profile.name == "Default"
            self.profile_name_entry.config(state='normal' if not is_default else 'disabled')
            self.profile_desc_text.config(state='normal' if not is_default else 'disabled')

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load profile details: {e}")

    def create_new_profile(self):
        """Create a new profile dialog"""
        try:
            dialog = ProfileDialog(self.window, "Create New Profile")
            profile_data = dialog.show()

            if profile_data:
                name, description = profile_data
                # Use current settings as base
                current_settings = self.config_manager.load_settings({})

                profile = self.profile_service.create_profile(
                    name=name,
                    description=description,
                    base_settings=current_settings
                )

                if profile:
                    self.refresh_profile_list()
                    messagebox.showinfo("Success", f"Profile '{name}' created successfully!")
                else:
                    messagebox.showerror("Error", f"Failed to create profile '{name}'")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to create profile: {e}")

    def switch_to_profile(self):
        """Switch to selected profile"""
        try:
            selection = self.profile_listbox.curselection()
            if not selection:
                messagebox.showwarning("Warning", "Please select a profile to switch to")
                return

            profile_name = self.profile_listbox.get(selection[0]).replace(" ✓", "")

            if self.profile_service.switch_profile(profile_name):
                self.refresh_profile_list()
                self.update_current_profile_display()

                # Update current settings in config manager
                profile = self.profile_service.get_profile(profile_name)
                if profile and self.on_profile_change:
                    self.on_profile_change(profile.settings)

                messagebox.showinfo("Success", f"Switched to profile '{profile_name}'")
            else:
                messagebox.showerror("Error", f"Failed to switch to profile '{profile_name}'")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to switch profile: {e}")

    def save_profile_changes(self):
        """Save changes to the selected profile"""
        try:
            selection = self.profile_listbox.curselection()
            if not selection:
                messagebox.showwarning("Warning", "Please select a profile to save")
                return

            profile_name = self.profile_listbox.get(selection[0]).replace(" ✓", "")

            if profile_name == "Default":
                messagebox.showwarning("Warning", "Cannot modify the default profile")
                return

            # Get updated values
            new_name = self.profile_name_var.get().strip()
            if not new_name:
                messagebox.showerror("Error", "Profile name cannot be empty")
                return

            description = self.profile_desc_text.get(1.0, tk.END).strip()

            # Get current profile
            profile = self.profile_service.get_profile(profile_name)
            if not profile:
                messagebox.showerror("Error", "Profile not found")
                return

            # Update profile
            if new_name != profile_name:
                # Name change - create new profile and delete old one
                profile.name = new_name
                profile.description = description
                if self.profile_service._save_profile(profile):
                    self.profile_service.delete_profile(profile_name)
                else:
                    messagebox.showerror("Error", "Failed to update profile name")
                    return
            else:
                # Just update description
                profile.description = description
                self.profile_service._save_profile(profile)

            self.refresh_profile_list()
            messagebox.showinfo("Success", "Profile saved successfully!")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save profile: {e}")

    def delete_profile(self):
        """Delete selected profile"""
        try:
            selection = self.profile_listbox.curselection()
            if not selection:
                messagebox.showwarning("Warning", "Please select a profile to delete")
                return

            profile_name = self.profile_listbox.get(selection[0]).replace(" ✓", "")

            if profile_name == "Default":
                messagebox.showwarning("Warning", "Cannot delete the default profile")
                return

            # Confirm deletion
            if messagebox.askyesno("Confirm Delete",
                                  f"Are you sure you want to delete profile '{profile_name}'?"):
                if self.profile_service.delete_profile(profile_name):
                    self.refresh_profile_list()
                    messagebox.showinfo("Success", f"Profile '{profile_name}' deleted successfully!")
                else:
                    messagebox.showerror("Error", f"Failed to delete profile '{profile_name}'")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete profile: {e}")

    def export_profile(self):
        """Export selected profile"""
        try:
            selection = self.profile_listbox.curselection()
            if not selection:
                messagebox.showwarning("Warning", "Please select a profile to export")
                return

            profile_name = self.profile_listbox.get(selection[0]).replace(" ✓", "")

            # Ask for save location
            file_path = filedialog.asksaveasfilename(
                title="Export Profile",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                initialfile=f"{profile_name}_profile.json"
            )

            if file_path:
                if self.profile_service.export_profile(profile_name, file_path):
                    messagebox.showinfo("Success", f"Profile exported to {file_path}")
                else:
                    messagebox.showerror("Error", "Failed to export profile")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to export profile: {e}")

    def import_profile(self):
        """Import profile from file"""
        try:
            # Ask for file location
            file_path = filedialog.askopenfilename(
                title="Import Profile",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )

            if file_path:
                # Check if profile already exists
                imported_profile = self.profile_service.import_profile(file_path)
                if imported_profile:
                    if self.profile_service.profile_exists(imported_profile.name):
                        # Ask if user wants to overwrite
                        if not messagebox.askyesno("Profile Exists",
                                                  f"Profile '{imported_profile.name}' already exists. Overwrite?"):
                            return
                        # Overwrite existing profile
                        imported_profile = self.profile_service.import_profile(file_path, overwrite=True)

                    if imported_profile:
                        self.refresh_profile_list()
                        messagebox.showinfo("Success", f"Profile '{imported_profile.name}' imported successfully!")
                    else:
                        messagebox.showerror("Error", "Failed to import profile")
                else:
                    messagebox.showerror("Error", "Failed to import profile")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to import profile: {e}")

    def close(self):
        """Close the profile manager window"""
        if self.window:
            self.window.destroy()


class ProfileDialog:
    """Dialog for creating/editing profiles"""

    def __init__(self, parent, title="Profile"):
        self.parent = parent
        self.title = title
        self.result = None
        self.window = None

    def show(self) -> Optional[tuple]:
        """Show the dialog and return the result"""
        self.window = tk.Toplevel(self.parent)
        self.window.title(self.title)
        self.window.geometry("400x200")
        self.window.resizable(False, False)

        # Make window modal
        self.window.transient(self.parent)
        self.window.grab_set()

        # Create form
        main_frame = ttk.Frame(self.window, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Profile name
        ttk.Label(main_frame, text="Profile Name:").grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        self.name_var = tk.StringVar()
        name_entry = ttk.Entry(main_frame, textvariable=self.name_var, width=30)
        name_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=(0, 10))

        # Profile description
        ttk.Label(main_frame, text="Description:").grid(row=1, column=0, sticky=tk.W, pady=(0, 10))
        self.desc_text = tk.Text(main_frame, height=4, width=30)
        self.desc_text.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=(0, 10))

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=(20, 0))

        ttk.Button(button_frame, text="OK", command=self.ok_clicked).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Cancel", command=self.cancel_clicked).pack(side=tk.LEFT)

        # Configure grid
        main_frame.columnconfigure(1, weight=1)

        # Focus on name entry
        name_entry.focus()
        name_entry.select_range(0, tk.END)

        # Center window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (self.window.winfo_width() // 2)
        y = (self.window.winfo_screenheight() // 2) - (self.window.winfo_height() // 2)
        self.window.geometry(f"+{x}+{y}")

        # Wait for dialog to close
        self.window.wait_window()
        return self.result

    def ok_clicked(self):
        """Handle OK button click"""
        name = self.name_var.get().strip()
        if not name:
            messagebox.showerror("Error", "Profile name cannot be empty")
            return

        description = self.desc_text.get(1.0, tk.END).strip()
        self.result = (name, description)
        self.window.destroy()

    def cancel_clicked(self):
        """Handle Cancel button click"""
        self.window.destroy()