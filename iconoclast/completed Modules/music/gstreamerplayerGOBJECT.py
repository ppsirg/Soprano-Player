import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject
#import gst
GObject.threads_init()
Gst.init(None)
#Arguements for time in Nanoseconds have changed position,
#for Gst 1.0 you must use self.player.query_duration(Gst.Format.TIME)[1]
#for Gst 0.10 you muse use self.player.query_duration(Gst.Format.TIME)[2]

class MusicPlayer(object):
	def __init__(self, enableVideo=False):
		self.player = Gst.ElementFactory.make("playbin", "player")
		fakesink = Gst.ElementFactory.make("fakesink", "fakesink")
		if not enableVideo:
			self.player.set_property("video-sink", fakesink)
		#self.loadeduri = None

	def change_volume(self, volume):		
		self.player.set_property('volume', volume)

	def set_track(self, filepath):
		#replace characters that Gstreamer doesnt like as a uri
		filepath = filepath.replace('%', '%25').replace('#', '%23')
		self.player.set_property("uri", filepath)
		#self.loadeduri = filepath# Gst introspection no longer allows get_property("uri") 

	def get_track(self):
		return self.player.get_property("current-uri")
		#return self.loadeduri

	def play_item(self):
		self.player.set_state(Gst.State.PLAYING)

	def pause_item(self):
		self.player.set_state(Gst.State.PAUSED)

	def stop_play(self):
		self.player.set_state(Gst.State.NULL)

	def seek(self, where):
		currtracklength = self.player.query_duration(Gst.Format.TIME)[1]
		self.player.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH, (currtracklength / 100)* where)

	def track_percent(self):
		if self.get_track()[:6] == 'mms://':
			return 0
		else:
			tracklength = self.player.query_duration(Gst.Format.TIME)[1]
			position = self.player.query_position(Gst.Format.TIME)[1]
			return ((float(position)/tracklength)*100)

	def get_tracklength(self):
		tracklength = self.player.query_duration(Gst.Format.TIME)[1]
		return self.convert_ns(tracklength)

	def get_trackposition(self):
		position = self.player.query_position(Gst.Format.TIME)[1]
		return self.convert_ns(position)

	def get_state(self):
		try: state = self.player.get_state(0)[1]
		except: state = Gst.State.NULL
		return state

	def get_player(self):
		return self.player

	def on_eos(self, function):
		bus = self.player.get_bus()
		bus.add_signal_watch()
		bus.connect("message::eos", function)

	def convert_ns(self, t):
		#convert nanoseconds to hours minutes and seconds
		s,ns = divmod(t, 1000000000)
		m,s = divmod(s, 60)

		if m < 60:
			return "%02i:%02i" %(m,s)
		else:
			h,m = divmod(m, 60)
			return "%i:%02i:%02i" %(h,m,s)


#debugging function
"""import time
def main():
	app = MusicPlayer(True)
	app.set_track("file:///media/Media/Music/Bob Dylan/Modern Times/06 - Workingman's Blues #2.ogg")
	app.change_volume(1.5)
	print(app.get_state())
	app.play_item()
	print(app.get_track())
	time.sleep(5)
	app.seek(25)
	time.sleep(5)
	app.pause_item()
	print(app.get_state())
	app.change_volume(3)
	time.sleep(1)
	app.play_item()
	time.sleep(5)
	app.stop_play()

main()"""
