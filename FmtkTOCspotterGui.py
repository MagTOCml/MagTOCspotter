# -*- coding: utf-8 -*-

###########################################################################
# Python code generated with wxFormBuilder (version 3.10.0-4761b0c)
# http://www.wxformbuilder.org/
#
# PLEASE DO *NOT* EDIT THIS FILE!
###########################################################################

import wx
# import wx.xrc
from wx import Frame

ID_PREVPG = 1000
ID_NEXTPG = 1001


###########################################################################
# Class FmtkTOCspotterGui
###########################################################################
class FmtkTOCspotterGui(Frame):

    def __init__(self, parent):
        Frame.__init__(self, parent, id=wx.ID_ANY, title=u"MagTOCml TOCspotter",
                       pos=wx.DefaultPosition, size=wx.Size(760, 800),
                       style=wx.DEFAULT_FRAME_STYLE)

        self.SetSizeHints(wx.Size(760, 800), wx.DefaultSize)

        self.frame_menubar = wx.MenuBar(0)
        self.m_menu1 = wx.Menu()
        self.m_menuItem1 = wx.MenuItem(self.m_menu1, wx.ID_ANY,
                                       u"Update CSV data...", wx.EmptyString,
                                       wx.ITEM_NORMAL)
        self.m_menu1.Append(self.m_menuItem1)

        self.m_menuItem2 = wx.MenuItem(self.m_menu1, wx.ID_ANY, u"Settings...",
                                       wx.EmptyString, wx.ITEM_NORMAL)
        self.m_menu1.Append(self.m_menuItem2)

        self.m_menuItem3 = wx.MenuItem(self.m_menu1, wx.ID_ANY, u"Quit",
                                       wx.EmptyString, wx.ITEM_NORMAL)
        self.m_menu1.Append(self.m_menuItem3)

        self.frame_menubar.Append(self.m_menu1, u"File")

        self.SetMenuBar(self.frame_menubar)

        self.frame_statusbar = self.CreateStatusBar(2, wx.STB_SIZEGRIP,
                                                    wx.ID_ANY)
        b_sizer1 = wx.BoxSizer(wx.VERTICAL)

        self.main_panel = wx.Panel(self, wx.ID_ANY, wx.DefaultPosition,
                                   wx.DefaultSize, 0)
        b_sizer2 = wx.BoxSizer(wx.HORIZONTAL)

        self.widgetbar = wx.Panel(self.main_panel, wx.ID_ANY,
                                  wx.DefaultPosition, wx.Size(-1, -1),
                                  wx.BORDER_SIMPLE)
        self.widgetbar.SetMaxSize(wx.Size(210, -1))

        b_sizer3 = wx.BoxSizer(wx.VERTICAL)

        sb_sizer1 = wx.StaticBoxSizer(
            wx.StaticBox(self.widgetbar, wx.ID_ANY, u"Magazine"), wx.VERTICAL)

        b_sizer8 = wx.BoxSizer(wx.HORIZONTAL)

        self.more_pgs = wx.Button(sb_sizer1.GetStaticBox(), wx.ID_ANY,
                                  u"More pgs", wx.DefaultPosition,
                                  wx.DefaultSize, 0)
        self.more_pgs.SetToolTip(u"More pages for this issue...")

        b_sizer8.Add(self.more_pgs, 0, wx.ALL, 5)

        self.more_issues = wx.Button(sb_sizer1.GetStaticBox(), wx.ID_ANY,
                                     u"Next batch", wx.DefaultPosition,
                                     wx.DefaultSize, 0)
        b_sizer8.Add(self.more_issues, 0, wx.ALL, 5)

        sb_sizer1.Add(b_sizer8, 1, wx.ALIGN_CENTER_HORIZONTAL | wx.BOTTOM, 3)

        current_issue_choices = [u"'Next batch' to begin..."]
        self.current_issue = wx.Choice(sb_sizer1.GetStaticBox(), wx.ID_ANY,
                                       wx.DefaultPosition, wx.DefaultSize,
                                       current_issue_choices, 0)
        self.current_issue.SetSelection(0)
        sb_sizer1.Add(self.current_issue, 0, wx.EXPAND, 0)

        b_sizer4 = wx.BoxSizer(wx.HORIZONTAL)

        self.prev_issue = wx.Button(sb_sizer1.GetStaticBox(), wx.ID_ANY,
                                    u"Prev", wx.DefaultPosition, wx.DefaultSize,
                                    0)

        self.prev_issue.SetDefault()
        self.prev_issue.SetAuthNeeded()
        b_sizer4.Add(self.prev_issue, 0, wx.ALL, 5)

        self.next_issue = wx.Button(sb_sizer1.GetStaticBox(), wx.ID_ANY,
                                    u"Next", wx.DefaultPosition, wx.DefaultSize,
                                    0)

        self.next_issue.SetDefault()
        self.next_issue.SetAuthNeeded()
        b_sizer4.Add(self.next_issue, 0, wx.ALL, 5)

        sb_sizer1.Add(b_sizer4, 1, wx.ALIGN_CENTER_HORIZONTAL | wx.TOP, 3)

        b_sizer3.Add(sb_sizer1, 0, wx.ALIGN_CENTER_HORIZONTAL, 0)

        sb_sizer2 = wx.StaticBoxSizer(
            wx.StaticBox(self.widgetbar, wx.ID_ANY, u"Page"), wx.VERTICAL)

        b_sizer5 = wx.BoxSizer(wx.HORIZONTAL)

        self.prev_pg = wx.Button(sb_sizer2.GetStaticBox(), ID_PREVPG, u"Prev",
                                 wx.DefaultPosition, wx.DefaultSize, 0)

        self.prev_pg.SetDefault()
        self.prev_pg.SetAuthNeeded()
        b_sizer5.Add(self.prev_pg, 0, wx.ALL, 5)

        self.next_pg = wx.Button(sb_sizer2.GetStaticBox(), ID_NEXTPG, u"Next",
                                 wx.DefaultPosition, wx.DefaultSize, 0)

        self.next_pg.SetDefault()
        self.next_pg.SetAuthNeeded()
        b_sizer5.Add(self.next_pg, 0, wx.ALL, 5)

        sb_sizer2.Add(b_sizer5, 1, wx.ALIGN_CENTER_HORIZONTAL, 0)

        b_sizer6 = wx.BoxSizer(wx.HORIZONTAL)

        self.toc_spotted = wx.Button(sb_sizer2.GetStaticBox(), wx.ID_ANY,
                                     u"TOC it!", wx.DefaultPosition,
                                     wx.DefaultSize, 0)

        self.toc_spotted.SetDefault()
        self.toc_spotted.SetAuthNeeded()
        b_sizer6.Add(self.toc_spotted, 0, wx.ALL, 5)

        self.toc_not = wx.Button(sb_sizer2.GetStaticBox(), wx.ID_ANY, u"UnTOC",
                                 wx.DefaultPosition, wx.DefaultSize, 0)

        self.toc_not.SetDefault()
        self.toc_not.SetAuthNeeded()
        self.toc_not.Enable(False)

        b_sizer6.Add(self.toc_not, 0, wx.ALL, 5)

        sb_sizer2.Add(b_sizer6, 0, wx.ALIGN_CENTER_HORIZONTAL, 0)

        b_sizer3.Add(sb_sizer2, 0, 0, 0)

        self.widgetbar.SetSizer(b_sizer3)
        self.widgetbar.Layout()
        b_sizer3.Fit(self.widgetbar)
        b_sizer2.Add(self.widgetbar, 0, wx.RIGHT, 0)

        self.page_img = wx.Panel(self.main_panel, wx.ID_ANY, wx.DefaultPosition,
                                 wx.Size(-1, -1), wx.BORDER_SIMPLE)
        b_sizer7 = wx.BoxSizer(wx.HORIZONTAL)

        self.leaf_img = wx.StaticBitmap(self.page_img, wx.ID_ANY, wx.NullBitmap,
                                        wx.DefaultPosition, wx.DefaultSize, 0)
        b_sizer7.Add(self.leaf_img, 1, wx.ALL | wx.EXPAND, 0)

        self.page_img.SetSizer(b_sizer7)
        self.page_img.Layout()
        b_sizer7.Fit(self.page_img)
        b_sizer2.Add(self.page_img, 1,
                     wx.ALIGN_LEFT | wx.ALIGN_TOP | wx.ALL | wx.EXPAND, 1)

        self.main_panel.SetSizer(b_sizer2)
        self.main_panel.Layout()
        b_sizer2.Fit(self.main_panel)
        b_sizer1.Add(self.main_panel, 1, wx.EXPAND | wx.ALL, 5)

        self.SetSizer(b_sizer1)
        self.Layout()

        # Connect Events
        self.Bind(wx.EVT_MENU, self.evt_update_csv_data,
                  id=self.m_menuItem1.GetId())
        self.Bind(wx.EVT_MENU, self.evt_edit_settings,
                  id=self.m_menuItem2.GetId())
        self.Bind(wx.EVT_MENU, self.evt_quit_app, id=self.m_menuItem3.GetId())
        self.main_panel.Bind(wx.EVT_LEFT_DOWN, self.evt_set_best_focus)
        self.more_pgs.Bind(wx.EVT_BUTTON, self.evt_more_pgs)
        self.more_pgs.Bind(wx.EVT_KEY_DOWN, self.evt_more_pgs)
        self.more_issues.Bind(wx.EVT_BUTTON, self.evt_next_batch)
        self.more_issues.Bind(wx.EVT_KEY_DOWN, self.evt_next_batch)
        self.current_issue.Bind(wx.EVT_CHOICE, self.evt_current_issue_changed)
        self.current_issue.Bind(
            wx.EVT_KEY_DOWN, self.evt_current_issue_changed)
        self.prev_issue.Bind(wx.EVT_BUTTON, self.evt_prev_issue)
        self.prev_issue.Bind(wx.EVT_KEY_DOWN, self.evt_prev_issue)
        self.next_issue.Bind(wx.EVT_BUTTON, self.evt_next_issue)
        self.next_issue.Bind(wx.EVT_KEY_DOWN, self.evt_next_issue)
        self.prev_pg.Bind(wx.EVT_BUTTON, self.evt_prev_pg)
        self.prev_pg.Bind(wx.EVT_KEY_DOWN, self.evt_prev_pg)
        self.next_pg.Bind(wx.EVT_BUTTON, self.evt_next_pg)
        self.next_pg.Bind(wx.EVT_KEY_DOWN, self.evt_next_pg)
        self.toc_spotted.Bind(wx.EVT_BUTTON, self.evt_toc_spotted)
        self.toc_spotted.Bind(wx.EVT_KEY_DOWN, self.evt_toc_spotted)
        self.toc_not.Bind(wx.EVT_BUTTON, self.evt_untoc_spotted)
        self.toc_not.Bind(wx.EVT_KEY_DOWN, self.evt_untoc_spotted)

    # def __del__(self):
    #     pass

    # Virtual event handlers, override them in your derived class
    def evt_update_csv_data(self, event):
        event.Skip()

    def evt_edit_settings(self, event):
        event.Skip()

    def evt_quit_app(self, event):
        event.Skip()

    def evt_set_best_focus(self, event):
        event.Skip()

    def evt_more_pgs(self, event):
        event.Skip()

    def evt_next_batch(self, event):
        event.Skip()

    def evt_current_issue_changed(self, event):
        event.Skip()

    def evt_prev_issue(self, event):
        event.Skip()

    def evt_next_issue(self, event):
        event.Skip()

    def evt_prev_pg(self, event):
        event.Skip()

    def evt_next_pg(self, event):
        event.Skip()

    def evt_toc_spotted(self, event):
        event.Skip()

    def evt_untoc_spotted(self, event):
        event.Skip()
