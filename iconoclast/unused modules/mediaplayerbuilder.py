from gi.repository import Gtk, GdkPixbuf, Gdk, Gio, GObject
import os
import gst
import random

from aboutbox import aboutBoxShow
from tagreading import TrackMetaData
from FileExplorer import FileBrowser
#from treefilebrowser import TreeFileBrowser

def widget_hide(widget, button):
    widget.hide()

class BuilderApp:
	def __init__(self):
		#Gstreamer Bits#
		self.player = gst.element_factory_make("playbin2", "player")
		fakesink = gst.element_factory_make("fakesink", "fakesink")
		self.player.set_property("video-sink", fakesink)
		self.player.connect('about-to-finish', self.play_next)
		self.repeat = False

		#timer to update the time labels and seek bar#
		self.timer = GObject.timeout_add(500, self.update_time_labels)

		#Window Creation
		self.builder = Gtk.Builder()
		filename = os.path.join('', 'MainWindow.glade')        

		self.builder.add_from_file(filename)
		self.builder.connect_signals(self)	

		self.window = self.builder.get_object('win-main')
		self.window.set_default_size(900, 550)
		self.window.connect('destroy', lambda x: Gtk.main_quit())
		self.window.show_all()
		#register drag and drop
	
		self.treeview = self.builder.get_object('treeview1')
		self.treeview.drag_dest_set(0, [], 0)
		self.treeview.connect('drag_motion', self.motion_cb)
		self.treeview.connect('drag_drop', self.drop_cb)
		self.treeview.connect('drag_data_received', self.got_data_cb)

		#Quit, About Menus
		self.menuaqt = self.builder.get_object('menu-quit')
		self.menuaqt.connect('activate', self.quit_activate)

		self.menuabt = self.builder.get_object('menu-about')
		self.menuabt.connect('activate', self.about_activate)

		#View Menu#
		self.menuvfull = self.builder.get_object('menu-mode-full')
		self.menuvfull.connect('activate', self.to_full_mode)

		self.menuvlean = self.builder.get_object('menu-mode-lean')
		self.menuvlean.connect('activate', self.to_lean_mode)

		self.menuvmini = self.builder.get_object('menu-mode-mini')
		self.menuvmini.connect('activate', self.to_mini_mode)

		self.menuvplist = self.builder.get_object('menu-mode-playlist')
		self.menuvplist.connect('activate', self.to_playlist_mode)

		#playing Toolbar
		self.toolnext = self.builder.get_object('btn-next')
		self.toolnext.connect('clicked', self.play_next)

		self.toolprev = self.builder.get_object('btn-previous')
		self.toolprev.connect('clicked', self.play_prev)

		self.toolstop = self.builder.get_object('btn-stop')
		self.toolstop.connect('clicked', self.stop_play)

		self.toolplay = self.builder.get_object('btn-play')
		self.toolplay.connect('clicked', self.play_pause)

		self.toolSeekBar = self.builder.get_object('scl-position')
		self.toolSeekBar.connect('change-value', self.seek)

		self.toolVolume = self.builder.get_object('btn-volume')
		self.toolVolume.connect('value-changed', self.change_volume)

		#bottom toolbar
		self.barclr = self.builder.get_object('btn-tracklistClear')
		self.barclr.connect('clicked', self.clear_liststore)

		self.barshfl = self.builder.get_object('btn-tracklistShuffle')
		self.barshfl.connect('clicked', self.shuffleliststore)

		self.barrpt = self.builder.get_object('btn-tracklistRepeat')
		self.barrpt.connect('toggled', self.setrepeat)

		#listview#
		self.listview = self.builder.get_object('treeview1')
		self.listview.connect('row-activated', self.on_activated)

		#listviewModel
		self.model = self.builder.get_object('liststore1')
		self.titleText = self.builder.get_object('lbl-trkTitle')
		self.infoText = self.builder.get_object('lbl-trkMisc')

		#notebook, Combobox and contents
		self.notebook = self.builder.get_object('notebook-explorer')		

		self.explorer = FileBrowser('/media/Media/Music')
		self.notebook.add(self.explorer.get_sw())

		#self.explorer2 = TreeFileBrowser('/media/Media/Music')
		#self.notebook.add(self.explorer2.get_scrolled())

		self.notebook.show_all()

		#preliminary combobox

		#folderpb = GdkPixbuf.Pixbuf.new_from_file('folder.png')

		#self.combobox = self.builder.get_object('combo-explorer')
		#self.combomodel = self.builder.get_object('combostore')

		#self.cellrenderera = Gtk.CellRendererText()
		#self.combobox.pack_end(self.cellrenderera, False)
		#self.combobox.add_attribute(self.cellrenderera, 'text', 1) 
		#self.combomodel.append(['folder', 'Music'])

		#self.combobox.set_active(1)

	#Math Funcs and Other Handlers#

	def update_time_labels(self):
		playstate = self.player.get_state()[1]
		if (playstate == gst.STATE_PLAYING):
			self.seek_scale_set(None)
			self.sclSeek = self.builder.get_object('scl-position')
			self.position = self.player.query_position(gst.FORMAT_TIME, None)[0]
			self.sclSeek.set_value(self.position)

			self.currTrackPosText = self.convert_ns(self.position)
			self.timeLabel = self.builder.get_object('lbl-elapsedTime')
			self.timeLabel.set_text(self.currTrackPosText)
		return True
		
	def convert_ns(self, t):
		# This method was taken from a web tutorial by Sam Mason.
		s,ns = divmod(t, 1000000000)
		m,s = divmod(s, 60)

		if m < 60:
			return "%02i:%02i" %(m,s)
		else:
			h,m = divmod(m, 60)
			return "%i:%02i:%02i" %(h,m,s)

	def about_activate(self, action):
		aboutBoxShow(self.window)

	def quit_activate(self, action):
        	Gtk.main_quit()

	#Listbox Handlers
	def add_row(self, action):
		action = action.replace('%20',' ')
		getmesumdatabruv = TrackMetaData()
		x = getmesumdatabruv.getTrackType(action)		
		#print x
		if x != False:
			x.insert(0, None)
			self.model.append(x)

	def on_activated(self, widget, row, col):        
		model = widget.get_model()

		text = model[row][7]
		text = "file://" + text 
		self.playitem(text)

		try: self.titleText.set_text(model[row][2])
		except: self.titleText.set_text('No Artist')
		try: self.infoText.set_text(model[row][3])
		except: self.infoText.set_text('No Album')
		
		self.set_playmark(row)

	def clear_playmark(self):
		i = 0
		while i != len(self.model):
			self.model.set_value(self.model.get_iter(i), 0, '')
			i = i+1

	def set_playmark(self, row):
		self.clear_playmark()		
		try: self.model.set_value(row, 0, 'media-playback-start')
		except: self.model.set_value(self.model.get_iter(row), 0, 'media-playback-start')

	#Drag and Drop Handling
	def motion_cb(self, windowid, context, x, y, time):
		#windowid.drag_get_data(context, context.list_targets()[-1], time)
		return True

	def drop_cb(self, windowid, context, x, y, time):
		# Some data was dropped, get the data
		windowid.drag_get_data(context, context.list_targets()[-1], time)
		return True

	def got_data_cb(self, windowid, context, x, y, data, info, time):
		# Got data.
		tempArray = data.get_text().splitlines()
		for i in tempArray:
			i = i.replace('file://','')
			#print i
			self.add_row(i)
		context.finish(True, False, time)

	#View Mode Menu Handlers#
	def to_full_mode(self, unused):
		self.builder.get_object('pan-main').get_child1().show()
		self.builder.get_object('statusbar').show()
		self.builder.get_object('box-btn-tracklist').show()
		self.builder.get_object('scrolled-tracklist').show()
		self.window.resize(900, 550)

	def to_lean_mode(self, unused):
		self.to_full_mode(None)	
		self.builder.get_object('box-btn-tracklist').hide()

	def to_mini_mode(self, unused):
		self.to_full_mode(None)	
		self.builder.get_object('pan-main').get_child1().hide()
		self.builder.get_object('statusbar').hide()
		self.builder.get_object('box-btn-tracklist').hide()
		self.builder.get_object('scrolled-tracklist').hide()
		self.window.resize(600, 150)

	def to_playlist_mode(self, unused):
		self.to_full_mode(None)	
		self.window.resize(600, 550)
		self.builder.get_object('pan-main').get_child1().hide()

	#Bottom Toolbar Handlers#
	def clear_liststore(self, action):
		self.model.clear()

	def shuffleliststore(self, arg1):
		x = len(self.model)
		y = self.model.get_n_columns()
		temparray = []
		for i in range(0, x):
			temparray2 = []
			for j in range(0, y):
				temparray2.append(self.model[i][j])
			temparray.append(temparray2)
		self.model.clear()
		random.shuffle(temparray)
		for i in range(0, len(temparray)):
			self.model.append(temparray[i])

	def setrepeat(self, arg1):
		self.repeat = not(self.repeat)

	#Audio Control Widget Handlers#
	def change_volume(self, volume, unused):
		volume = self.builder.get_object('btn-volume').get_value()
		self.player.set_property('volume', volume)

	def seek_scale_set(self, unused):
		self.sclSeek = self.builder.get_object('scl-position')

		self.currTrackLength = (self.player.query_duration(gst.FORMAT_TIME, None)[0])
		self.sclSeek.set_range(0, self.currTrackLength)

		self.currTrackLengthText = self.convert_ns(self.currTrackLength)
		self.timeLabel = self.builder.get_object('lbl-remainingTime')
		self.timeLabel.set_text(self.currTrackLengthText)

	#Gstreamer Player Handlers#
	def play_pause(self, filepath):
		selected = self.builder.get_object('treeview-selection1')

		if selected.get_selected()[1] != None:
			modeliter = selected.get_selected()[1]
			self.set_playmark(modeliter)
		elif self.model.get_iter_first() != None:
			modeliter = self.model.get_iter_first()
			self.set_playmark(0)

		try: filepath = self.model.get_value(modeliter, 7)
		except: return

		toolplayimg = self.builder.get_object('image3')
		playstate = self.player.get_state()[1]
		if (playstate == gst.STATE_PLAYING):
			self.player.set_state(gst.STATE_PAUSED)

			toolplayimg.set_from_icon_name('media-playback-start', Gtk.IconSize.LARGE_TOOLBAR)			
		elif os.path.isfile(filepath):
			self.player.set_property("uri", "file://" + filepath)
			self.player.set_state(gst.STATE_PLAYING)

			getmesumdatabruv = TrackMetaData()
			x = getmesumdatabruv.getTrackType(filepath)

			try: self.titleText.set_text(x[1])
			except: self.titleText.set_text('No Artist')
			try: self.infoText.set_text(x[2])
			except: self.infoText.set_text('No Album')
			toolplayimg.set_from_icon_name('media-playback-pause', Gtk.IconSize.LARGE_TOOLBAR)

	def playitem(self, filepath):
		self.player.set_state(gst.STATE_NULL)
		self.player.set_property("uri", filepath)
		self.player.set_state(gst.STATE_PLAYING)

		toolplayimg = self.builder.get_object('image3')
		toolplayimg.set_from_icon_name('media-playback-pause', Gtk.IconSize.LARGE_TOOLBAR)	

	def stop_play(self, *args):
		self.player.set_state(gst.STATE_NULL)

		self.timeLabel = self.builder.get_object('lbl-remainingTime')
		self.timeLabel.set_text('')
		self.elapsedTimeLabel = self.builder.get_object('lbl-elapsedTime')
		self.elapsedTimeLabel.set_text('')

		self.titleText.set_text('Iconoclast Audio Player')
		self.infoText.set_text('...One Goal, Be Epic')
		self.clear_playmark()
		toolplayimg = self.builder.get_object('image3')
		toolplayimg.set_from_icon_name('media-playback-start', Gtk.IconSize.LARGE_TOOLBAR)

	def play_prev(self, unused):
		for x in range(1,len(self.model)):
			#if ("file://" + self.model[x][7]) == self.player.get_property("uri"):
			if self.model[x][0] == 'media-playback-start':
				self.stop_play()
				self.playitem("file://" + self.model[x-1][7])
				self.set_playmark(x-1)
				break

	def play_next(self, unused):
		for x in range(0,len(self.model)):
			if x == len(self.model)-1 and self.repeat == True:
				self.stop_play()
				self.playitem("file://" + self.model[0][7])
				self.set_playmark(0)
			if self.model[x][0] == 'media-playback-start' and x < len(self.model)-1:
				self.stop_play()
				self.playitem("file://" + self.model[x+1][7])
				self.set_playmark(x+1)
				break


	def seek(self, widget, test, where):
		self.player.seek_simple(gst.FORMAT_TIME, gst.SEEK_FLAG_FLUSH, where)
		self.update_time_labels()

	#Status Icon Handlers#

	def toggle_window(self, trayicon):
		if self.window.get_property("visible"):
			self.window.hide()
		else:
			self.window.show()

	def right_click_event(self, icon, button, time):
		self.menu = Gtk.Menu()

		about = Gtk.MenuItem()
		about.set_label("About")
		quit = Gtk.MenuItem()
		quit.set_label("Quit")
		
		about.connect("activate", self.about_activate)
		quit.connect("activate", self.quit_activate)
		
		self.menu.append(about)
		self.menu.append(quit)
		
		self.menu.show_all()

		def pos(menu, ignore, aicon):
			return (Gtk.StatusIcon.position_menu(menu, aicon))

		self.menu.popup(None, None, pos, icon, button, time)

def main(iconoclast=None):
	app = BuilderApp()

	myStatusIcon = Gtk.StatusIcon()
	myStatusIcon.set_from_file('decibel-tray.png')
	myStatusIcon.connect('activate', app.toggle_window)
	myStatusIcon.connect('popup-menu', app.right_click_event)

	if __name__ == '__main__':
		Gtk.main()

main()
