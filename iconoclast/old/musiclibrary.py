# -*- coding: utf-8 -*-

"""
TreeFileBrowser a tree-like gtk file browser
Copyright (C) 2006-2008 Adolfo González Blázquez <code@infinicode.org>

This library is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License as
published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.

If you find any bugs or have any suggestions email: code@infinicode.org
"""
try:
    from gi.repository import Gtk, GdkPixbuf
    from gi.repository import GObject
except:
    raise SystemExit

from gettext import gettext as _

import os
from os.path import splitext
try:
    from os import path as ospath
    import dircache
except:
    raise SystemExit

class TreeFileBrowser(GObject.GObject):
    """ A widget that implements a tree-like file browser, like the
    one used on Nautilus spatial view in list mode """

    __gproperties__ = {        
        'rules-hint': (GObject.TYPE_BOOLEAN, 'rules hint',
                       'show rows background in alternate colors', True, GObject.PARAM_READWRITE),
        'root': (GObject.TYPE_STRING, 'initial path',
                 'initial path selected on tree browser', '/', GObject.PARAM_READWRITE)
    }

    __gsignals__ = { 'row-expanded' : (GObject.SignalFlags.RUN_LAST, None, (GObject.TYPE_STRING,)),
                     'cursor-changed' : (GObject.SignalFlags.RUN_LAST, None, (GObject.TYPE_STRING,))
    }

    def __init__(self, root=None):
        """ Path is where we wan the tree initialized """

        GObject.GObject.__init__(self)

        self.show_hidden = False
        self.show_only_dirs = False
        self.show_rules_hint = True

        self.root = '/'
        if root != None and ospath.isdir(root): self.root = root
        #elif root != None: print "ERROR: %s doesn't exist." % root

        self.view, self.scrolled = self.make_view()
        self.create_new()
        self.create_popup()

    #####################################################
    # Accessors and Mutators

    def get_view(self):
        return self.view

    def get_scrolled(self):
        return self.scrolled

    def set_rules_hint(self, rules):
        self.show_rules_hint = rules
        self.view.set_rules_hint(rules)

    def get_rules_hint(self):
        return self.show_rules_hint

    def get_selected(self):
        """ Returns selected item in browser """
        model, iter = self.view.get_selection().get_selected()
        if iter != None:
            return model.get_value(iter, 2)
        else:
            return None


    #####################################################
    # Callbacks

    def row_expanded(self, treeview, iter, path):
        """ CALLBACK: a row is expanded """

        model = treeview.get_model()
        model.set_value(iter, 0, self.get_folder_opened_icon())
        self.get_file_list(model, iter, model.get_value(iter,2))
        self.remove_empty_child(model, iter)

        # Send signal with path of expanded row
        self.emit('row-expanded', model.get_value(iter,2))


    def row_collapsed(self, treeview, iter, path):
        """ CALLBACK: a row is collapsed """

        model = treeview.get_model()
        model.set_value(iter, 0, self.get_folder_closed_icon())
        while model.iter_has_child(iter):
            child = model.iter_children(iter)
            model.remove(child)
        self.add_empty_child(model, iter)


    def row_activated(self, treeview, path, view_column):
        """ CALLBACK: row activated using return, double-click, shift-right, etc. """

        if treeview.row_expanded(path):
            treeview.collapse_row(path)
        else:
            treeview.expand_row(path, False)


    def cursor_changed(self, treeview):
        """ CALLBACK: a new row has been selected """
        model, iter = treeview.get_selection().get_selected()

        # Send signal with path of expanded row
        if iter == None:
            path = treeview.get_cursor()[0]
            iter = self.model.get_iter(path)

        self.emit('cursor-changed', model.get_value(iter,2))


    def button_pressed(self, widget, event):
        """ CALLBACK: clicked on widget """
        if event.button == 3:
            x = int(event.x)
            y = int(event.y)
            time = event.time
            pthinfo = self.view.get_path_at_pos(x, y)
            if pthinfo is not None:
                path, col, cellx, celly = pthinfo
                #self.view.grab_focus()
                #self.view.set_cursor( path, col, 0)
                self.popup.popup( None, None, None, None, event.button, time)
            return 1

    def show_hidden_toggled(self, widget):
        """ CALLBACK: Show hidden files on context menu toggled """
        state = widget.get_active()
        self.set_show_hidden(state)


    #####################################################
    # Directories and files, nodes and icons

    def set_cursor_on_first_row(self):
        model = self.view.get_model()
        iter = model.get_iter_root()
        path = model.get_path(iter)
        self.view.set_cursor(path)

    def check_active_dir(self, directory):
        rootdir = self.root
        if not ospath.isdir(directory):
            return False
        if  not (rootdir in directory):
            return False
        if  directory == rootdir:
            return True
        return True


    def set_active_dir(self, directory):

        rootdir = self.root

        # Expand root
        model = self.view.get_model()
        iter = model.get_iter_root()
        path = model.get_path(iter)
        self.view.expand_row(path, False)
        iter = model.iter_children(iter)

        # Add trailing / to paths
        if len(directory) > 1 and directory[-1] != '/': directory += '/'
        if len(rootdir) > 1 and rootdir[-1] != '/':  rootdir += '/'

        if not ospath.isdir(directory):
            #print "ERROR: %s doesn't exist." % directory
            self.set_cursor_on_first_row()
            return False
        if  not (rootdir in directory):
            #print "ERROR: %s is not on root path." % directory
            self.set_cursor_on_first_row()
            return False
        if  directory == rootdir:
            self.set_cursor_on_first_row()
            return True
        else:

            # Now we check if the desired dir is valid
            # Convert the given '/home/user/dir/' to ['/', 'home/', 'user/', 'dir/']
            if len(directory) > 1:
                dirtree = directory.split('/')
                dirtree.pop(-1)
            else: dirtree = ['/']
            if len(dirtree) > 1:
                dirtree[0] = '/'
                for i in range(len(dirtree)-1): dirtree[i+1] = dirtree[i+1] + '/'

            # Convert root to '/home/user/dir/' to ['/', 'home/', 'user/', 'dir/']
            if len(rootdir) > 1:
                roottree = rootdir.split('/')
                roottree.pop(-1)
            else: roottree = ['/']
            if len(roottree) > 1:
                roottree[0] = '/'
                for i in range(len(roottree)-1): roottree[i+1] = roottree[i+1] + '/'

            # Check if the dir is in the same path as the desired root
            long = len(roottree)
            for i in range(long):
                if  roottree[i] != dirtree[i]: return False

            # End checking

            # Star expanding
            # Count how many iterations we need
            depth = len(dirtree) - len(roottree)

            # Expand baby expand!
            exp = len(roottree)
            for i in range(depth):
                newpath = dirtree[i+exp]
                if iter == None: continue
                val = model.get_value(iter, 1).replace('/','') + '/'
                while val != newpath:
                    iter = model.iter_next(iter)
                    val = model.get_value(iter, 1).replace('/','') + '/'

                path = model.get_path(iter)
                self.view.expand_row(path, False)
                iter = model.iter_children(iter)

            # Don't expand last row
            self.view.collapse_row(path)

            # Set the cursor
            self.view.set_cursor(path)

            return True


    def add_empty_child(self, model, iter):
        """ Adds a empty child to a node.
        Used when we need a folder that have children to show the expander arrow """

        model.insert_before(iter, None)


    def remove_empty_child(self, model, iter):
        """ Delete empty child from a node.
        Used to remove the extra child used to show the expander arrow
        on folders with children """

        newiter = model.iter_children(iter)
        model.remove(newiter)

    def get_music_library(self, top_level_dir=None):
	fileFormats = {'.mp3','.ogg','.oga','.wma','.flac','.m4a','.mp4'}
	songList = []

	def processDirectory ( args, dirname, filenames ):                              
	    for filename in filenames:     
		if splitext(filename.lower())[1] in fileFormats:
			#print dirname + '/' + filename
			songList.append(dirname + '/' + filename) 
		                                                                        
	top_level_dir = "/media/Media/Music"                                                    
	os.path.walk(top_level_dir, processDirectory, None )
	return songList

    def get_file_list(self, model, iter, dir):
        """ Get the file list from a given directory """

        ls = dircache.listdir(dir)
	#ls = self.get_music_library()
        ls.sort(key=str.lower)
        for i in ls:
            path = ospath.join(dir,i)
            if ospath.isdir(path) or not self.show_only_dirs :
                if i[0] != '.' or (self.show_hidden and i[0] == '.'):
                    newiter = model.append(iter)
                    if ospath.isdir(path): icon = self.get_folder_closed_icon()
                    else: icon = self.get_file_icon()
                    model.set_value(newiter, 0, icon)
                    model.set_value(newiter, 1, i)
                    model.set_value(newiter, 2, path)
                    if ospath.isdir(path):
                    	try: subdir = dircache.listdir(path)
                    	except: subdir = []
                        if subdir != []:
                            for i in subdir:
                                if ospath.isdir(ospath.join(path,i)) or not self.show_only_dirs:
                                    if i[0] != '.' or (self.show_hidden and i[0] == '.'):					
                                        self.add_empty_child(model, newiter)
                                        break

    def create_root(self):

        model = self.view.get_model()

        if self.root != '/':
            if self.root[-1] == '/': self.root  = self.root.rsplit('/',1)[0] # Remove last / if neccesary
            directory = self.root.split('/')[-1]
        else: directory = self.root

        iter = model.insert_before(None, None)
        model.set_value(iter, 0, self.get_folder_opened_icon())
        model.set_value(iter, 1, directory)
        model.set_value(iter, 2, self.root)
        iter = model.insert_before(iter, None)
        return iter

    def create_new(self):
        """ Create tree from scratch """

        model = self.view.get_model()
        model.clear()
        iter = self.create_root()
        self.get_file_list(self.view.get_model(), iter, self.root)


    def create_popup(self):
        """ Create popup menu for right click """
        self.popup = Gtk.Menu()

        self.hidden_check_menu = Gtk.CheckMenuItem()
	self.hidden_check_menu.set_label(_("Show hidden files"))
        self.hidden_check_menu.connect('toggled', self.show_hidden_toggled)

        self.popup.add(self.hidden_check_menu)
        self.popup.show_all()


    def get_folder_closed_icon(self):
        """ Returns a pixbuf with the current theme closed folder icon """

        icon_theme = Gtk.IconTheme.get_default()
        try:
            icon = icon_theme.load_icon("gnome-fs-directory", 16, 0)
            return icon
        except GObject.GError, exc:
            #print "Can't load icon", exc
            try:
                icon = icon_theme.load_icon("gtk-directory", 16, 0)
                return icon
            except:
                #print "Can't load default icon"
                return None


    def get_folder_opened_icon(self):
        """ Returns a pixbuf with the current theme opened folder icon """

        icon_theme = Gtk.IconTheme.get_default()
        try:
            icon = icon_theme.load_icon("gnome-fs-directory-accept", 16, 0)
            return icon
        except GObject.GError, exc:
            #print "Can't load icon", exc
            try:
                icon = icon_theme.load_icon("gtk-directory", 16, 0)
                return icon
            except:
                #print "Can't load default icon"
                return None


    def get_file_icon(self):
        """ Returns a pixbuf with the current theme file icon """

        icon_theme = Gtk.IconTheme.get_default()
        try:
            icon = icon_theme.load_icon("text-plain", 16, 0)
            return icon
        except GObject.GError, exc:
            #print "Can't load icon", exc
            return None


    #####################################################
    # Model, treeview and scrolledwindow

    def make_view(self):
        """ Create the view itself.
            (Icon, dir name, path) """
        self.model = Gtk.TreeStore(GdkPixbuf.Pixbuf, GObject.TYPE_STRING, GObject.TYPE_STRING)

        view = Gtk.TreeView(model = self.model)
        view.set_headers_visible(False)
        view.set_enable_search(True)
        view.set_reorderable(False)
        view.set_rules_hint(self.show_rules_hint)
        view.connect('row-expanded',  self.row_expanded)
        view.connect('row-collapsed', self.row_collapsed)
        view.connect('row-activated', self.row_activated)
        view.connect('cursor-changed', self.cursor_changed)
        view.connect('button_press_event', self.button_pressed)

        col = Gtk.TreeViewColumn()

        # The icon
        render_pixbuf = Gtk.CellRendererPixbuf()
        col.pack_start(render_pixbuf, 0)
        col.add_attribute(render_pixbuf, 'pixbuf', 0)

        # The dir name
        render_text = Gtk.CellRendererText()
        col.pack_start(render_text, 0)
        col.add_attribute(render_text, 'text', 1)

        view.append_column(col)
        view.show()

        # Create scrollbars around the view
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        scrolled.add(view)
        scrolled.show()

        return view, scrolled

GObject.type_register(TreeFileBrowser)

# End TreeFileBrowser

def main():	
	window = Gtk.Window()
	flcdexample = TreeFileBrowser('/home/mike')
	view = flcdexample.get_view()
	scrolled = flcdexample.get_scrolled()
	window.add(scrolled)
	window.set_size_request(150, 500)
	window.connect("delete_event", Gtk.main_quit)
	window.show_all()
	Gtk.main()

if __name__ == "__main__":	
	main()
