#!/usr/bin/env python
# -*- coding: utf-8 -*-

from gi.repository import Gtk, GdkPixbuf, Gdk, GLib, GObject
import os, sys

import pyMorphoILV
import pyHIDvcom

from Queue import Queue
import threading

import wsq
import nfiq

#TODO: WARNING Its not possible to use both readers at the same time using threads and Queue as implemented now

#Comment the first line and uncomment the second before installing
#or making the tarball (alternatively, use project variables)
UI_FILE = "pyFprintBench.ui"
#UI_FILE = "/usr/local/share/testcalc/ui/pyBioTimeRec.ui"
def exit_handler():
  print 'My application is ending!'
  GUI.end()
  sys.exit(0)

class GUI:
  def __init__(self):
    self.builder = Gtk.Builder()
    self.builder.add_from_file(UI_FILE)
    self.builder.connect_signals(self)
    window = self.builder.get_object('vPrincipal')
    self.builder.get_object('bCaptureMorpho').connect("clicked", self.capture)
    self.builder.get_object('bCaptureHID').connect("clicked", self.capture)
#    window.connect("key-press-event", self.keyIn)

    self.morph = pyMorphoILV.Terminal()
    self.hid = pyHIDvcom.Terminal()
    self.readThread = None

    window.set_name('Fingerprint reader benchmarking')
    window.show_all()

  def capture(self, widget):
    print "Captura Solicitada"
    brand = Gtk.Buildable.get_name(widget).replace('bCapture','') # widget.get_name resturn default name
    if brand   == 'Morpho':
      self.fprintReader = self.morph
    elif brand == 'HID':
      self.fprintReader = self.hid
    else:
      print "Unknown fingerprint reader brand"
      return
    q = Queue()
    self.readThread = threading.Thread(target=self.lectorScanner, args=(q,brand))
    self.readThread.start()
    self.fprintReader.startRead(q)
    self.fprintReader.getFingerPrint()

  def keyIn(self, widget, event):
    keyname = Gdk.keyval_name(event.keyval)
    print "Key %s (%d) was pressed" % (keyname, event.keyval)
    print "Key %s" % unicode(Gdk.keyval_to_unicode(event.keyval))
    self.evaluarInput(keyname)

  def on_window_destroy(self, window):
    self.terminarLectura()
    print 'Terminando GUI'
    Gtk.main_quit()

  def show_fingerprint(self, data, target):
    imagen = []
    w = data['data']['colNumber']
    h = data['data']['rowNumber']
    for byte in data['data']['huella']:
      byte = ord(byte)
      if byte<240:
        alfa = 255
      else:
        alfa = 0
#      alfa = 255
#      imagen.extend([255-byte,255-byte,255-byte, alfa])
      imagen.extend([byte,byte,byte, alfa])
    pixbuf = GdkPixbuf.Pixbuf.new_from_data(imagen, GdkPixbuf.Colorspace.RGB, True, 8, w, h, w*4, None, None)
#    if data['data']['rowNumber']<316:
#      pixbuf = pixbuf.scale_simple(416, 416, 2)

#    result =  nfiq.comp_nfiq(data['data']['huella'], w,  h, 8, 500)
#    quality = result[1]
#    self.builder.get_object('pbQuality'+brand).set_text(str(quality));
#    self.builder.get_object('pbQuality'+brand).set_fraction((5-quality)/4.0);
#    self.builder.get_object('pbQualityMorpho').set_fraction((5-quality)/4.0);
#    print "Huella %dx%d: calidad %d"%(data['data']['colNumber'], data['data']['rowNumber'], quality)

    target.set_from_pixbuf(pixbuf)

  def lectorScanner(self, in_q, brand):
    t = threading.currentThread()
    while getattr(t, "do_run", True):
      if not in_q.empty():
        data = in_q.get()
        if data is not None:
          self.processResponse(data, brand)

  def terminarLectura(self):
    print 'Terminando FingerPrint Scanner'
    if self.readThread != None:
      self.fprintReader.close()
      self.readThread.do_run = False
      self.readThread.join()
      self.readThread = None

  def processResponse(self, data, brand):
    print '\n\n--------------------------------------------------------\n\n'
    tarea = ""
    depth = 8
    ppi = 500
    print data['status']
    if data['status'] == 'huellaf' or data['status'] == 'huella':
#    if data['status'] == 'huella':
      target = self.builder.get_object('fprint'+brand)
      GLib.idle_add(self.show_fingerprint, data, target)
      GLib.idle_add(self.show_fingerprint, data, target)
      
      result =  nfiq.comp_nfiq(data['data']['huella'], data['data']['colNumber'],  data['data']['rowNumber'], depth, ppi)
      quality = result[1]
      self.builder.get_object('pbQuality'+brand).set_text(str(quality));
      self.builder.get_object('pbQuality'+brand).set_fraction((5-quality)/4.0);
      print "Huella %dx%d: calidad %d"%(data['data']['colNumber'], data['data']['rowNumber'], quality)
      
    if data['status'] == 'huellaf':
      encoded = ""
      length = 0
      bitrate = 2.25
      
      '''
      encoded = wsq.wsq_encode_mem(bitrate, data['data']['huella'],  data['data']['colNumber'],  data['data']['rowNumber'], depth, ppi, "")
      print "Resultado wsq: "encoded[1]

      slef.terminarLectura()

      #------
      import requests
      import base64
      import json

      SERVER = 'http://10.243.65.180:8091/digiscanGateway/'
      huella64 = base64.b64encode(data['data']['huella'])
      data = {'Pi_expediente': expediente, 'Pi_ubicacion': 'home', 'Ps_huella':huella64}
      response = sesion.post(SERVER+'validarHuella.php', data=json.dumps(data))
      respuesta = response.json()
      print '\n\n********************* Validación de huella *************************\n\n'
      if respuesta['respuesta']:
        print 'Verificación exitosa!!'
      else:
        print 'Falló: ', respuesta['descError']
      print '\n\n******************************************************************\n\n'
      '''
    print '\n\n--------------------------------------------------------\n\n'

def main():
  GObject.threads_init()
  app = GUI()
  Gtk.main()
		
if __name__ == "__main__":
  sys.exit(main())

