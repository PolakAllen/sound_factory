#!/usr/bin/python3

import os
import re
import yaml
import itertools as it
import argparse

def unwrap(fnOrObject, *args, **kwargs):
  if callable(fnOrObject):
    return fnOrObject(*args, **kwargs)
  else:
    return fnOrObject

def choose_an_option(question, options, action=lambda:None):
  valid_options = range(1, len(options) + 1)
  option_string = question + "\n\n" + "\n".join("{}) {}".format(i,option)
    for i,option in zip(valid_options, options)) + "\n"
  result = None
  while result not in valid_options:
    action()
    try:
      result = int(input(option_string))
    except ValueError:
      result = None
  print("You choose", result)
  return result

""" return true if satisfactory """
def _test_sound(filename):
  def play():
    print("Checking sound {}".format(filename))
    os.system("mpg123 '{}.mp3' > /dev/null 2>&1".format(filename.split('.')[0]))
  result = choose_an_option("What should I do with this sound?", 
    ["Keep it", "Try again", "Skip it"], play)
  if result != 1:
    os.system("rm '{}'.*".format(filename))
  if result == 3:
    raise KeyboardInterrupt
  return result != 1

def _record_sound(filename, description=None, context=None, trim=None, record=None):
  base_name = filename.split('.')[0]
  trimmed_name = base_name + ".trim.wav"
  tmp_name = base_name + ".tmp.wav"
  compressed_name = base_name + ".mp3"
  sound_description = ["Recording sound file '{}'".format(compressed_name)]
  if description:
    sound_description.append("as in '{}'".format(description))
  if context:
    sound_description.append("with context '{}'".format(context))
  print(" ".join(sound_description))
  record_params = record or "-d 5 -f cd"
  trim_params = trim or "silence -l 1 0.3 1% -1 0.5 5%"
  os.system("touch '{}'".format(compressed_name))
  filesize = 0
  supress_output = "" #"> /dev/null "
  while filesize < 600:
    os.system("arecord {0} '{1}' {2} 2>&1".format(record_params, tmp_name, supress_output))
    os.system("sox '{0}' '{1}' {2} {3} 2>&1".format(tmp_name, trimmed_name, trim_params, supress_output))
    os.system("lame -V 1 '{0}' '{1}' {2} 2>&1".format(trimmed_name, compressed_name, supress_output))
    filesize = os.path.getsize(compressed_name)
    print(filesize)
  os.system("rm '{}' '{}' > /dev/null 2>&1".format(tmp_name, trimmed_name))
  
def rerecord_sound(filename, **kwargs):
  def try_again():
    return _test_sound(filename)
  while try_again():
    _record_sound(filename, **kwargs)

def record_new_sound(filename, **kwargs):
  _record_sound(filename, **kwargs)
  rerecord_sound(filename, **kwargs)

def record_sounds(requested, destination='.', options={}):
  for sound in requested:
    filename = sound["filename"].split('.')[0]
    try:
      if filename not in {f.split('.')[0] for f in os.listdir(destination) if os.path.isfile(f)}:
        record_new_sound(**sound)
      elif options.get("check", False):
        rerecord_sound(**sound)
    except KeyboardInterrupt:
      if choose_an_option("Stop recording?", ["yes","no"]) == 1:
        break
