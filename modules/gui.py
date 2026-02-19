import wx
import os
import threading
import wx.lib.newevent
from modules.search_engine import search_youtube
from modules.player import play_video
from modules.downloader import download_media

# Define a custom event for progress updates using the modern way
DownloadEvent, EVT_DOWNLOAD_UPDATE = wx.lib.newevent.NewEvent()

class TeTubeFrame(wx.Frame):
    def __init__(self):
        super().__init__(parent=None, title="Te_Tube - YouTube Search & Download", size=(800, 600))
        
        self.results = []
        self.init_ui()
        self.Centre()
        
        # Use CHAR_HOOK for global hotkeys like Enter
        self.Bind(wx.EVT_CHAR_HOOK, self.on_key_down)

    def set_accessible_name(self, control, name):
        """Safely sets the accessible name for a control."""
        control.SetName(name)
        acc = control.GetAccessible()
        if acc:
            acc.SetName(name)

    def init_ui(self):
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        # Tab control
        self.notebook = wx.Notebook(panel)
        self.search_tab = wx.Panel(self.notebook)
        self.notebook.AddPage(self.search_tab, "Search")

        self.setup_search_tab()

        vbox.Add(self.notebook, 1, wx.EXPAND | wx.ALL, 5)
        panel.SetSizer(vbox)

    def setup_search_tab(self):
        vbox = wx.BoxSizer(wx.VERTICAL)

        # Search box
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        search_label = wx.StaticText(self.search_tab, label="Search Query:")
        self.search_input = wx.TextCtrl(self.search_tab, style=wx.TE_PROCESS_ENTER)
        self.search_input.SetHint("Enter keywords here...")
        self.search_input.Bind(wx.EVT_TEXT_ENTER, self.on_search)
        
        # Accessibility for search input
        self.set_accessible_name(self.search_input, "Search YouTube")
        
        search_button = wx.Button(self.search_tab, label="Search")
        search_button.Bind(wx.EVT_BUTTON, self.on_search)
        self.set_accessible_name(search_button, "Search")

        hbox1.Add(search_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        hbox1.Add(self.search_input, 1, wx.EXPAND | wx.ALL, 5)
        hbox1.Add(search_button, 0, wx.ALL, 5)
        vbox.Add(hbox1, 0, wx.EXPAND | wx.ALL, 5)

        # Result list
        self.result_list = wx.ListBox(self.search_tab, style=wx.LB_SINGLE)
        self.result_list.Bind(wx.EVT_LISTBOX_DCLICK, self.on_play)
        self.result_list.Bind(wx.EVT_CONTEXT_MENU, self.on_context_menu)
        
        # Accessibility for list box
        self.set_accessible_name(self.result_list, "Search Results")

        vbox.Add(self.result_list, 1, wx.EXPAND | wx.ALL, 5)
        self.search_tab.SetSizer(vbox)

    def on_search(self, event):
        query = self.search_input.GetValue()
        if not query:
            return

        # Show status
        self.SetTitle(f"Searching for '{query}'...")
        
        # Clear previous results
        self.result_list.Clear()
        try:
            self.results = search_youtube(query)
            
            for item in self.results:
                display_text = f"{item['title']} [{item['duration']}] - {item['uploader']}"
                self.result_list.Append(display_text)
        except Exception as e:
            wx.MessageBox(f"Error during search: {e}", "Search Error", wx.OK | wx.ICON_ERROR)
        
        self.SetTitle("Te_Tube - YouTube Search & Download")
        if self.result_list.GetCount() > 0:
            self.result_list.SetSelection(0)
            self.result_list.SetFocus()

    def on_play(self, event):
        selection = self.result_list.GetSelection()
        if selection != wx.NOT_FOUND:
            video_url = self.results[selection]['url']
            try:
                play_video(video_url)
            except Exception as e:
                wx.MessageBox(f"Error playing video: {e}", "Playback Error", wx.OK | wx.ICON_ERROR)

    def on_key_down(self, event):
        keycode = event.GetKeyCode()
        if keycode in [wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER]:
            # Trigger play only if search box is NOT focused
            # OR if focus is in result_list
            focused = wx.Window.FindFocus()
            if focused != self.search_input:
                self.on_play(None)
                return # Don't Skip() if we handle it
        
        event.Skip()

    def on_copy_link(self, event):
        selection = self.result_list.GetSelection()
        if selection != wx.NOT_FOUND:
            video_url = self.results[selection]['url']
            if wx.TheClipboard.Open():
                wx.TheClipboard.SetData(wx.TextDataObject(video_url))
                wx.TheClipboard.Close()
                wx.MessageBox("Link copied to clipboard!", "Success", wx.OK | wx.ICON_INFORMATION)

    def on_context_menu(self, event):
        selection = self.result_list.GetSelection()
        if selection == wx.NOT_FOUND:
            return

        menu = wx.Menu()
        play_item = menu.Append(wx.ID_ANY, "&Play\tEnter")
        self.Bind(wx.EVT_MENU, self.on_play, play_item)

        copy_item = menu.Append(wx.ID_ANY, "&Copy Link")
        self.Bind(wx.EVT_MENU, self.on_copy_link, copy_item)

        download_menu = wx.Menu()
        formats = [("MP4 Video", "mp4"), ("M4A Audio", "m4a"), ("MP3 Audio", "mp3"), ("WAV Audio", "wav")]
        
        for label, fmt in formats:
            item = download_menu.Append(wx.ID_ANY, label)
            self.Bind(wx.EVT_MENU, lambda evt, f=fmt: self.on_download(f), item)
            
        menu.AppendSubMenu(download_menu, "&Download")
        
        self.PopupMenu(menu)
        menu.Destroy()

    def on_download(self, fmt):
        selection = self.result_list.GetSelection()
        if selection != wx.NOT_FOUND:
            video_url = self.results[selection]['url']
            title = self.results[selection]['title']
            
            dialog = DownloadProgressDialog(self, title, video_url, fmt)
            dialog.Show()

class DownloadThread(threading.Thread):
    def __init__(self, win, url, fmt):
        super().__init__()
        self.win = win
        self.url = url
        self.fmt = fmt
        self.daemon = True

    def run(self):
        try:
            def callback(p):
                wx.PostEvent(self.win, DownloadEvent(**p))
            
            final_path = download_media(self.url, self.fmt, callback)
            wx.PostEvent(self.win, DownloadEvent(status='finished', path=final_path))
        except Exception as e:
            wx.PostEvent(self.win, DownloadEvent(status='error', error=str(e)))

class DownloadProgressDialog(wx.Dialog):
    def __init__(self, parent, title, url, fmt):
        super().__init__(parent, title="Downloading...", size=(400, 180))
        self.video_title = title
        self.last_percent = -1
        
        panel = wx.Panel(self)
        self.vbox = wx.BoxSizer(wx.VERTICAL)
        
        self.title_label = wx.StaticText(panel, label=f"Downloading: {title}")
        self.set_accessible_name(self.title_label, f"Downloading: {title}")
        
        self.gauge = wx.Gauge(panel, range=100, size=(350, 25))
        self.set_accessible_name(self.gauge, "Download progress")
        
        self.status_label = wx.StaticText(panel, label="Initializing...")
        self.set_accessible_name(self.status_label, "Status: Initializing")
        
        self.vbox.Add(self.title_label, 0, wx.ALL | wx.EXPAND, 10)
        self.vbox.Add(self.gauge, 0, wx.ALL | wx.EXPAND, 10)
        self.vbox.Add(self.status_label, 0, wx.ALL | wx.EXPAND, 10)
        
        panel.SetSizer(self.vbox)
        self.Centre()
        
        self.Bind(EVT_DOWNLOAD_UPDATE, self.on_update)
        
        self.thread = DownloadThread(self, url, fmt)
        self.thread.start()

    def set_accessible_name(self, control, name):
        """Safely sets the accessible name for a control."""
        control.SetName(name)
        acc = control.GetAccessible()
        if acc:
            acc.SetName(name)

    def on_update(self, event):
        status = event.status
        
        if status == 'downloading':
            percent = int(event.percent)
            if percent != self.last_percent:
                self.gauge.SetValue(percent)
                self.last_percent = percent
            
            # Clean up the status line (remove [download])
            clean_status = event.line.replace('[download]', '').strip()
            self.status_label.SetLabel(clean_status)
            # AVOID set_accessible_name on every tick as it's expensive and causes freeze
            
        elif status == 'finished':
            self.gauge.SetValue(100)
            self.status_label.SetLabel("Download Complete!")
            # Final accessibility update when finished is okay
            self.set_accessible_name(self.status_label, "Status: Download Complete")
            
            path = event.path or "Unknown location"
            wx.MessageBox(f"Download complete!\nFile saved at: {path}", "Success", wx.OK | wx.ICON_INFORMATION)
            self.Destroy()
            
        elif status == 'error':
            error_msg = event.error or "Unknown error"
            wx.MessageBox(f"Download failed: {error_msg}", "Error", wx.OK | wx.ICON_ERROR)
            self.Destroy()

def start_gui():
    app = wx.App()
    frame = TeTubeFrame()
    frame.Show()
    app.MainLoop()
