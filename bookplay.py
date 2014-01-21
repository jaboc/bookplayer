#!/usr/bin/env python2
 
import sys, os, thread, time
import pygtk, gtk, gobject
import pygst
import sqlite3 as lite

#pygst.require("0.10")
import gst
 
myLibrary = "/home/damonj/Audiobooks"
con = lite.connect('bookplayer.db') 
 
class Book_Player:
 
 
	def __init__(self):
		self.fname=None
		window = gtk.Window(gtk.WINDOW_TOPLEVEL)
		window.set_title("Audio-Player")
		window.set_default_size(500, -1)
		#window.connect("destroy", gtk.main_quit, "WM destroy")
		window.connect("destroy", self.destroy)
		vbox = gtk.VBox()
		window.add(vbox)
		self.entry = gtk.Label()
		vbox.pack_start(self.entry, False, True)
		self.time_label = gtk.Label()
		self.time_label.set_text("00:00 / 00:00")
		vbox.pack_start(self.time_label, False, True)
 
		#ADD Hbox 1 and it's buttons
		hbox1 = gtk.HBox()
		vbox.add(hbox1)
		#the rewind button
		self.bbutton = gtk.Button("<10")
		self.bbutton.connect("clicked", self.rewind_callback,10)
		hbox1.add(self.bbutton)
		#the play button
		self.sbutton = gtk.Button("Start")
		self.sbutton.connect("clicked", self.start_stop)
		self.sbutton.set_tooltip_text("Click me to Play or Stop")
		hbox1.add(self.sbutton)
		#the fast forward button
		self.fbutton = gtk.Button("10>")
		self.fbutton.connect("clicked", self.forward_callback,10)
		hbox1.add(self.fbutton)
 
		#ADD Hbox 2 and it's buttons
		hbox2 = gtk.HBox()
		vbox.add(hbox2)
		#the rewind button
		self.fbbutton = gtk.Button("<60")
		self.fbbutton.connect("clicked", self.rewind_callback,60)
		hbox2.add(self.fbbutton)
		#the file select button
		self.file_button = gtk.Button("File")
		self.file_button.connect("clicked", self.select_file)
		self.file_button.connect("clicked", self.start_stop)
		hbox2.add(self.file_button)
		#the fast forward button
		self.ffbutton = gtk.Button("60>")
		self.ffbutton.connect("clicked",self.forward_callback,60)
 
		hbox2.add(self.ffbutton)

		#ADD Hbox 2 and it's buttons
		hbox3 = gtk.HBox()
		vbox.add(hbox3)
		#add bookmark button
		self.bmbutton = gtk.Button("Add Bookmark")
		self.bmbutton.connect("clicked", self.save_bookmark)
		hbox3.add(self.bmbutton)
		#add load bookmark button
		self.lbmbutton = gtk.Button("Load Bookmark")
		self.lbmbutton.connect("clicked", self.save_bookmark)
		hbox3.add(self.lbmbutton)		
		#add about button
		self.abbutton = gtk.Button("About")
		self.abbutton.connect("clicked", self.about_clicked)
		hbox3.add(self.abbutton)		
		
		try:
			window.set_icon_from_file("book.png")
		except Exception, e:
			print e.message
			sys.exit(1)
		
		window.show_all()
 
		self.player = gst.element_factory_make("playbin2", "player")
		bus = self.player.get_bus()
		bus.add_signal_watch()
		bus.connect("message", self.on_message)
 
 
	def select_file(self, w):
		dialog = gtk.FileChooserDialog("Open..",None,gtk.FILE_CHOOSER_ACTION_OPEN,(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN, gtk.RESPONSE_OK))
		dialog.set_default_response(gtk.RESPONSE_OK)
		dialog.set_current_folder(myLibrary)
		filter = gtk.FileFilter()
		filter.set_name("All files")
		filter.add_pattern("*")
		dialog.add_filter(filter)
		response = dialog.run()
		if response == gtk.RESPONSE_OK:
     			print dialog.get_filename(), 'selected'
			self.fname = dialog.get_filename()
			self.entry.set_label(os.path.basename(self.fname))
		elif response == gtk.RESPONSE_CANCEL:
     			print 'Closed, no files selected'
		dialog.destroy()
 
	def about_clicked(self, widget):
		about = gtk.AboutDialog()
		about.set_program_name("bookplayer")
		about.set_version("0.1")
		about.set_comments("Bookplayer is a resuming audiobook player")
		about.set_website("http://github.com/jaboc")
		about.set_logo(gtk.gdk.pixbuf_new_from_file("book.png"))
		about.run()
		about.destroy()
 
	def start_stop(self, w):
		if self.sbutton.get_label() == "Start":
			print self.fname
			if self.fname == None:
				print "ok"
				self.select_file(w)
 
			if os.path.isfile(self.fname):
				self.sbutton.set_label("Stop")
				self.player.set_property("uri", "file://" + self.fname)
				self.player.set_state(gst.STATE_PLAYING)
				self.play_thread_id = thread.start_new_thread(self.play_thread, ())
				self.get_sqlplace()
 
		else:
			self.play_thread_id = None
			self.save_sqlplace()
			self.player.set_state(gst.STATE_NULL)
			self.sbutton.set_label("Start")
			self.time_label.set_text("00:00 / 00:00")
 
 
	def on_message(self, bus, message):
		t = message.type
		if t == gst.MESSAGE_EOS:
			self.player.set_state(gst.STATE_NULL)
			self.sbutton.set_label("Start")
			print "End of stream"
		elif t == gst.MESSAGE_ERROR:
			self.player.set_state(gst.STATE_NULL)
			err, debug = message.parse_error()
			print "Error: %s" % err, debug
			self.button.set_label("Start")
 
 
	def rewind_callback(self, w, seconds):
		pos_int = self.player.query_position(gst.FORMAT_TIME, None)[0]
		seek_ns = pos_int - (seconds * 1000000000)
		self.player.seek_simple(gst.FORMAT_TIME, gst.SEEK_FLAG_FLUSH, seek_ns)
 
 
	def forward_callback(self, w, seconds):
		pos_int = self.player.query_position(gst.FORMAT_TIME, None)[0]
		seek_ns = pos_int + (seconds * 1000000000)
		self.player.seek_simple(gst.FORMAT_TIME, gst.SEEK_FLAG_FLUSH, seek_ns)
 
	def convert_ns(self, t):
		s,ns = divmod(t, 1000000000)
		m,s = divmod(s, 60)
 
		if m < 60:
			return "%02i:%02i" %(m,s)
		else:
			h,m = divmod(m, 60)
			return "%i:%02i:%02i" %(h,m,s)
 
	def play_thread(self):
		play_thread_id = self.play_thread_id
		gtk.gdk.threads_enter()
		self.time_label.set_text("00:00 / 00:00")
		gtk.gdk.threads_leave()
 
		while play_thread_id == self.play_thread_id:
			try:
				time.sleep(0.2)
				dur_int = self.player.query_duration(gst.FORMAT_TIME, None)[0]
				if dur_int == -1:
					continue
				dur_str = self.convert_ns(dur_int)
				gtk.gdk.threads_enter()
				self.time_label.set_text("00:00 / " + dur_str)
				gtk.gdk.threads_leave()
				break
			except:
				pass
 
		time.sleep(0.2)
		while play_thread_id == self.play_thread_id:
			pos_int = self.player.query_position(gst.FORMAT_TIME, None)[0]
			pos_str = self.convert_ns(pos_int)
			if play_thread_id == self.play_thread_id:
				gtk.gdk.threads_enter()
				self.time_label.set_text(pos_str + " / " + dur_str)
				gtk.gdk.threads_leave()
			time.sleep(1)
 
	def save_sqlplace(self):
		if self.sbutton.get_label() == "Start":
			print "Nothing Playing"
		else:
			with con:    
				print ("Saving Listening Location") 
				my_place = self.player.query_position(gst.FORMAT_TIME, None)[0]
				filename= os.path.basename(self.fname)
				cur = con.cursor() 
				cur.execute("SELECT count(place) FROM lastplay WHERE file =?", (filename,)) 
				row = cur.fetchone()
				print "SQL Results : ", row[0]
				if row[0] == 0:
					print "Inserting"
					cur.execute("insert INTO lastplay VALUES(?,?)", (filename,my_place)) 
				else:
					print "Updating"
					cur.execute("UPDATE lastplay SET place=? WHERE file =?", (my_place,filename))
				
	def save_bookmark(self, data=None):
		if self.sbutton.get_label() == "Start":
			print "Nothing Playing"
		else:
			with con:    
				print ("Saving bookmark") 
				my_place = self.player.query_position(gst.FORMAT_TIME, None)[0]
				filename= os.path.basename(self.fname)
				cur = con.cursor() 
				cur.execute("INSERT INTO bookmarks VALUES(?,?)", (filename,my_place)) 
				
				
				
 
	def get_sqlplace(self):
		with con:    
			filename= os.path.basename(self.fname)
			cur = con.cursor() 
			cur.execute("SELECT count(place) FROM lastplay WHERE file =?", (filename,))   
			row = cur.fetchone()
			print "SQL Results : ", row[0]
			if row[0] == 1:
				cur.execute("SELECT place FROM lastplay WHERE file =?", (filename,))
				row = cur.fetchone()
				seek_ns = int(row[0])
				print "Seeking to ",seek_ns
				time.sleep(0.1)
				self.player.seek_simple(gst.FORMAT_TIME, gst.SEEK_FLAG_FLUSH, seek_ns)
			else:
				print "No saved location"

	def destroy(self, widget, data=None):
		self.save_sqlplace()
		gtk.main_quit('WM destroy')
		

	
#Main        
Book_Player()
gtk.gdk.threads_init()
gtk.main()
 
print "quitter"
