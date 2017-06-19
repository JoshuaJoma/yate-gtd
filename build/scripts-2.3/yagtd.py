#!/usr/bin/python -O
# -*- coding: ISO-8859-15 -*-
#
# To-do list manager.
# Copyright (C) 2006-2007 MiKael NAVARRO
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

"""yaGTD
Copyright (C) 2006-2007 MiKael NAVARRO

A primitive Getting Things Done to-do list manager.
Cmd version: line oriented command interpreters.

"""

# Specific variables for pydoc
__author__ = "MiKael Navarro <klnavarro@gmail.com>"
__date__ = "Wed Jan 03 2007"
__version__ = "0.1.6"

# Include directives
import os
import sys
import errno
import re
import datetime
from math import sqrt, log

import cmd

if __debug__: from pprint import pprint as pp

from gtd import Task, ToDo
import gtd

# Global variables
TODO_DIR    = "."
TODO_TXT    = TODO_DIR + "/todo.txt"
TODO_REST   = TODO_DIR + "/todo.rest"
TODO_TMP    = TODO_DIR + "/todo.tmp"
REPORT_TXT  = TODO_DIR + "/report.txt"
DONE_TXT    = TODO_DIR + "/done.txt"

# Colorization
COLOR_CODES = ( { 'none': "",
                  'default': "\033[0m",
                  # primary colors
                  'black': "\033[0;30m",
                  'grey': "\033[0;37m",
                  'red': "\033[0;31m",
                  'green': "\033[0;32m",
                  'blue': "\033[0;34m",
                  'purple': "\033[0;35m",
                  'cyan': "\033[0;36m",
                  'yellow': "\033[0;33m",
                  # bold colors
                  'white': "\033[1;37m",
                  'dark_grey': "\033[1;30m",
                  'dark_red': "\033[1;31m",
                  'dark_green': "\033[1;32m",
                  'dark_blue': "\033[1;34m",
                  'dark_purple': "\033[1;35m",
                  'dark_cyan': "\033[1;36m",
                  'dark_yellow': "\033[1;33m",
                  # other colors                  
                  'normal': "\x1b[0;37;40m",
                  'title': "\x1b[1;32;40m",
                  'heading': "\x1b[1;35;40m",
                  'bold': "\x1b[1;35;40m",
                  'important': "\x1b[1;31;40m",
                  'error': "\x1b[1;31;40m",
                  'reverse': "\x1b[0;7m",
                  'row0': "\x1b[0;35;40m",
                  'row1': "\x1b[0;36;40m" } )

# Default colors
DEFAULT_COLOR = COLOR_CODES['default']
CONTEXT_COLOR   = COLOR_CODES['dark_yellow']
PROJECT_COLOR   = COLOR_CODES['dark_purple']
STATUS_COLOR    = COLOR_CODES['dark_green']
REFERENCE_COLOR = COLOR_CODES['dark_blue']
URGENCY_COLOR    = COLOR_CODES['red']
IMPORTANCE_COLOR = COLOR_CODES['red']
COMPLETE_COLOR   = COLOR_CODES['white']
TIME_COLOR       = COLOR_CODES['cyan']
RECURRENCE_COLOR = COLOR_CODES['cyan']
START_COLOR      = COLOR_CODES['red']
DUE_COLOR        = COLOR_CODES['red']
END_COLOR        = COLOR_CODES['green']

# Regexps for parsing a task line
CONTEXT_CHAR   = "@"
PROJECT_CHAR   = "p:"
STATUS_CHAR    = "!"
REFERENCE_CHAR = "ref:"
URGENCY_CHAR    = "U:"
IMPORTANCE_CHAR = "I:"
COMPLETE_CHAR   = "C:"
TIME_CHAR       = "T:"
RECURRENCE_CHAR = "R:"
START_CHAR      = "S:"
DUE_CHAR        = "D:"
END_CHAR        = "E:"

WORD_MATCH      = r"(\w+)"
DIGIT_MATCH     = r"(\d+)"
DATE_MATCH      = r"(\d\d\d\d-\d\d-\d\d)"
TIMEDELTA_MATCH = r"(\d+)([WDHM])"

CONTEXT_REGEXP   = re.compile(CONTEXT_CHAR + WORD_MATCH, re.IGNORECASE)
PROJECT_REGEXP   = re.compile(PROJECT_CHAR + WORD_MATCH, re.IGNORECASE)
STATUS_REGEXP    = re.compile(STATUS_CHAR + WORD_MATCH, re.IGNORECASE)
REFERENCE_REGEXP = re.compile(REFERENCE_CHAR + WORD_MATCH, re.IGNORECASE)
URGENCY_REGEXP   = re.compile(URGENCY_CHAR + DIGIT_MATCH, re.IGNORECASE)
IMPORTANCE_REGEXP = re.compile(IMPORTANCE_CHAR + DIGIT_MATCH, re.IGNORECASE)
COMPLETE_REGEXP   = re.compile(COMPLETE_CHAR + DIGIT_MATCH, re.IGNORECASE)
TIME_REGEXP       = re.compile(TIME_CHAR + TIMEDELTA_MATCH, re.IGNORECASE)
RECURRENCE_REGEXP = re.compile(RECURRENCE_CHAR + TIMEDELTA_MATCH, re.IGNORECASE)
START_REGEXP      = re.compile(START_CHAR + DATE_MATCH, re.IGNORECASE)
DUE_REGEXP        = re.compile(DUE_CHAR + DATE_MATCH, re.IGNORECASE)
END_REGEXP        = re.compile(END_CHAR + DATE_MATCH, re.IGNORECASE)


#
# Main GTD class.
#
class GTD(cmd.Cmd):
    """GTD(cmd.Cmd) class."""

    def __init__(self):
        cmd.Cmd.__init__(self)
        self.intro= """
  yaGTD is a free software available under the terms of the GNU GPL.
  Refer to the file COPYING (which should be included in this distribution)
  for the specific terms of this licence.
  """
        self.prompt = "GTD> "
        self.todo = ToDo()  # the to-do list is here!

        self.colorize = False

    #
    # Private functions.
    #

    def _parse_args(self, args):
        """Parse command arguments= num + str."""

        num = string = None
        
        # Parse command args
        n = re.search(r"^(?x)(\d+)", args)  # num
        s = re.search(r" +([@!:\-\w ]+)$", args)  # string

        if n: num = int(n.group(1))
        if s: string = s.group(1)

        #print "parsed", num, string
        return (num, string)

    def _colorize(self, string):
        """Colorize the given 'string'."""

        s = string

        if self.colorize:
            # Scan to colorize attributes (accordingly to global settings) ...
            for attr in Task.attributes_list[3:]:
                color_fct = lambda m: eval(attr.upper() + '_COLOR') + m.group(0) + DEFAULT_COLOR
                s = eval(attr.upper() + '_REGEXP').sub(color_fct, s)

        return s

    def _parse_line(self, line):
        """Return a dictionary (task mapping) from 'line' parsing."""

        t = {}  # Task mapping
        title = line  # the 'title' extracted from line

        # Parse for GTD attributes
        for attr in ['context', 'project', 'status', 'reference']:
            title = eval(attr.upper() + '_REGEXP').sub('', title)

            matches = eval(attr.upper() + '_REGEXP').findall(line)
            if matches:
                t[attr] = matches

        # Parse additional properties
        for attr in ['urgency', 'importance', 'complete']:
            title = eval(attr.upper() + '_REGEXP').sub('', title)

            matches = eval(attr.upper() + '_REGEXP').findall(line)
            if matches:
                t[attr] = int(matches[-1])  # keep only last!

        # Parse timedelta
        for attr in ['time', 'recurrence']:
            title = eval(attr.upper() + '_REGEXP').sub('', title)

            matches = eval(attr.upper() + '_REGEXP').findall(line)
            if matches:
                match = matches[-1]  # keep only last!
                hours = minutes = 0  # compute hours

                if attr == 'time':  # compute time requiered (in working hours)
                    if match[1].upper() == 'W':  # weeks
                        hours = int(match[0]) * gtd.WEEK_IN_HOURS
                    elif match[1].upper() == 'D':  # days
                        hours = int(match[0]) * gtd.DAY_IN_HOURS
                    elif match[1].upper() == 'H':  # hours
                        hours = int(match[0])
                    elif match[1].upper() == 'M':  # minutes
                        minutes = int(match[0])
                    else:
                        pass  # invalid time range indicator
                    
                elif attr == 'recurrence':  # compute full hours
                    if match[1].upper() == 'W':  # weeks
                        hours = int(match[0]) * 7 * 24
                    elif match[1].upper() == 'D':  # days
                        hours = int(match[0]) * 24
                    elif match[1].upper() == 'H':  # hours
                        hours = int(match[0])
                    elif match[1].upper() == 'M':  # minutes
                        minutes = int(match[0])
                    else:
                        pass  # invalid time range indicator

                t[attr] = datetime.timedelta(hours= hours, minutes=minutes)
        
        # Parse dates
        for attr in ['start', 'due', 'end']:
            title = eval(attr.upper() + '_REGEXP').sub('', title)

            matches = eval(attr.upper() + '_REGEXP').findall(line)
            if matches:
                year, month, day = matches[-1].split('-')  # keep only last!
                t[attr] = datetime.datetime(int(year), int(month), int(day))

        # Post-processing
        if t.has_key('end') or t.has_key('reference'):  # ignore completed and archived tasks
            t['complete'] = 100
            
        # Set the title
        t['title'] = " ".join(title.split())  # remove useless blank chars too
        
        return t
            
    def _dump_line(self, task):
        """Return a formatted line from the given 'task'."""

        s = task['title']  # init the line with the title
            
        # Dump GTD attributes
        for attr in ['context', 'project', 'status', 'reference']:
            if task.has_key(attr):
                for value in task[attr]:
                    s += " " + eval(attr.upper() + '_CHAR') + value
            
        # Dump additional properties
        for attr in ['urgency', 'importance', 'complete']:
            if task.has_key(attr) and task[attr]:
                s += " " + eval(attr.upper() + '_CHAR') + str(task[attr])

        # Parse timedelta
        for attr in ['time', 'recurrence']:
            if task.has_key(attr) and task[attr]:
                hours = task[attr].days * 24 + task[attr].seconds / 3600
                if hours > 0:
                    s += " " + eval(attr.upper() + '_CHAR') + str(hours) + "H"
                else:  # less than 1 hour!
                    minutes = task[attr].seconds / 60
                    s += " " + eval(attr.upper() + '_CHAR') + str(minutes) + "M"

        # Parse dates
        for attr in ['start', 'due', 'end']:
            if task.has_key(attr) and task[attr]:
                s += " " + eval(attr.upper() + '_CHAR') + task[attr].strftime("%Y-%m-%d")
            
        return s

    def _disp(self, task):
        """Display the 'id' and a summary of the 'task'."""

        task_line = task['title']
        if __debug__:
            task_line = self._dump_line(task)

        id_str = "%3d:" % task['id']
        if __debug__:
            id_str = "%3d:(%f)" % (task['id'], task.priority())
        if self.colorize:  # colorize #id
            id_str = COLOR_CODES['cyan'] + id_str + DEFAULT_COLOR
        
        return "%s %s" % (id_str, self._colorize(task_line))

    def _show(self, task):
        """Display details of the given 'task'."""
        
        s = ""
        for attrib in Task.attributes_list[1:]:
            if task.has_key(attrib) and task[attrib]:
                if s: s = s + "\n"
                s = s + attrib.capitalize() + ": "
                s = s + str(task[attrib])
        return s

    #
    # Edition
    #

    def do_add(self, line):
        """Add a new task (from the input line)."""

        if line:
            # Create the new task
            task = Task()
            
            # Parse input line for GTD and additional attributes
            task.add(**self._parse_line(line))

            # And, add it to the to-do list
            task_id = self.todo.add(task)

            # And, set the start date
            self.do_append("%d S:%s" % (task_id, datetime.datetime.now().strftime("%Y-%m-%d")))

    def do_del(self, id):
        """Delete task given by #id."""

        # Parse command line
        idx = self._parse_args(id)[0]

        if idx:
            self.todo.supp(idx)

    do_rm = do_del

    def do_close(self, id):
        """Close the given task (#id)."""

        # Parse command line
        idx = self._parse_args(id)[0]

        if idx:
            # First, we need to find the task
            task = self.todo.find('id', idx)
            if task:
                if task['recurrence']:
                    task['start'] = task['due']  # reinit start date
                    task['due'] = task['start'] + task['recurrence']
                else:
                    task['end'] = datetime.datetime.now()
                    task['complete'] = 100

    do_done = do_close

    def do_replace(self, id_line):
        """Replace the entire task #id by a new one (line)."""

        # Parse command line
        idx, line = self._parse_args(id_line)

        if idx and line:
        
            # Frist, we need to find the task
            task = self.todo.find('id', idx)
            if task:
                i = self.todo.index(task)
                
                task = Task()  # create a new task
                
                # Parse input line for GTD and additional attributes
                task.add(**self._parse_line(line))
                task.add(id=idx)

                # And, replace it into the to-do list
                self.todo[i] = task

    do_sub = do_replace

    def do_extend(self, id_desc):
        """Add more text (description) to task #id."""

        # Parse command line
        idx, desc = self._parse_args(id_desc)

        if idx and desc:
            print "Not Yet Implemented!"

    do_notes = do_extend

    def do_append(self, id_line):
        """Add new elements (line) to task #id but leave existing elemenents unchanged.""" 

        # Parse command line
        idx, line = self._parse_args(id_line)
        
        if idx and line:
            # Frist, we need to find the task
            task = self.todo.find('id', idx)
            if task:
                # Parse additional input line
                attrs = self._parse_line(line)
            
                # Then, modify the task
                for attr, value in attrs.items():
                    if value and not task[attr]:  # not override!
                        task[attr] = value

    def do_modify(self, id_line):
        """Add/change elements (line) of task #id but leave each other unchanged."""

        # Parse command line
        idx, line = self._parse_args(id_line)

        if idx and line:
            # Frist, we need to find the task
            task = self.todo.find('id', idx)
            if task:
                # Parse additional input line
                attrs = self._parse_line(line)
            
                # Then, modify the task
                for attr, value in attrs.items():
                    if value:  # override!
                        task[attr] = value

    def do_archive(self, line):
        """Archive completed tasks."""

        print "Not Yet Implemented!"

    #
    # Specific GTD commands
    #

    def do_someday(self, id):
        """Mark the given task (#id) as @someday."""

        # Parse command line
        idx = self._parse_args(id)[0]

        if idx:
            self.do_modify("%d %s" % (idx, "@someday"))

    do_maybe = do_someday
        
    def do_waitingfor(self, id):
        """Mark the given task (#id) as @waitingfor."""

        # Parse command line
        idx = self._parse_args(id)[0]

        if idx:
            self.do_modify("%d %s" % (idx, "@waitingfor"))

    def do_ref(self, id_ref):
        """Archive the given task (#id) as Reference."""

        # Parse command line
        idx, reference = self._parse_args(id_ref)

        if idx:
            self.do_append("%d ref:%s" % (idx, reference))

    #
    # Sorted/ordered display.
    #

    def do_listall(self, nb):
        """List #nb tasks (ordered by #id)."""

        # Parse command line
        nb = self._parse_args(nb)[0]

        tasks = self.todo
        if nb:  # display only nb tasks
            tasks = tasks[:nb]

        for t in tasks:
            print self._disp(t)

    do_la = do_listall

    def do_list(self, nb):
        """List #nb open tasks (ordered by #id)."""

        # Parse command line
        nb = self._parse_args(nb)[0]

        tasks = [ t for t in self.todo if t['complete'] < 100 ]  # filter done/close tasks
        if nb:  # display only nb tasks
            tasks = tasks[:nb]

        for t in tasks:
            print self._disp(t)

    do_ls = do_list

    def do_listref(self, nb):
        """List #nb ref tasks (ordered by #id)."""

        # Parse command line
        nb = self._parse_args(nb)[0]

        tasks = [ t for t in self.todo if t.has_key('reference') and t['reference'] ]  # filter ref tasks
        if nb:  # display only nb tasks
            tasks = tasks[:nb]

        for t in tasks:
            print self._disp(t)

    do_lr = do_listref

    def do_show(self, id):
        """Show details of the given task #id."""

        # Parse command line
        idx = self._parse_args(id)[0]

        if idx:
            # Frist, we need to find the task
            task = self.todo.find('id', idx)
            if task:
                print self._show(task)

    def do_sort(self, nb):
        """Sort #nb tasks by priority."""

        # Parse command line
        nb = self._parse_args(nb)[0]

        tasks = [ t for t in self.todo.sort() if t['complete'] < 100 ]
        if nb:  # display only nb tasks
            tasks = tasks[:nb]

        for t in tasks:
            print self._disp(t)

    do_listpri = do_sort
    
    def do_order(self, nb_attr):
        """Order #nb tasks by context/project/status/reference (and priority)."""

        # Parse command line
        nb, attr = self._parse_args(nb_attr)
        
        if not attr or attr not in ['context', 'project', 'status', 'reference']:
            attr = 'context'  # by default order by context

        for c, ts in self.todo.order(attr).items():
            # Section title
            print self._colorize(eval(attr.upper() + '_CHAR') + c.capitalize())

            if attr == 'reference':
                tasks = [ t for t in ts ]  # even if completed!
            else:
                tasks = [ t for t in ts if t['complete'] < 100 ] 
            if nb: tasks = tasks[:nb]  # display only nb tasks
            for t in tasks:
                print self._disp(t)

    def do_status(self, line):
        """Display projects statuses (percent complete)."""

        for p, ts in self.todo.order('project').items():
            # Section title
            print self._colorize(PROJECT_CHAR + p.capitalize()),

            percent = 0  # compute project's percent complete 
            for t in ts:
                if t['complete']:
                    percent += int(t['complete'])
            print "%d%%" % (percent / len(ts))

    do_summary = do_status
            
    #
    # Re-search.
    #

    def do_search(self, regexp):
        """Retrieve tasks matching given regexp."""

        # Rk: improved search function that retrieve regexp
        #     over all tasks attributes

        todos = [ t for t in self.todo.sort() ]  # first sort by priority

        # Then, retrieve the pattern (into full desc tasks)
        expr = re.compile(regexp, re.IGNORECASE)
        tasks = [ t for t in todos if expr.search(self._dump_line(t)) ]

        for t in tasks:
            print self._disp(t)

    #
    # IO functions.
    #

    def do_load(self, todotxt):
        """Load from a todotxt file."""

        try:
            f = open(todotxt, 'r')
            try:
                self.todo.erase()  # clean
                for line in f:
                    #print line,
                    if line.lstrip().startswith('#'): continue
                    self.do_add(line.strip())
            finally:
                f.close()
        except IOError, err:
            # 'file not found' exception?
            if err.errno != errno.ENOENT: raise  # raise all others
            print err  # and continue

    def do_save(self, todotxt):
        """Save to a todotxt file."""

        if todotxt == "": todotxt = TODO_TXT
        try:
            f = open(todotxt, 'w')
            try:
                for t in self.todo:
                    f.write(self._dump_line(t) + "\n")
            finally:
                f.close()
        except IOError, err:
            print err  # and continue

    def do_print(self, rest):
        """Export into printable format (ReST)."""

        if rest == "": rest = TODO_REST
        try:
            f = open(rest, 'w')
            try:
                sys.stdout = f  # a little trick

                # Header
                print "Getting Things Done to-do list manager"
                print "######################################"
                print
                print " ", "; ".join([__author__, __date__, __version__])
                print
                print ".. contents::"
                print

                prt_list = ( { 'name': "context",
                               'title': "contexts",
                               'char': CONTEXT_CHAR },
                             { 'name': "project",
                               'title': "projects",
                               'char': PROJECT_CHAR },
                             { 'name': "status",
                               'title': "statuses",
                               'char': STATUS_CHAR },
                             { 'name': "reference",
                               'title': "references",
                               'char': REFERENCE_CHAR },
                             )

                for attr in prt_list:
                    print attr['title'].capitalize()
                    print "=" * len(attr['title'])
                    print

                    for a, ts in self.todo.order(attr['name']).items():
                        attr_name = attr['char'] + a  # attr (full) name
                        print attr_name.lower()
                        print "-" * len(attr_name)
                        print
                        
                        tasks = [ t for t in ts if t['complete'] < 100 ] 
                        for t in tasks:  # task details
                            print "-", t['title']
                        print
                    else:
                        print ".."
                        print
            finally:
                sys.stdout = sys.__stdout__  # restore stdout
                f.close()

        except IOError, err:
            print err  # and continue
            
    #
    # Quit.
    #
            
    def do_EOF(self, line=None):
        """Quit."""

        print "bye"
        sys.exit()


#
# Main entry point.
#
def main(options):
    """A primitive Getting Things Done to-do list manager.
       Cmd version: line oriented command interpreters."""

    gtd_cmd = GTD()

    if options.todotxt: gtd_cmd.do_load(options.todotxt)
    elif options.todoyaml: gtd_cmd.do_import(options.todoyaml)

    if options.color:
        gtd_cmd.colorize = True

    try:
        # Enter the main cmdloop
        gtd_cmd.cmdloop()
    except KeyboardInterrupt:  # C^c
        print "bye"

    
#
# External entry point.
#
if __name__ == "__main__":
    # Get options
    from optparse import OptionParser, make_option

    option_list = [
        make_option("-c", "--color",
                    action="store_true", dest="color", 
                    default=False,
                    help="activate color highlightment"),
        make_option("-l", "--load",
                    action="store", dest="todotxt", 
                    type="string", default=TODO_TXT,
                    help="todotxt file to load"),
        ]

    parser = OptionParser(usage="python -O %prog [options] ... [args] ...", 
                          version=__version__,
                          description="A primitive Getting Things Done to-do list manager.",
                          option_list=option_list)

    (options, args) = parser.parse_args()

    # Compulsory arguments
    if not options.todotxt and not options.todoyaml:
        print "Missing todo file argument (see --help)!" 
        sys.exit(1)

    # Commands list
    #if __debug__: print "Commands=", args
        
    # Process start here
    main(options)
