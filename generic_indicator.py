#!/usr/bin/env python
#
# Author: Philip Zeyliger <philip@cloudera.com>
# License: Apache 2.0
#
# Generic GTK App Indicator
#
# Based on http://conjurecode.com/create-indicator-applet-for-ubuntu-unity-with-python/
# See also https://wiki.ubuntu.com/DesktopExperienceTeam/ApplicationIndicators
#
# Example Invocations:
#  sudo generic_indicator.py -- openvpn --config ~/vpn/client.ovpn
#

import sys
import gtk
import appindicator
import argparse
import subprocess
import logging
import tempfile
import time

# Refresh this frequently
FREQUENCY_MILLIS = 10000
# After a signal, refresh a bit more aggressively.
REFRESH_AFTER_KILL_MILLIS = 100

LOG = logging.getLogger(__name__)

class Indicator(object):


  def __init__(self, args):
    self.off_icon = args.officon
    self.on_icon = args.onicon
    self.log_fd, self.log_file = tempfile.mkstemp()

    self.indicator = appindicator.Indicator(
      "generic-indicator",
      self.off_icon,
      appindicator.CATEGORY_APPLICATION_STATUS)
    self.indicator.set_status(appindicator.STATUS_ACTIVE)

    self.subprocess = None
    self.kill_nine_time = None

    self.command = args.cmd

    self.menu = gtk.Menu()

    str_cmd =  " ".join(args.cmd)
    if len(str_cmd) > 20:
      memo = str_cmd[0:17] + "..."
    else:
      memo = str_cmd
    self.memo_item = gtk.MenuItem(memo)
    self.memo_item.set_sensitive(False)
    self.memo_item.show()
    self.menu.append(self.memo_item)

    self.pid_item = gtk.MenuItem("")
    self.pid_item.set_sensitive(False)
    self.pid_item.show()
    self.menu.append(self.pid_item)

    self.start_item = gtk.MenuItem("Start")
    self.start_item.connect("activate", self.start)
    self.start_item.show()
    self.menu.append(self.start_item)

    self.stop_item = gtk.MenuItem("Stop")
    self.stop_item.connect("activate", self.stop)
    self.stop_item.set_sensitive(False)
    self.stop_item.show()
    self.menu.append(self.stop_item)

    self.view_logs_item = gtk.MenuItem("Logs")
    self.view_logs_item.connect("activate", self.view_logs)
    self.view_logs_item.show()
    self.menu.append(self.view_logs_item)

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
    self.start_item.set_sensitive(False)
    self.stop_item.set_sensitive(True)

  def deactivate(self):
    self.indicator.set_icon(self.off_icon)
    self.start_item.set_sensitive(True)
    self.stop_item.set_sensitive(False)
    self.pid_item.set_label("")

  def start(self, widget):
    if self.subprocess is not None:
      LOG.warning("Cannot start a process when one is already running.")
      return

    LOG.info("Starting subprocess.")
    self.subprocess = subprocess.Popen(self.command, 
      shell=False,
      close_fds=True,
      stdin=None, stdout=self.log_fd, stderr=self.log_fd)
    try:
      self.pid_item.set_label(" pid " + str(self.subprocess.pid))
    except:
      pass

    self.activate()

  def stop(self, widget):
    if self.subprocess is not None:
      LOG.info("Killing subprocess.")
      self.subprocess.terminate()
      self.kill_nine_time = time.time() + 5
    gtk.timeout_add(REFRESH_AFTER_KILL_MILLIS, self.periodic_helper)

  def view_logs(self, widget):
    subprocess.Popen("x-terminal-emulator -e less %s" % (self.log_file,),
      close_fds=True, stdin=None, stdout=None, stderr=None, shell=True)

  def periodic(self):
    gtk.timeout_add(FREQUENCY_MILLIS, self.periodic)
    self.periodic_helper()

  def periodic_helper(self):
    if self.subprocess is not None:
      if self.kill_nine_time is not None and self.kill_nine_time < time.time():
        # Enough is enough; kill the sucker.
        self.subprocess.kill()
      if self.subprocess.poll() is not None:
        LOG.info("Subprocess exited: %d" % (self.subprocess.poll(),))
        self.subprocess = None
        self.kill_nine_time = None
        self.deactivate()
      else:
        self.activate()
    else:
      self.deactivate()

  def error(self, text):
    md = gtk.MessageDialog(self, 
        gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_ERROR, 
        gtk.BUTTONS_CLOSE, text)
    md.run()
    md.destroy()

  def quit(self, widget):
    if self.subprocess is not None:
      self.subprocess.terminate()
      time.sleep(REFRESH_AFTER_KILL_MILLIS)
      if self.subprocess.poll() is not None:
        self.subprocess.kill()
    sys.exit(0)

  def main(self):
    gtk.timeout_add(FREQUENCY_MILLIS, self.periodic)
    gtk.main()

def parse_args():
  parser = argparse.ArgumentParser(description='monitor a pre-configured process')
  parser.add_argument('--officon', help='icon to use when disabled', default="security-low")
  parser.add_argument('--onicon', help='icon to use when enabled', default="security-high")
  parser.add_argument('cmd', help='command to run', nargs='+')
  args = parser.parse_args()
  return args
      
if __name__ == "__main__":
  logging.basicConfig(level=logging.INFO)

  args = parse_args()
  indicator = Indicator(args)
  indicator.main()
