##
#     Project: GNOME App Folders Manager
# Description: Manage GNOME Shell applications folders
#      Author: Fabio Castelli (Muflone) <muflone@vbsimple.net>
#   Copyright: 2016 Fabio Castelli
#     License: GPL-2+
#  This program is free software; you can redistribute it and/or modify it
#  under the terms of the GNU General Public License as published by the Free
#  Software Foundation; either version 2 of the License, or (at your option)
#  any later version.
#
#  This program is distributed in the hope that it will be useful, but WITHOUT
#  ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
#  FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
#  more details.
#  You should have received a copy of the GNU General Public License along
#  with this program; if not, write to the Free Software Foundation, Inc.,
#  51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA
##

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import Gio

from gnome_appfolders_manager.constants import (
    APP_NAME,
    FILE_SETTINGS, FILE_WINDOWS_POSITION,
    SCHEMA_FOLDERS)
from gnome_appfolders_manager.functions import (
    get_ui_file, get_treeview_selected_row, text, _)
import gnome_appfolders_manager.preferences as preferences
import gnome_appfolders_manager.settings as settings
from gnome_appfolders_manager.gtkbuilder_loader import GtkBuilderLoader

from gnome_appfolders_manager.ui.about import UIAbout

from gnome_appfolders_manager.models.folder_info import FolderInfo
from gnome_appfolders_manager.models.appfolder_info import AppFolderInfo
from gnome_appfolders_manager.models.appfolders import ModelAppFolders
from gnome_appfolders_manager.models.application_info import ApplicationInfo
from gnome_appfolders_manager.models.applications import ModelApplications

SECTION_WINDOW_NAME = 'main'


class UIMain(object):
    def __init__(self, application):
        self.application = application
        # Load settings
        settings.settings = settings.Settings(FILE_SETTINGS, False)
        settings.positions = settings.Settings(FILE_WINDOWS_POSITION, False)
        self.folders = {}
        preferences.preferences = preferences.Preferences()
        self.loadUI()
        # Prepares the models for folders and applications
        self.model_folders = ModelAppFolders(self.ui.store_folders)
        self.model_applications = ModelApplications(self.ui.store_applications)
        # Detect the AppFolders and select the first one automatically
        self.reload_folders()
        if self.model_folders.count() > 0:
            self.ui.treeview_folders.set_cursor(0)
        self.ui.treeview_folders.grab_focus()
        # Restore the saved size and position
        settings.positions.restore_window_position(
            self.ui.win_main, SECTION_WINDOW_NAME)

    def loadUI(self):
        """Load the interface UI"""
        self.ui = GtkBuilderLoader(get_ui_file('main.ui'))
        self.ui.win_main.set_application(self.application)
        self.ui.win_main.set_title(APP_NAME)
        # Initialize actions
        for widget in self.ui.get_objects_by_type(Gtk.Action):
            # Connect the actions accelerators
            widget.connect_accelerator()
            # Set labels
            widget.set_label(text(widget.get_label()))
        # Initialize tooltips
        for widget in self.ui.get_objects_by_type(Gtk.ToolButton):
            action = widget.get_related_action()
            if action:
                widget.set_tooltip_text(action.get_label().replace('_', ''))
        # Initialize Gtk.HeaderBar
        self.ui.header_bar.props.title = self.ui.win_main.get_title()
        self.ui.win_main.set_titlebar(self.ui.header_bar)
        for button in (self.ui.button_folder_new, self.ui.button_folder_remove,
                       self.ui.button_files_add, self.ui.button_files_remove,
                       self.ui.button_files_save, self.ui.button_about, ):
            action = button.get_related_action()
            icon_name = action.get_icon_name()
            if preferences.get(preferences.HEADERBARS_SYMBOLIC_ICONS):
                icon_name += '-symbolic'
            # Get desired icon size
            icon_size = (Gtk.IconSize.BUTTON
                         if preferences.get(preferences.HEADERBARS_SMALL_ICONS)
                         else Gtk.IconSize.LARGE_TOOLBAR)
            button.set_image(Gtk.Image.new_from_icon_name(icon_name,
                                                          icon_size))
            # Remove the button label
            button.props.label = None
            # Set the tooltip from the action label
            button.set_tooltip_text(action.get_label().replace('_', ''))
        # Connect signals from the glade file to the module functions
        self.ui.connect_signals(self)

    def run(self):
        """Show the UI"""
        self.ui.win_main.show_all()

    def on_win_main_delete_event(self, widget, event):
        """Save the settings and close the application"""
        settings.positions.save_window_position(
            self.ui.win_main, SECTION_WINDOW_NAME)
        settings.positions.save()
        settings.settings.save()
        self.application.quit()

    def on_action_about_activate(self, action):
        """Show the about dialog"""
        dialog = UIAbout(self.ui.win_main)
        dialog.show()
        dialog.destroy()

    def on_action_quit_activate(self, action):
        """Close the application by closing the main window"""
        event = Gdk.Event()
        event.key.type = Gdk.EventType.DELETE
        self.ui.win_main.event(event)

    def reload_folders(self):
        """Reload the Application Folders"""
        self.folders = {}
        settings_folders = Gio.Settings.new(SCHEMA_FOLDERS)
        list_folders = settings_folders.get_value('folder-children')
        for folder_name in list_folders:
            folder_info = FolderInfo(folder_name)
            appfolder = AppFolderInfo(folder_info)
            self.model_folders.add_data(appfolder)
            self.folders[folder_info.folder] = folder_info

    def on_treeview_folders_cursor_changed(self, widget):
        selected_row = get_treeview_selected_row(self.ui.treeview_folders)
        if selected_row:
            folder_name = self.model_folders.get_key(selected_row)
            folder_info = self.folders[folder_name]
            self.ui.lbl_name_text.set_label(folder_info.folder)
            self.ui.lbl_title_text.set_label(
                folder_info.desktop_entry.getName())
            self.ui.lbl_description_text.set_label(
                folder_info.desktop_entry.getComment())
            # Clear any previous application icon
            self.model_applications.clear()
            # Add new application icons
            applications = folder_info.get_applications()
            for application in applications:
                desktop_file = applications[application]
                if desktop_file or not preferences.get(
                        preferences.PREFERENCES_HIDE_MISSING):
                    application_file = applications[application]
                    application_info = ApplicationInfo(
                        application,
                        application_file.getName()
                        if desktop_file else 'Missing desktop file',
                        application_file.getComment()
                        if desktop_file else application,
                        application_file.getIcon() if desktop_file else None)
                    self.model_applications.add_data(application_info)
