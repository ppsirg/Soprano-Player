#!/usr/bin/env python

import os, stat, time
from gi.repository import Gtk, GdkPixbuf, Gdk
from os.path import splitext

class FileBrowser:
    column_names = ['Name', 'Size', 'Mode', 'Last Changed']    
 
    def __init__(self, dname = None):
	self.userstartpath = dname
 
        try: listmodel = self.make_list(dname)
	except: listmodel = self.make_list(os.path.expanduser('~'))
 
        # create the TreeView
        self.treeview = Gtk.TreeView()

        # create the TreeViewColumns to display the data
        self.tvcolumn = [None] * len(self.column_names)
        cellpb = Gtk.CellRendererPixbuf()
	cellpb.set_fixed_size(18,18)
        self.tvcolumn[0] = Gtk.TreeViewColumn(self.column_names[0], None)
        self.tvcolumn[0].pack_start(cellpb, False)
        self.tvcolumn[0].set_cell_data_func(cellpb, self.file_pixbuf)
        cell = Gtk.CellRendererText()
	cell.set_fixed_size(100,18)
        self.tvcolumn[0].pack_start(cell, False)
        self.tvcolumn[0].set_cell_data_func(cell, self.file_name)
        self.treeview.append_column(self.tvcolumn[0])

        self.treeview.connect('row-activated', self.open_file)
        self.scrolledwindow = Gtk.ScrolledWindow()
        self.scrolledwindow.add(self.treeview)
        self.treeview.set_model(listmodel)
	self.treeview.set_headers_visible(False)
 
	#list of file extensions to be showed
	self.fileFormats = {'.mp3','.ogg','.oga','.wma','.flac','.m4a','.mp4'}

        icon_theme = Gtk.IconTheme.get_default()
        try:
		self.folderpb = icon_theme.load_icon("gnome-fs-directory", 16, 0)
        except:
		folderxpm = 'folder.png'
		self.folderpb = GdkPixbuf.Pixbuf.new_from_file(folderxpm)
	icon_theme = None

	filexpm = 'file-icon.png'
	self.filepb = GdkPixbuf.Pixbuf.new_from_file(filexpm)

        return

    def get_sw(self):
	return self.scrolledwindow

    def make_list(self, dname=None):
        if not dname:
            self.dirname = os.path.expanduser('~')
        else:
            self.dirname = os.path.abspath(dname)
        files = [f for f in os.listdir(self.dirname) if f[0] <> '.']
        files.sort()
	if self.dirname != self.userstartpath:
        	files = ['..'] + files
        listmodel = Gtk.ListStore(object)
	temparray = []
        for f in files:
		if os.path.isdir(os.path.join(self.dirname + '/' + f)):	#folders
			listmodel.append([f])
		elif os.path.isfile(os.path.join(self.dirname + '/' + f)): #files
			if splitext(f.lower())[1] in self.fileFormats: #only certain filextensions
				temparray.append(f)			#stick in an array and add after the folders
	for f in temparray:
		listmodel.append([f])
        return listmodel

    def getDirContents(directory):
	directories = []
        mediaFiles  = []

	for (file, path) in listDir(directory, False):
		if os.path.isdir(path):
			directories.append(file)
		elif os.path.isfile(path):		
		        if splitext(file.lower())[1] in fileFormats:
				mediaFiles.append(file)
	return (directories, mediaFiles)


    def open_file(self, treeview, path, column):
        model = treeview.get_model()
        iter = model.get_iter(path)
        filename = os.path.join(self.dirname, model.get_value(iter, 0))
        filestat = os.stat(filename)
        if stat.S_ISDIR(filestat.st_mode):
            new_model = self.make_list(filename)
            treeview.set_model(new_model)
        return

    def file_pixbuf(self, column, cell, model, iter, unused):
        filename = os.path.join(self.dirname, model.get_value(iter, 0))
        filestat = os.stat(filename)
        if stat.S_ISDIR(filestat.st_mode):
            pb = self.folderpb
        else:
            pb = self.filepb
        cell.set_property('pixbuf', pb)
        return

    def file_name(self, column, cell, model, iter, unused):
        cell.set_property('text', model.get_value(iter, 0))
        return


##################
#Test Stuff add to random window
##################    

#def main():	
#	window = Gtk.Window()
#	flcdexample = FileBrowser('/media/Media')
#	window.add(flcdexample.get_sw())
#	window.set_size_request(150, 500)
#	window.connect("delete_event", Gtk.main_quit)
#	window.show_all()
#	print(flcdexample.get_sw())
#	Gtk.main()

#if __name__ == "__main__":	
#	main()
