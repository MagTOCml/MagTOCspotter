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

import csv
import os
import random
import shutil
import threading
from configparser import ConfigParser
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from threading import Thread
# import urllib.parse
from urllib.error import URLError, HTTPError
from urllib.request import Request, urlopen
# Workaround for Nuitka compilation issue
# import Requests
import certifi

import wx
from PIL import Image
from pubsub import pub

import FmtkLeafGrabber as lg
from FmtkTOCspotterGui import FmtkTOCspotterGui

Image.MAX_IMAGE_PIXELS = 1000000000


###########################################################################
# Class TOCloc
###########################################################################
@dataclass
class TOCloc:
    """
    A class to hold the location of a TOC file specific to the structure of
    digital collections at the Internet Archive.
    """
    Item_id: str
    Leaf_num: int


###########################################################################
# Class TOCspotterGui
###########################################################################
class TOCspotterGui(FmtkTOCspotterGui):
    def __init__(self, *args, **kwds):
        FmtkTOCspotterGui.__init__(self, *args, **kwds)
        if 'wxMac' in wx.PlatformInfo:
            self.m_menuItem3.SetItemLabel('Mac: Quit from App Menu')
            self.m_menuItem3.Enable(False)
        self.Bind(wx.EVT_CLOSE, self.evt_quit_app)
        self.frame_statusbar.SetStatusWidths([150, -1])
        self.frame_statusbar.SetStatusText("Ready", 0)
        self.app = None

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
            self.more_pgs.Disable()
            self.next_pg.SetFocus()
            # event.Skip()

    def evt_toc_spotted(self, event):
        """
        If self.save_toc_img is True, save the image. In all cases,
        remember/save the toc_spec.
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

    def evt_update_csv_data(self, event):
        """Download the latest CSV data and update the database."""
        if event.ClassName == 'wxCommandEvent' or \
                (event.ClassName == 'wxKeyEvent' and
                 event.GetKeyCode() not in (wx.WXK_TAB, wx.WXK_SHIFT)):
            self.app.update_csv_data()
        event.Skip()

    def queue_issues(self, event):
        if event.ClassName == 'wxCommandEvent' or \
                (event.ClassName == 'wxKeyEvent' and
                 event.GetKeyCode() not in (wx.WXK_TAB, wx.WXK_SHIFT)):
            # Show modal dialog to block input until done...
            pass
            # Download the next batch of issues...
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

    def evt_quit_app(self, event):
        if event:
            self.app.quit_app()
            # event.Skip()

# end of class FmtkTOCspotterGui


###########################################################################
# Class FmtkTOCspotterApp
###########################################################################
class FmtkTOCspotterApp(wx.App):
    def __init__(self, redirect=False, filename=None, useBestVisual=False,
                 clearSigInt=True):
        # Var/attributes read from the configuration file and defined
        # in the OnInit method.
        self.done_pubs_pfn = None
        self.tocs_pfn = None
        self.compmags_pfn = None
        self.save_toc_imgs = None
        self.csv_fieldnames = None
        self.queued_pubs = None
        self.done_pubs = None
        self.known_pubs = None
        self.spotted_tocs = None
        self.more_pages = None
        self.queue_size = None
        self.toc_img_dir = None
        self.max_height = None
        self.config = None
        self.dl_dlg = None
        self.sess_dlg = None

        # Specify location of user's tocdata directory...
        # TODO: Check how this works on Windows.
        self.tocdata_dir = os.path.join(os.path.expanduser('~'), 'tocdata')

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

        # Image grabbing threads post these messages, and we react...
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
        self.read_config()
        # Create the frame
        self.frame = TOCspotterGui(None)
        self.frame.app = self
        self.buffer = wx.Bitmap(100, 100)
        if self.more_pages == 1:
            self.frame.more_pgs.SetLabel('1 More Pg')
        self.frame.more_pgs.Disable()
        self.frame.current_issue.SetSelection(0)
        self.frame.prev_issue.Disable()
        # Workaround for Nuitka SSL issue
        cafile = certifi.where()
        print('CA certs: ' + cafile, 1)
        self.frame.more_issues.SetFocus()
        return True

    def read_config(self):
        self.config = ConfigParser()
        tocdir = self.tocdata_dir
        self.config.read(os.path.join(tocdir, 'FmtkTOCspotterApp.ini'))
        # 'pfn' is the path and filename of the CSV-format TOC file, etc.
        self.toc_img_dir = os.path.join(tocdir,
                                        self.config['Paths and Filenames'][
                                            'toc_img_dir'])
        self.tocs_pfn = os.path.join(tocdir, self.config['Paths and Filenames'][
            'spotted_tocs_pfn'])
        self.compmags_pfn = os.path.join(tocdir, self.config['Paths and '
                                                             'Filenames'][
            'compmags_pfn'])
        self.done_pubs_pfn = os.path.join(tocdir, self.config['Paths and '
                                                              'Filenames'][
            'done_pubs_pfn'])
        # Persistent local variables stored in the config file.
        self.max_height = int(
            self.config['Persistent variables']['max_height'])
        self.queue_size = int(
            self.config['Persistent variables']['queue_size'])
        self.save_toc_imgs = bool(self.config['Persistent variables'][
            'save_toc_imgs'])
        self.more_pages = int(
            self.config['Persistent variables']['more_pages'])
        # Read the project's master list of known computer magazines in the
        # collections of the Internet Archive.
        self.known_pubs = self.read_csv(self.compmags_pfn)
        self.queued_pubs = random.sample(self.known_pubs, 3)
        self.csv_fieldnames = {
            self.tocs_pfn: ['Item_id', 'Leaf_num'],
            self.done_pubs_pfn: ['Item_id']
        }
        # self.update_csv_data()

    def read_csv(self, pfn_url):
        """
        :param pfn_url: Path and filename or URL of the CSV-format TOC file.
        :return list: compmags & done_pubs are item_id only, spotted_tocs
                      are Item_id and Leaf_num TOCloc dataclass instances.
        """
        if pfn_url.startswith('http'):
            # If the URL starts with http, we assume it's a URL to a CSV file.
            request = Request(pfn_url)
            try:
                reply = urlopen(request)
            except HTTPError as err:
                wx.CallAfter(lambda *a: pub.sendMessage(
                    "file_not_found",
                    err_msg='The server could not fulfill the request.',
                    err_code=404))
            except URLError as err:
                wx.CallAfter(lambda *a: pub.sendMessage(
                    "server_not_found",
                    err_msg='We failed to reach a server.',
                    err_code=err.reason))
            else:
                flo = reply.read().decode('utf-8')
                reader = csv.DictReader(flo.splitlines())
                return self.get_csv_data(reader)
        else:
            # Otherwise, we assume it's a local file.
            pfn_url = os.path.join(os.getcwd(), pfn_url)
            with open(pfn_url, newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                return self.get_csv_data(reader)
        return []

    @staticmethod
    def get_csv_data(reader):
        """
        :param reader: A csv.DictReader object.
        :return:
        """
        result_list = []
        if len(reader.fieldnames) == 1:
            for row in reader:
                result_list.append(row[reader.fieldnames[0]])
        else:
            for row in reader:
                toc_loc = TOCloc(row[reader.fieldnames[0]],
                                 row[reader.fieldnames[1]])
                result_list.append(toc_loc)
        return result_list

    def write_csv(self, pfn, data):
        field_names = self.csv_fieldnames[pfn]
        with open(pfn, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=field_names)
            writer.writeheader()
            if len(field_names) == 1:
                for item in data:
                    writer.writerow({field_names[0]: item})
            else:
                for item in data:
                    writer.writerow({field_names[0]: item.Item_id,
                                     field_names[1]: item.Leaf_num})

    def queue_page_images(self, item_id=None):
        self.popup_download_progress_dlg()

        if item_id is None:
            # Get page images for all issues in the issue choice widget...
            self.frame.StatusBar.SetStatusText('Getting queued issue '
                                               'images...', 1)
            for issue_id in self.queued_pubs:
                for leaf_num in range(0, self.queue_size):
                    self.grab_leaf(issue_id, leaf_num)
        else:
            # When an issue is selected/set in the issue choice widget, get its
            # first self.queue_size page images
            self.frame.StatusBar.SetStatusText('Getting new issue images', 1)
            for leaf_num in range(0, self.queue_size):
                self.grab_leaf(item_id, leaf_num)

    def popup_download_progress_dlg(self):
        # Create a ProgressDialog to show the user the progress of the
        # downloading.
        self.dl_dlg = wx.ProgressDialog(
            'Downloading page images',
            'Wait while downloading page images...',
            maximum=100,
            parent=self.frame,
            style=wx.PD_AUTO_HIDE | wx.PD_ELAPSED_TIME)
        self.dl_dlg.Show()

    def queue_next_batch(self):
        """
        Get random sample of next pubs to queue ignoring pubs already known,
        then queue their page images and update the issues choice widget.
        :return: list of next pubs
        """
        self.log_done_pub(self.frame.current_issue.GetStringSelection())
        next_pubs = []
        while not next_pubs or len(next_pubs) < 3:
            next_pub = random.sample(self.known_pubs, 1)[0]
            if next_pub not in self.done_pubs:
                next_pubs.append(next_pub)
            continue
        self.queued_pubs = next_pubs.copy()
        self.frame.current_issue.Set(self.queued_pubs)
        self.frame.current_issue.SetSelection(0)
        self.frame.prev_issue.Disable()
        self.frame.next_issue.Enable()
        self.frame.next_pg.Enable()
        self.frame.prev_pg.Disable()
        self.leaf_num = 0
        self.queue_page_images()
        self.frame.next_pg.SetFocus()

    def queue_updated(self, item_id, leaf_num, pil_img, pil_sm_img):
        # Update the dl_dlg with the current progress.
        self.dl_dlg.Pulse('Wait while grabbing leaf images...')
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
            self.dl_dlg.Update(100)
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
            pil_image = Image.open('./tocdata/NoImgAvbl.png', 'r')
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
        self.frame.more_pgs.Disable()
        self.frame.toc_spotted.Enable()
        self.popup_download_progress_dlg()
        # Get the next page of the current issue
        self.frame.StatusBar.SetStatusText('Getting more pages', 1)
        self.queue_size = self.queue_size + self.more_pages
        self.leaf_num += 1
        for leaf_num in range(self.leaf_num, self.queue_size):
            self.grab_leaf(item_id, leaf_num)

    def grab_leaf(self, item_id, leaf_num):
        # Grab the leaf and add it to the queue
        self.downloads_pending += 1
        self.dl_dlg.Pulse('Wait while grabbing leaf images...')
        self.frame.StatusBar.SetStatusText(
            'Downloads pending: ' + str(self.downloads_pending), 0)
        leaf_grabber = Thread(target=lg.FmtkLeafGrabber,
                              args=[item_id, leaf_num, None,
                                    None, self.max_height,
                                    self.sema4, self.image_pool])
        if leaf_grabber is not None:
            # leaf_grabber.setDaemon(True)
            leaf_grabber.daemon = True
            leaf_grabber.start()

    def save_toc_image(self):
        item_id = self.frame.current_issue.GetStringSelection()
        toc_fname = item_id + '_tocleaf_' + \
            str(self.leaf_num).zfill(4) + '.jpg'
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
        self.spotted_tocs.remove(TOCloc(item_id, leaf_num))
        self.write_csv(self.tocs_pfn, self.spotted_tocs)
        self.frame.StatusBar.SetStatusText('Forgot toc: ' + item_id +
                                           'leaf: ' + str(leaf_num), 1)
        self.frame.toc_spotted.Enable()
        self.frame.toc_not.Disable()

    def log_spotted_toc(self, item_id, leaf_num):
        new_toc = TOCloc(item_id, leaf_num)
        self.spotted_tocs.append(new_toc)
        self.spotted_tocs.sort(key=lambda x: x.Item_id)
        self.write_csv(self.tocs_pfn, self.spotted_tocs)
        pass

    def log_done_pub(self, item_id):
        self.done_pubs.append(item_id)
        self.done_pubs.sort()
        self.write_csv(self.done_pubs_pfn, self.done_pubs)

    def check_toc(self, item_id=None, leaf_num=None):
        # Check if this toc has been spotted before...
        if item_id is None:
            item_id = self.frame.current_issue.GetStringSelection()
            leaf_num = self.leaf_num
        if len(self.spotted_tocs) == 0:
            self.frame.toc_spotted.Enable()
            self.frame.toc_not.Disable()
        else:
            # Find TOCloc object in spotted_tocs
            toc_loc = TOCloc(item_id, leaf_num)
            if toc_loc in self.spotted_tocs:
                if self.no_img_flag:
                    self.frame.toc_spotted.Disable()
                    self.frame.toc_not.Disable()
                    self.no_img_flag = False
                else:
                    self.frame.toc_spotted.Disable()
                    self.frame.toc_not.Enable()
                return True
            else:
                if self.no_img_flag:
                    self.frame.toc_spotted.Disable()
                    self.frame.toc_not.Disable()
                    self.no_img_flag = False
                else:
                    self.frame.toc_spotted.Enable()
                    self.frame.toc_not.Disable()
        return False

    def update_csv_data(self):
        dlg = wx.MessageDialog(None, "Do you want to continue TOC spotting "
                                     "with your current CSV tocdata or archive "
                                     "these files and begin a new session?",
                               "Continue or Archive Data-gathering",
                               wx.YES_NO |
                               wx.ICON_QUESTION)
        dlg.SetYesNoLabels("Continue", "Archive")
        result = dlg.ShowModal()
        if result == wx.ID_NO:
            date_str = date.today().strftime('%m%d%y')

            # Archive current files
            archive_dir = os.path.join(self.tocdata_dir, 'archive')
            if not os.path.exists(archive_dir):
                os.makedirs(archive_dir)
            if os.path.exists(self.tocs_pfn):
                for x in 'abcdefghijklmnopqrstuvwxyz':
                    archive_name = os.path.join(archive_dir,
                                                f'spotted_tocs{date_str}'
                                                f'{x}.csv')
                    if os.path.exists(archive_name):
                        continue
                    else:
                        shutil.move(self.tocs_pfn, archive_name)
                        break
            if os.path.exists(self.done_pubs_pfn):
                for x in 'abcdefghijklmnopqrstuvwxyz':
                    archive_name = os.path.join(archive_dir,
                                                f'done_pubs{date_str}'
                                                f'{x}.csv')
                    if os.path.exists(archive_name):
                        continue
                    else:
                        shutil.move(self.done_pubs_pfn, archive_name)
                        break
            # Update current files
            st_url = "https://raw.githubusercontent.com/MagTOCml/MagTOCdata" \
                     "/main/tocdata/spotted_tocs.csv"
            dp_url = "https://raw.githubusercontent.com/MagTOCml/MagTOCdata" \
                     "/main/tocdata/done_pubs.csv"
            self.spotted_tocs = self.read_csv(st_url)
            self.write_csv(self.tocs_pfn, self.spotted_tocs)
            self.done_pubs = self.read_csv(dp_url)
            self.write_csv(self.done_pubs_pfn, self.done_pubs)
            if self.frame is not None:
                self.frame.StatusBar.SetStatusText('Updated and archived CSV '
                                                   'files.', 1)
        else:
            if self.frame is not None:
                self.frame.StatusBar.SetStatusText('CSV files not updated.', 1)
            self.spotted_tocs = self.read_csv(self.tocs_pfn)
            self.done_pubs = self.read_csv(self.done_pubs_pfn)

    def quit_app(self):
        self.frame.Close()
        self.frame.Destroy()

# end of class FmtkTOCspotterApp


if __name__ == "__main__":
    app = FmtkTOCspotterApp()
    app.SetTopWindow(app.frame)
    app.frame.Show()
    app.update_csv_data()
    app.MainLoop()
