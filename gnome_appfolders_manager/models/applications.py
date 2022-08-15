##
#     Project: GNOME AppFolders Manager
# Description: Manage GNOME Shell applications folders
#      Author: Fabio Castelli (Muflone) <muflone@muflone.com>
#   Copyright: 2016-2022 Fabio Castelli
#     License: GPL-3+
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.
##

from gi.repository import GLib

from gnome_appfolders_manager.constants import MISSING_ICON_NAME
from gnome_appfolders_manager.functions import get_pixbuf_from_icon_name
from gnome_appfolders_manager.models.abstract import ModelAbstract


class ModelApplications(ModelAbstract):
    COL_TITLE = 1
    COL_COMMENT = 2
    COL_DESCRIPTION = 3
    COL_ICON = 4
    COL_VALID = 5
    COL_VISIBLE = 6

    def __init__(self, model):
        super(self.__class__, self).__init__(model)
        self.items = {}

    def add_data(self, item):
        """Add a new row to the model if it doesn't exist"""
        super(self.__class__, self).add_data(item)
        if item.filename not in self.rows:
            icon = None
            if item.icon_name:
                icon = get_pixbuf_from_icon_name(item.icon_name, 48)
            # Use a fallback icon if the icon was not found, or it was missing
            if not icon:
                icon = get_pixbuf_from_icon_name(MISSING_ICON_NAME, 48)
            new_row = self.model.append((
                item.filename,
                item.name,
                item.description,
                '<b>{name}</b>\n'
                '<small>{description}</small>\n'
                '<small>{filename}</small>'.format(**{
                    'name': item.name,
                    'description': item.description,
                    'filename': GLib.markup_escape_text(item.filename)}),
                icon,
                item.valid,
                item.valid))
            self.rows[item.filename] = new_row
            self.items[item.filename] = item
            return new_row

    def get_title(self, treeiter):
        """Get the title from a TreeIter"""
        return self.model[treeiter][self.COL_TITLE]

    def get_description(self, treeiter):
        """Get the description from a TreeIter"""
        return self.model[treeiter][self.COL_DESCRIPTION]

    def get_icon(self, treeiter):
        """Get the icon from a TreeIter"""
        return self.model[treeiter][self.COL_ICON]

    def set_all_rows_visibility(self, visible):
        """Set all items visible or restore the valid column for visibility"""
        for treeiter in self.model:
            self.model[treeiter.path][self.COL_VISIBLE] = (
                # All rows are visible
                True if visible
                # Only valid rows are visible
                else self.model[treeiter.path][self.COL_VALID])
