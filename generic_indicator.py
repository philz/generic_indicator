#!/usr/bin/env python
#
# Author: Philip Zeyliger <philip@cloudera.com>
# License: Apache 2.0
#
# Generic GTK App Indicator
#
# gksudo for sudo?
#
# Based on http://conjurecode.com/create-indicator-applet-for-ubuntu-unity-with-python/
# See also https://wiki.ubuntu.com/DesktopExperienceTeam/ApplicationIndicators

import sys
import gtk
import appindicator
import argparse
import subprocess
import logging

FREQUENCY_MILLIS = 10000

LOG = logging.getLogger(__name__)

class Indicator(object):


  def __init__(self, args):
    self.off_icon = args.officon
    self.on_icon = args.onicon

    self.indicator = appindicator.Indicator(
      "generic-indicator",
      self.off_icon,
      appindicator.CATEGORY_APPLICATION_STATUS)
    self.indicator.set_status(appindicator.STATUS_ACTIVE)


    self.subprocess = None

    self.command = args.cmd

    self.menu = gtk.Menu()

    self.start_item = gtk.MenuItem("Start")
    self.start_item.connect("activate", self.start)
    self.start_item.show()
    self.menu.append(self.start_item)

    self.stop_item = gtk.MenuItem("Stop")
    self.stop_item.connect("activate", self.stop)
    self.stop_item.show()
    self.menu.append(self.stop_item)

    self.quit_item = gtk.MenuItem("Quit")
    self.quit_item.connect("activate", self.quit)
    self.quit_item.show()
    self.menu.append(self.quit_item)

    self.indicator.set_menu(self.menu)

  def activate(self):
    # Using the "attention" hint doesn't work for me,
    # so just changing the icon directly.  In theory,
    # the following is sufficient:
    #   self.indicator.set_attention_icon(args.onicon)
    #   self.indicator.set_status(appindicator.STATUS_ATTENTION)
    self.indicator.set_icon(self.on_icon)

  def deactivate(self):
    self.indicator.set_icon(self.off_icon)

  def start(self, widget):
    if self.subprocess is not None:
      LOG.warning("Cannot start a process when one is already running.")
      return

    LOG.info("Starting subprocess.")
    self.subprocess = subprocess.Popen(self.command, 
      shell=True,
      close_fds=True,
      stdin=None, stdout=None, stderr=None)

    self.activate()

  def stop(self, widget):
    if self.subprocess is not None:
      LOG.info("Killing subprocess.")
      self.subprocess.kill()

  def periodic(self):
    gtk.timeout_add(FREQUENCY_MILLIS, self.periodic)
    if self.subprocess is not None:
      if self.subprocess.poll() is not None:
        LOG.info("Subprocess exited: %d" % (self.subprocess.poll(),))
        self.subprocess = None
        self.deactivate()
      else:
        self.activate()
    else:
      self.deactivate()

  def quit(self, widget):
    sys.exit(0)

  def main(self):
    gtk.timeout_add(FREQUENCY_MILLIS, self.periodic)
    gtk.main()


def parse_args():
  parser = argparse.ArgumentParser(description='monitor a pre-configured process')
  parser.add_argument('--officon', help='icon to use when disabled', default="security-low")
  parser.add_argument('--onicon', help='icon to use when enabled', default="security-high")
  parser.add_argument('cmd', help='command to run')
  args = parser.parse_args()
  return args
      
if __name__ == "__main__":
  logging.basicConfig(level=logging.INFO)

  args = parse_args()
  indicator = Indicator(args)
  indicator.main()
