#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
#
# Copyright 2021 Jim Salmons. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import threading
from configparser import ConfigParser
from pathlib import Path
from threading import Thread

import pandas as pd
import wx
# from urllib.request import Request, urlopen
# import urllib.parse
# from urllib.error import URLError, HTTPError
from PIL import Image  # , ImageDraw
from pubsub import pub

# import xmltodict as x2d
import FmtkLeafGrabber as lg
from FmtkTOCspotterGui import FmtkTOCspotterGui

Image.MAX_IMAGE_PIXELS = 1000000000


# Utility & dev one-offs likely not to survive...

# def get_pages_from_scandata(scandata_xml):
#     scandata = x2d.parse(scandata_xml)
#     page_elements = scandata['book']['pageData']['page']
#     return page_elements


# Get a dataframe of all compmags issues...
# df = pd.read_csv('tocdata/compmags_pubs.csv', header=0, index_col=False)
# print(df.head(3))
# print(df.tail(3))

# Grab a random issue...
# queue = df.sample(1)
# print(queue)


###########################################################################
# Class TOCspotterGui
###########################################################################
class TOCspotterGui(FmtkTOCspotterGui):
    def __init__(self, *args, **kwds):
        FmtkTOCspotterGui.__init__(self, *args, **kwds)
        self.frame_statusbar.SetStatusWidths([150, -1])
        self.frame_statusbar.SetStatusText("Ready", 0)
        self.app = None

    def __del__(self):
        self.app.__del__()

    def evt_quit_app(self, event):
        self.__del__()
        event.Skip()

    def evt_current_issue_changed(self, event):
        if event.ClassName == 'wxCommandEvent' or \
                (event.ClassName == 'wxKeyEvent' and
                 event.GetKeyCode() not in (wx.WXK_TAB, wx.WXK_SHIFT)):
            if event is not None:
                if self.current_issue.CurrentSelection == 0:
                    self.prev_issue.Disable()
                    self.next_issue.Enable()
                elif self.current_issue.CurrentSelection == \
                        self.current_issue.GetCount() - 1:
                    self.next_issue.Disable()
                    self.prev_issue.Enable()
                else:
                    self.prev_issue.Enable()
                    self.next_issue.Enable()
                self.app.leaf_num = 0
                self.prev_pg.Disable()
                self.next_pg.Enable()
                self.toc_spotted.Enable()
                self.show_page()
                # event.Skip()

    def evt_prev_issue(self, event):
        if event.ClassName == 'wxCommandEvent' or \
                (event.ClassName == 'wxKeyEvent' and
                 event.GetKeyCode() not in (wx.WXK_TAB, wx.WXK_SHIFT)):
            if self.current_issue.CurrentSelection > 0:
                self.current_issue.SetSelection(
                    self.current_issue.CurrentSelection - 1)
                self.next_issue.Enable()
                self.prev_issue.SetFocus()
            if self.current_issue.CurrentSelection == 0:
                self.prev_issue.Disable()
                self.next_issue.SetFocus()
            self.app.leaf_num = 0
            self.more_pgs.Disable()
            self.prev_pg.Disable()
            self.next_pg.Enable()
            self.app.check_toc()
            self.show_page()
            # event.Skip()

    def evt_next_issue(self, event):
        if event.ClassName == 'wxCommandEvent' or \
                (event.ClassName == 'wxKeyEvent' and
                 event.GetKeyCode() not in (wx.WXK_TAB, wx.WXK_SHIFT)):
            self.app.log_done_pub(self.current_issue.GetStringSelection())
            if self.current_issue.CurrentSelection < \
                    self.current_issue.GetCount() - 1:
                self.current_issue.SetSelection(
                    self.current_issue.CurrentSelection + 1)
                self.prev_issue.Enable()
                self.next_pg.SetFocus()
            if self.current_issue.CurrentSelection == \
                    self.current_issue.GetCount() - 1:
                self.next_issue.Disable()
                self.next_pg.SetFocus()
            if self.app.queue_size > int(
                    self.app.config['Persistent variables'][
                        'queue_size']):
                self.app.queue_size = int(
                    self.app.config['Persistent variables'][
                        'queue_size'])
            self.app.leaf_num = 0
            self.prev_pg.Disable()
            self.next_pg.Enable()
            self.more_pgs.Disable()
            self.toc_spotted.Enable()
            self.show_page()
            self.next_pg.SetFocus()
            # event.Skip()

    def evt_prev_pg(self, event):
        if event.ClassName == 'wxCommandEvent' or \
                (event.ClassName == 'wxKeyEvent' and
                 event.GetKeyCode() not in (wx.WXK_TAB, wx.WXK_SHIFT)):
            # If there is a prev leaf image, show it...
            prev_leaf = self.app.leaf_num - 1
            if prev_leaf >= 0:
                self.app.leaf_num -= 1
                self.show_page()
                self.next_pg.Enable()
                self.more_pgs.Disable()
                if self.app.leaf_num == 0:
                    self.prev_pg.Disable()
                    self.next_pg.SetFocus()
                else:
                    self.prev_pg.Enable()
            self.app.check_toc()
            # event.Skip()

    def evt_next_pg(self, event):
        if event.ClassName == 'wxCommandEvent' or \
                (event.ClassName == 'wxKeyEvent' and
                 event.GetKeyCode() not in (wx.WXK_TAB, wx.WXK_SHIFT)):
            # If there is a next leaf image, show it...
            next_leaf = self.app.leaf_num + 1
            # TODO: Check if leaf exists...
            if next_leaf <= self.app.queue_size - 1:
                self.app.leaf_num += 1
                self.show_page()
                self.prev_pg.Enable()
                if self.app.leaf_num == self.app.queue_size - 1:
                    self.next_pg.Disable()
                    self.more_pgs.Enable()
                    if self.next_issue.IsEnabled():
                        self.next_issue.SetFocus()
                    else:
                        self.more_issues.SetFocus()
                else:
                    self.next_pg.SetFocus()
            self.app.check_toc()
            # event.Skip()

    def evt_more_pgs(self, event):
        if event.ClassName == 'wxCommandEvent' or \
                (event.ClassName == 'wxKeyEvent' and
                 event.GetKeyCode() not in (wx.WXK_TAB, wx.WXK_SHIFT)):
            # Get 1 or more pages for the currently selected issue...
            self.app.get_more_pages(self.current_issue.GetStringSelection())
            event.Skip()

    def evt_next_batch(self, event):
        if event.ClassName == 'wxCommandEvent' or \
                (event.ClassName == 'wxKeyEvent' and
                 event.GetKeyCode() not in (wx.WXK_TAB, wx.WXK_SHIFT)):
            if self.app.queue_size > int(
                    self.app.config['Persistent variables'][
                        'queue_size']):
                self.app.queue_size = int(
                    self.app.config['Persistent variables'][
                        'queue_size'])
            self.queue_issues(event)
            self.app.check_toc()
            self.next_pg.SetFocus()
            # event.Skip()

    def evt_toc_spotted(self, event):
        """
        If self.save_toc_img is True, save the image. In all cases,
        remember/save the toc_spec.
        :param event: wx.Event
        :return: None
        """
        if event.ClassName == 'wxCommandEvent' or \
                (event.ClassName == 'wxKeyEvent' and
                 event.GetKeyCode() not in (wx.WXK_TAB, wx.WXK_SHIFT)):
            item_id = None
            leaf_num = None
            if self.app.save_toc_imgs:
                item_id, leaf_num = self.app.save_toc_image()
            self.app.log_spotted_toc(item_id, leaf_num)
            self.toc_spotted.Disable()
            self.toc_not.Enable()
            if self.next_pg.IsEnabled():
                self.next_pg.SetFocus()
            elif self.next_issue.IsEnabled():
                self.next_issue.SetFocus()
            else:
                self.more_issues.SetFocus()
            # event.Skip()

    def evt_untoc_spotted(self, event):
        if event.ClassName == 'wxCommandEvent' or \
                (event.ClassName == 'wxKeyEvent' and
                 event.GetKeyCode() not in (wx.WXK_TAB, wx.WXK_SHIFT)):
            self.toc_spotted.Enable()
            # If self.save_toc_img is True, delete the image. In all cases,
            # forget/delete the toc_spec.
            item_id = self.current_issue.GetStringSelection()
            if self.app.save_toc_imgs:
                self.app.delete_toc_image(item_id, self.app.leaf_num)
            self.app.forget_toc(item_id, self.app.leaf_num)
            # event.Skip()

    def evt_queue_issues(self, event):
        self.queue_issues(event)
        # event.Skip()

    def queue_issues(self, event):
        if event.ClassName == 'wxCommandEvent' or \
                (event.ClassName == 'wxKeyEvent' and
                 event.GetKeyCode() not in (wx.WXK_TAB, wx.WXK_SHIFT)):
            self.app.queue_next_batch()
            self.current_issue.SetSelection(0)
            self.next_pg.SetFocus()
            # event.Skip()

    def show_page(self):
        img = self.app.get_displayed_leaf_img()
        if img is not None:
            self.page_img.GetChildren()[0].SetBitmap(img)
            self.page_img.Refresh()
        else:
            self.page_img.GetChildren()[0].SetBitmap(wx.NullBitmap)
            self.page_img.Refresh()
            self.frame_statusbar.SetStatusText('No image to display.')

    def evt_edit_settings(self, event):
        print('Config settings TBD...')
        event.Skip()

    def evt_set_best_focus(self, event):
        if event:
            if self.next_pg.IsEnabled():
                self.next_pg.SetFocus()
            elif self.next_issue.IsEnabled():
                self.next_issue.SetFocus()
            elif self.more_issues.IsEnabled():
                self.more_issues.SetFocus()
        # event.Skip()


# end of class FmtkTOCspotterGui


###########################################################################
# Class FmtkTOCspotterApp
###########################################################################
class FmtkTOCspotterApp(wx.App):
    def __init__(self, redirect=False, filename=None, useBestVisual=False,
                 clearSigInt=True):
        # Read the configuration file.
        self.config = ConfigParser()
        self.config.read('FmtkTOCspotterApp.ini')
        self.leaf_queue_dir = self.config['Paths and Filenames'][
            'leaf_queue_dir']
        self.toc_img_dir = self.config['Paths and Filenames']['toc_img_dir']
        self.max_height = int(self.config['Persistent variables']['max_height'])
        self.queue_size = int(self.config['Persistent variables']['queue_size'])
        self.more_pages = int(self.config['Persistent variables']['more_pages'])
        self.save_toc_imgs = self.config['Persistent variables'].getboolean(
            'save_to_imgs')
        # 'pfn' is the path and filename of the CSV-format TOC file, etc.
        toc_pfn = self.config['Paths and Filenames']['spotted_tocs_pfn']
        compmags_pfn = self.config['Paths and Filenames']['compmags_pfn']
        done_pubs_pfn = self.config['Paths and Filenames']['done_pubs_pfn']
        # Persistent local variables stored in the config file.
        self.spotted_tocs = pd.read_csv(toc_pfn, header=0, index_col=False)
        self.known_pubs = pd.read_csv(compmags_pfn, header=0, index_col=False)
        self.done_pubs = pd.read_csv(done_pubs_pfn, header=0, index_col=False)
        self.queued_pubs = self.known_pubs.sample(3)

        # Session specific local variables
        self.pg_queue = {}
        self.image_pool = lg.DownloadPool()
        self.sema4 = threading.Semaphore(10)
        self.frame = None
        # At Internet Archive, image ids are known as 'leaf's.
        self.leaf_num = 0
        self.downloads_pending = 0
        self.page_images = {}
        self.no_img_flag = False
        self.pil_img2buffer = wx.Image(100, 100)
        self.buffer = wx.NullBitmap

        # Image grabbing threads post these messages and we react...
        pub.subscribe(self.queue_updated, 'image_ready')
        pub.subscribe(self.queue_problem, 'image_not_found')
        pub.subscribe(self.queue_problem, 'server_not_found')
        # Now do the rest of a wx.App's init...
        super().__init__(redirect, filename, useBestVisual, clearSigInt)

    def OnInit(self):
        #  TODO: Image height offset hard-coded, needs dynamic fix or
        #   user setting
        if 'wxMac' in wx.PlatformInfo:
            self.max_height = wx.GetDisplaySize().Height - 88
        else:
            self.max_height = wx.GetDisplaySize().Height - 128
        # Create the frame
        self.frame = TOCspotterGui(None)
        self.frame.app = self
        self.buffer = wx.Bitmap(100, 100)
        if self.more_pages == 1:
            self.frame.more_pgs.SetLabel('1 More Pg')
        self.frame.more_pgs.Disable()
        self.frame.current_issue.Set(self.queued_pubs['Item_id'].values)
        self.frame.current_issue.SetSelection(0)
        self.frame.prev_issue.Disable()
        self.queue_page_images()
        self.frame.next_pg.SetFocus()
        return True

    def read_config(self):
        self.config = ConfigParser()
        self.config.read('FmtkTOCspotterApp.ini')
        self.leaf_queue_dir = self.config['Paths and Filenames'][
            'leaf_queue_dir']
        self.toc_img_dir = self.config['Paths and Filenames']['toc_img_dir']
        self.max_height = int(self.config['Persistent variables']['max_height'])
        self.queue_size = int(self.config['Persistent variables']['queue_size'])
        # 'pfn' is the path and filename of the CSV-format TOC file, etc.
        toc_pfn = self.config['Paths and Filenames']['spotted_tocs_pfn']
        compmags_pfn = self.config['Paths and Filenames']['compmags_pfn']
        done_pubs_pfn = self.config['Paths and Filenames']['done_pubs_pfn']
        # Persistent local variables stored in the config file.
        self.spotted_tocs = pd.read_csv(toc_pfn, header=0, index_col=False)
        self.known_pubs = pd.read_csv(compmags_pfn, header=0, index_col=False)
        self.done_pubs = pd.read_csv(done_pubs_pfn, header=0, index_col=False)
        self.queued_pubs = self.known_pubs.sample(3)

    def queue_page_images(self, item_id=None):
        # When an issue is selected/set in the issue choice widget, get its
        # first self.queue_size page images
        if item_id is None:
            # Get page images for all issues in the issue choice widget...
            self.frame.StatusBar.SetStatusText('Getting queued issue '
                                               'images...', 1)
            for issue_id in self.queued_pubs['Item_id'].values:
                for leaf_num in range(0, self.queue_size):
                    self.grab_leaf(issue_id, leaf_num)
        else:
            self.frame.StatusBar.SetStatusText('Getting new issue images', 1)
            for leaf_num in range(0, self.queue_size):
                self.grab_leaf(item_id, leaf_num)

    def queue_next_batch(self):
        """
        Get random sample of next pubs to queue ignoring pubs already known,
        then queue their page images and update the issues choice widget.
        :return: list of next pubs
        """
        self.log_done_pub(self.frame.current_issue.GetStringSelection())
        next_pubs = pd.DataFrame(columns=['Item_id'])
        while len(next_pubs) < 3:
            next_pub = self.known_pubs.sample(1)
            if next_pub.values[0][0] not in self.done_pubs['Item_id'].tolist():
                next_pubs = next_pubs.append([{'Item_id': next_pub.values[0][
                    0]}], ignore_index=True)
            continue
        self.queued_pubs = next_pubs.copy()
        self.frame.current_issue.Set(self.queued_pubs['Item_id'].values)
        self.frame.current_issue.SetSelection(0)
        self.frame.prev_issue.Disable()
        self.frame.next_issue.Enable()
        self.frame.next_pg.Enable()
        self.frame.prev_pg.Disable()
        self.leaf_num = 0
        self.queue_page_images()
        self.frame.next_pg.SetFocus()

    def queue_updated(self, item_id, leaf_num, pil_img, pil_sm_img):
        # An image has come back, update the statusbar...
        self.downloads_pending -= 1
        self.frame.StatusBar.SetStatusText('Downloads pending: ' +
                                           str(self.downloads_pending), 0)
        if item_id in self.pg_queue:
            self.pg_queue[item_id][str(leaf_num)] = pil_img
            self.pg_queue[item_id][str(leaf_num) + 'sm'] = pil_sm_img
        else:
            self.pg_queue[item_id] = {}
            self.pg_queue[item_id][str(leaf_num)] = pil_img
            self.pg_queue[item_id][str(leaf_num) + 'sm'] = pil_sm_img
        self.frame.StatusBar.SetStatusText('Queued image: ' + item_id +
                                           'leaf: ' + str(leaf_num), 1)
        if item_id == self.frame.current_issue.GetStringSelection() and \
                self.leaf_num == leaf_num:
            self.frame.show_page()
        if self.downloads_pending == 0:
            self.frame.StatusBar.SetStatusText('Downloads done.', 0)
            self.frame.StatusBar.SetStatusText('', 1)
        if self.leaf_num <= self.queue_size - 1:
            self.frame.next_pg.Enable()
            self.frame.next_pg.SetFocus()

    def queue_problem(self, err_msg, err_code):
        # Adjust the self.page_queue, widgets, and statusbar
        pass
        self.frame.StatusBar.SetStatusText(
            'Error: ' + err_msg + ' ' + str(err_code), 1)
        self.downloads_pending -= 1
        self.frame.StatusBar.SetStatusText('Downloads pending: ' +
                                           str(self.downloads_pending), 0)
        if self.downloads_pending == 0:
            self.frame.StatusBar.SetStatusText('', 0)
            self.frame.StatusBar.SetStatusText('', 1)
            self.frame.next_pg.Enable()

    def get_displayed_leaf_img(self):
        item_id = self.frame.current_issue.GetStringSelection()
        try:
            pil_image = self.pg_queue[item_id][str(self.leaf_num)]
        except KeyError:
            # print('No image for', item_id, 'leaf:', str(self.leaf_num))
            self.frame.StatusBar.SetStatusText('No Image Available', 1)
            pil_image = Image.open('./resources/NoImgAvbl.png', 'r')
            self.no_img_flag = True
        display_width = self.frame.page_img.GetChildren()[0].Size.Width
        resize_percent = display_width / pil_image.size[0]
        hsize = int((float(pil_image.size[1]) * float(
            resize_percent)))
        display_image = pil_image.resize((
            int(display_width), int(hsize)), Image.BICUBIC)

        self.pil_img2buffer = wx.Image(display_image.size[0],
                                       display_image.size[1])
        self.pil_img2buffer.SetData(display_image.convert("RGB").tobytes())
        try:
            self.buffer = self.pil_img2buffer.ConvertToBitmap()
        except KeyError:
            print('Could not convert PIL image to bitmap...')
            return None
        return self.buffer

    def get_more_pages(self, item_id):
        # Get the next page of the current issue
        self.frame.StatusBar.SetStatusText('Getting more pages', 1)
        self.queue_size = self.queue_size + self.more_pages
        self.leaf_num += 1
        for leaf_num in range(self.leaf_num, self.queue_size):
            self.grab_leaf(item_id, leaf_num)

    def grab_leaf(self, item_id, leaf_num):
        # Grab the leaf and add it to the queue
        self.downloads_pending += 1
        self.frame.StatusBar.SetStatusText(
            'Downloads pending: ' + str(self.downloads_pending), 0)
        leaf_grabber = Thread(target=lg.FmtkLeafGrabber,
                              args=[item_id, leaf_num, None,
                                    self.leaf_queue_dir, self.max_height,
                                    self.sema4, self.image_pool])
        if leaf_grabber is not None:
            leaf_grabber.setDaemon(True)
            leaf_grabber.start()

    def save_toc_image(self):
        item_id = self.frame.current_issue.GetStringSelection()
        toc_fname = item_id + '_tocleaf_' + str(self.leaf_num).zfill(4) + '.jpg'
        save_img_path = self.toc_img_dir + toc_fname
        leaf_file = Path(save_img_path)
        if not leaf_file.is_file():
            if str(self.leaf_num) in self.pg_queue[item_id].keys():
                pil_image = self.pg_queue[item_id][str(self.leaf_num)]
                pil_image.save(save_img_path)
        else:
            print("Already saved.")
        return item_id, self.leaf_num

    def delete_toc_image(self, item_id, leaf_num):
        toc_fname = item_id + '_tocleaf_' + str(leaf_num).zfill(4) + '.jpg'
        leaf_file = Path(self.toc_img_dir + toc_fname)
        if leaf_file.is_file():
            try:
                os.remove(leaf_file)
            except OSError:
                self.frame.StatusBar.SetStatusText('Could not delete ' +
                                                   toc_fname, 1)
            self.frame.StatusBar.SetStatusText('Deleted: ' + toc_fname, 1)
        else:
            self.frame.StatusBar.SetStatusText('Not found: ' + toc_fname, 1)

    def forget_toc(self, item_id, leaf_num):
        self.spotted_tocs = self.spotted_tocs.drop(
            self.spotted_tocs[(self.spotted_tocs['Item_id'] == item_id) &
                              (self.spotted_tocs['Leaf_num'] ==
                               leaf_num)].index)
        self.spotted_tocs.to_csv('./tocdata/spotted_tocs.csv', header=True,
                                 index=False)
        self.frame.StatusBar.SetStatusText('Forgot toc: ' + item_id +
                                           'leaf: ' + str(leaf_num), 1)
        self.frame.toc_spotted.Enable()
        self.frame.toc_not.Disable()

    def log_spotted_toc(self, item_id, leaf_num):
        new_toc = {'Item_id': item_id, 'Leaf_num': leaf_num}
        self.spotted_tocs = self.spotted_tocs.append(new_toc, ignore_index=True)
        self.spotted_tocs = self.spotted_tocs.sort_values('Item_id')
        self.spotted_tocs.to_csv('./tocdata/spotted_tocs.csv', header=True,
                                 index=False)
        pass

    def log_done_pub(self, item_id):
        done_pub = {'Item_id': item_id}
        self.done_pubs = self.done_pubs.append(done_pub, ignore_index=True)
        self.done_pubs = self.done_pubs.sort_values('Item_id')
        self.done_pubs.to_csv('./tocdata/done_pubs.csv', header=True,
                              index=False)

    def check_toc(self, item_id=None, leaf_num=None):
        # Check if this toc has been spotted before...
        if item_id is None:
            item_id = self.frame.current_issue.GetStringSelection()
            leaf_num = self.leaf_num
        if self.spotted_tocs.empty:
            self.frame.toc_spotted.Enable()
            self.frame.toc_not.Disable()
        else:
            toc_row = self.spotted_tocs.loc[
                (self.spotted_tocs['Item_id'] == item_id) &
                (self.spotted_tocs['Leaf_num'] == leaf_num)]
            if toc_row.empty:
                if self.no_img_flag:
                    self.frame.toc_spotted.Disable()
                    self.frame.toc_not.Disable()
                    self.no_img_flag = False
                else:
                    self.frame.toc_spotted.Enable()
                    self.frame.toc_not.Disable()
            else:
                if self.no_img_flag:
                    self.frame.toc_spotted.Disable()
                    self.frame.toc_not.Disable()
                    self.no_img_flag = False
                else:
                    self.frame.toc_spotted.Disable()
                    self.frame.toc_not.Enable()
                return True
        return False


# end of class FmtkTOCspotterApp


if __name__ == "__main__":
    app = FmtkTOCspotterApp()
    app.SetTopWindow(app.frame)
    app.frame.Show()
    app.MainLoop()
