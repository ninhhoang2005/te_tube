import wx
import os
from modules.search_engine import search_youtube
from modules.player import play_video
from modules.downloader import download_media

class TeTubeFrame(wx.Frame):
    def __init__(self):
        super().__init__(parent=None, title="Te_Tube - YouTube Search & Download", size=(800, 600))
        
        self.results = []
        self.init_ui()
        self.Centre()

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
        self.result_list.Bind(wx.EVT_KEY_DOWN, self.on_key_down)
        
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
        if keycode == wx.WXK_RETURN:
            self.on_play(None)
        else:
            event.Skip()

    def on_context_menu(self, event):
        selection = self.result_list.GetSelection()
        if selection == wx.NOT_FOUND:
            return

        menu = wx.Menu()
        play_item = menu.Append(wx.ID_ANY, "&Play")
        self.Bind(wx.EVT_MENU, self.on_play, play_item)

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
            download_media(video_url, fmt)
            wx.MessageBox(f"Download started for: {self.results[selection]['title']}\nFormat: {fmt}\nCheck the 'download' folder.", "Download Started")

def start_gui():
    app = wx.App()
    frame = TeTubeFrame()
    frame.Show()
    app.MainLoop()
