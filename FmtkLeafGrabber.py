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

import base64
import json
import pickle
import threading
from pathlib import Path
from threading import Thread
import certifi
from urllib.error import URLError, HTTPError
from urllib.request import Request, urlopen

import wx
from PIL import Image, ImageDraw, ImageFont
from pubsub import pub


# Now some useful classes to handle image file access at the Internet Archive.
class PythonObjectEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (list, dict, str, int, float, bool, type(None))):
            return super().default(obj)
        elif isinstance(obj, Image.Image):
            # We don't want ad images in our saved files...
            return
        return {'_python_object': base64.b64encode(
            pickle.dumps(obj)).decode('utf-8')
                }


def as_python_object(dct):
    if '_python_object' in dct:
        return pickle.loads(base64.b64decode(
            dct['_python_object'].encode('utf-8')))
    return dct


class DownloadPool(object):
    def __init__(self):
        super(DownloadPool, self).__init__()
        self.active = []
        self.lock = threading.Lock()

    def make_active(self, name):
        with self.lock:
            self.active.append(name)
            # logging.debug('Running: %s', self.active)

    def make_inactive(self, name):
        with self.lock:
            self.active.remove(name)
            # logging.debug('Running: %s', self.active)


class FmtkLeafGrabber(Thread):
    """This thread handles getting a leaf image from the Internet Archive
        destined for the pg_queue."""

    def __init__(self, item_id=None, leafnum=0, local_leafdir=None, outdir=None,
                 max_height=0, sema4=None, img_pool=None, save_img=False):
        """Init the Worker Thread that queues leaf images."""
        Thread.__init__(self)
        self.item_id = item_id
        self.current_leaf = leafnum
        self.local_leafdir = local_leafdir
        self.outdir = outdir
        self.max_height = max_height
        self.save_image_flag = save_img
        self.fontname = 'arial.ttf'
        self.sema4 = sema4
        self.img_pool = img_pool
        self.pil_image = Image.Image()
        # logging.debug('Ready to launch a thread...')
        self.daemon = True
        self.start()  # start the thread
        # self.join()

    def run(self):
        """Run GetImage Worker Thread to grab an image from the local_leafdir,
          if available. Otherwise, download from the Internet Archive."""
        with self.sema4:
            name = threading.current_thread().name
            self.img_pool.make_active(name)
            if self.current_leaf == 'missing':
                self.image_unavailable()
            else:
                if self.local_leafdir is not None:
                    pass
                    self.pil_image = self.get_local_leaf()
                else:
                    request = Request("https://archive.org/download/" +
                                      self.item_id + "/page/leaf" +
                                      str(self.current_leaf))
                    try:
                        reply = urlopen(request, cafile=certifi.where())
                    except HTTPError as err:
                        # print('The server could not fulfill the request.')
                        # print('Error code: ', err.code)
                        if err is not None:
                            errcode = err.code
                        else:
                            errcode = 'None'
                        wx.CallAfter(lambda *a: pub.sendMessage(
                            "image_not_found",
                            err_msg='The server could not fulfill the request.',
                            err_code=errcode))
                    except URLError as err:
                        # print('We failed to reach a server.')
                        print('Reason: ', err.reason)
                        reason = err.reason
                        wx.CallAfter(lambda *a: pub.sendMessage(
                            "server_not_found",
                            err_msg='We failed to reach a server.',
                            err_code=reason))
                    else:
                        self.pil_image = Image.open(reply)
                        # Do the full-page image scaled to device frame..
                        resize_percent = self.max_height / \
                            self.pil_image.size[1]
                        wsize = int((float(self.pil_image.size[0]) * float(
                            resize_percent)))
                        pil_sm_image = self.pil_image.resize((
                            int(wsize), int(self.max_height)), Image.BICUBIC)
                        wx.CallAfter(lambda *a: pub.sendMessage(
                            "image_ready",
                            item_id=self.item_id,
                            leaf_num=self.current_leaf,
                            pil_img=self.pil_image,
                            pil_sm_img=pil_sm_image))
                        if self.save_image_flag:
                            self.save_image()
            self.img_pool.make_inactive(name)

    def get_local_leaf(self):
        local_leafpath = \
            self.local_leafdir + self.item_id + '_' \
            + str(self.current_leaf).zfill(4) + '.jpg'
        # If we have a local leaf image, use it.
        leaf_file = Path(local_leafpath)
        if leaf_file.is_file():
            img = Image.open(leaf_file)
        else:
            print("Oops, should not happen!? Local leaf!?")
            img = None
        return img

    def image_unavailable(self):
        funt = ImageFont.truetype(font='arial.ttf', size=400)
        pil_image = Image.new('RGB', (4200, 5600), 'white')
        dc = ImageDraw.Draw(pil_image)
        dc.text((int((4200 - 2600) / 2), int((5600 - 600) / 2)),
                "Image Unavailable", font=funt, fill='black')
        # First, do the full-page image...
        resize_percent = self.max_height / pil_image.size[1]
        wsize = int((float(pil_image.size[0]) * float(resize_percent)))
        pil_sm_image = pil_image.resize((int(wsize), int(self.max_height)),
                                        Image.BICUBIC)
        image = wx.Image(pil_sm_image.size[0], pil_sm_image.size[1])
        image.SetData(pil_sm_image.convert("RGB").tobytes())
        wx.CallAfter(lambda *a: pub.sendMessage(
            "image_ready", leafnum=self.current_leaf, pilimg=pil_image,
            pilsmimg=pil_sm_image))

    def save_image(self):
        save_img_path = self.outdir + self.item_id + '_' + str(
            self.current_leaf).zfill(4) + '.jpg'
        leaf_file = Path(save_img_path)
        if not leaf_file.is_file():
            self.pil_image.save(save_img_path)
        else:
            print("Oops, should not happen!?")
        return
