#!/usr/bin/python env
'''This module contains symbolic implementations of VEX operations.'''

import z3
import re
import sys
import symbolic_irexpr

import logging
l = logging.getLogger("symbolic_irop")
l.setLevel(logging.DEBUG)

##########################
### Generic operations ###
##########################

def generic_Sub(args, size, state):
	#l.debug("OP: %s - %s" % (args[0], args[1]))
	return args[0] - args[1]

def generic_Add(args, size, state):
	#l.debug("OP: %s - %s" % (args[0], args[1]))
	return args[0] + args[1]

def generic_narrow(args, from_size, to_size, part, state):
	if part == "":
		to_start = 0
	elif part == "HI":
		to_start = from_size / 2

	n = z3.Extract(to_start + to_size - 1, to_start, args[0])
	l.debug("Narrowed expression: %s" % n)
	return n

def generic_widen(args, from_size, to_size, signed, state):
	if signed == "U":
		return z3.ZeroExt(to_size - from_size, args[0])
	elif signed == "S":
		return z3.SignExt(to_size - from_size, args[0])

def generic_concat(args, state):
	return z3.Concat(args)

###########################
### Specific operations ###
###########################

op_handlers = { }

##################
### Op Handler ###
##################
def translate(op, args, state):
	symbolic_args = [ symbolic_irexpr.translate(a, state) for a in args ]

	# specific ops
	if op in op_handlers:
		l.debug("Calling %s" % op_handlers)
		constraints = op_handlers[op](symbolic_args, state)
		l.debug("Generated constraints: %s" % constraints)
		return constraints

	# widening
	m = re.match("Iop_(\d+)(S|U)to(\d+)", op)
	if m:
		f = m.group(1)
		s = m.group(2)
		t = m.group(3)
		l.debug("Calling generic_widen(args, %s, %s, '%s', state) for %s" % (f, t, s, op))
		return generic_widen(symbolic_args, int(f), int(t), s, state)

	# narrowing
	m = re.match("Iop_(\d+)(HI|)to(\d+)", op)
	if m:
		f = m.group(1)
		p = m.group(2)
		t = m.group(3)
		l.debug("Calling generic_narrow(args, %s, %s, '%s', state) for %s" % (f, t, p, op))
		return generic_narrow(symbolic_args, int(f), int(t), p, state)

	# concatenation
	m = re.match("Iop_(\d+)HLto(\d+)", op)
	if m:
		l.debug("Calling generic_concat(args, state) for %s" % (op))
		return generic_concat(symbolic_args, state)

	# other generic ops
	m = re.match("Iop_(\D+)(\d+)", op)
	if m:
		name = m.group(1)
		size = int(m.group(2))

		func_name = "generic_" + name
		l.debug("Calling %s" % func_name)
		if hasattr(sys.modules[__name__], func_name):
			constraints = getattr(sys.modules[__name__], func_name)(symbolic_args, size, state)
			l.debug("Generated constraints: %s" % constraints)
			return constraints

	raise Exception("Unsupported operation: %s" % op)