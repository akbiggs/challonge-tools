#!/usr/bin/env python


"""Various utility functions that aren't related to Challonge things."""


import argparse


def str_to_bool(s):
  """Converts a string value to a boolean value.

  Args:
    s: The string to convert to a boolean value.

  Raises:
    argparse.ArgumentTypeError: If the string doesn't correspond to a bool.

  Returns:
    The corresponding boolean value for the string.
  """
  if s.lower() in ('yes', 'true', 't', 'y', '1'):
    return True
  elif s.lower() in ('no', 'false', 'f', 'n', '0'):
    return False
  else:
    raise argparse.ArgumentTypeError('Boolean value expected.')


def prompt_yes_no(prompt):
  """Prompts the user to respond yes/no to a question.
  
  Asks repeatedly until valid input is given.

  Args:
    prompt: The prompt to use. This should not include "[y/n]".

  Returns:
    True if the user answered yes, False if they answered yes.
  """
  while True:
    print (prompt + " [y/n]"),

    choice = raw_input().lower()
    try:
      return str_to_bool(choice)
    except argparse.ArgumentTypeError:
      print "Invalid response. Please say 'y' or 'n'."

