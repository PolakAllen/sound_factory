#!/usr/bin/python3

import os
import yaml
import itertools as it
import argparse

from sound_factory import record_sounds

class readable_dir(argparse.Action):
  def __call__(self,parser, namespace, values, option_string=None):
    prospective_dir=values
    if not os.path.isdir(prospective_dir):
      raise argparse.ArgumentTypeError("readable_dir:{0} is not a valid path".format(prospective_dir))
    if os.access(prospective_dir, os.R_OK):
      setattr(namespace,self.dest,prospective_dir)
    else:
      raise argparse.ArgumentTypeError("readable_dir:{0} is not a readable dir".format(prospective_dir))

class yaml_str(argparse.Action):
  def __call__(self, parser, namespace, values, option_string=None):
    setattr(namespace, self.dest, yaml.load(values))

class yaml_file(argparse.Action):
  def __call__(self, parser, namespace, filename, option_string=None):
    yaml_text = None
    if not os.path.isfile(filename):
      raise argparse.ArgumentTypeError("yaml_file:{} not found".format(filename))
    try:
      with open(filename, 'r') as f:
        yaml_text = f.read()
    except:
      raise argparse.ArgumentTypeError("yaml_file:failed to read {}".format(filename))
    setattr(namespace, self.dest, yaml.load(yaml_text))

parser = argparse.ArgumentParser(add_help=True, prefix_chars='-', description='Sound recording software helper')
parser.add_argument('source', action=yaml_file, help="Source file for description and name of sounds to be recorded")
"""
Recursive Accumlator Map
  Definition occurs in two parts, one part to specify the navigation format, another part to specify accumlation
    walk: {<input_attr>:{...}}
    transform: {<output_attr>:<input_attr>}
  The walk is defined as an ordered map, which will walk to its lowest depth first
  The transform specifies which output attributes correspond to the input attributes
    Transformations are only done on child-less nodes
    If the transformed node completly missing a required output attribute, its output is supressed
    Note: if walk defined a parent node but an instance of it has no children, we'll attempt to transform the parent node
  Input attribute resolution is context dependant. 
    The input attribute will look at the current node for the attribute value.
    If it is not found at the current node, the parent will be checked (and so on)
"""
parser.add_argument('--walk', '-w', action=yaml_str, help="How the transformation of the source file should be performed")
parser.add_argument('--transform', '-t', action=yaml_str, help="Transformation to read source file")
parser.add_argument('--check', '-c', action="store_true", help="Check already defined sounds")
parser.add_argument('--directory', '-d', action=readable_dir, default=os.getcwd(), help="Directory to record sounds to")
parser.add_argument('--debug',  action="store_true", help="Debug print")
parser.add_argument('--dryrun',  action="store_true", help="Don't record anything, just print")
args = parser.parse_args()

def debug(*varargs):
  if args.debug or args.dryrun:
    print(*varargs)

def do_transform(source, transform, parents=[], required_output=set()):
  output = {}
  for output_key,input_key in transform.items():
    if not isinstance(input_key, list):
      input_key = [input_key]
    try:
      for s in [source] + parents:
        if output_key in output: break
        for k in input_key:
          if s.get(k, None):
            output[output_key] = s.get(k, None)
            break
    except StopIteration:
      pass
  for key in required_output:
    if not key in output:
      raise ValueError("Required attribute {} not found".format(output_key))
  debug("transform", source, [list(p.keys()) for p in parents], "->", output)
  return output

def walk_transform(walk, transform, source, required_output=set(), parents=[]):
  did_sub_walk = False
  output = []
  if isinstance(source, list):
    for v in source:
      output += walk_transform(walk, transform, v, required_output, parents)
  if isinstance(source, dict):
    if walk:
      for k in walk:
        if k in source:
          output += walk_transform(walk[k], transform, source[k], required_output, parents + [source])
          did_sub_walk = True
    if not did_sub_walk:
      if transform:
        try:
          output.append(do_transform(source, transform, parents + [source], required_output))
        except ValueError:
          pass # supress any objects with missing required attributes
      else:
        output.append(source)
  return output
    
sounds = walk_transform(args.walk, args.transform, args.source)
debug("sounds after transformation", sounds)
if not args.dryrun:
  record_sounds(sounds, args.directory, vars(args))
