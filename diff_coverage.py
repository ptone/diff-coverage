#!/usr/bin/env python
# coding: utf-8

"""

    diff-coverage

    This module will, in a somewhat inflexible way, compare a diff coverage.py
    data to determine whether lines added or modified in the diff, were executed
    during a coverage session.

    requires http://python-patch.googlecode.com/svn/trunk/patch.py
    which is included in this package with attribution

"""

from collections import defaultdict
from optparse import OptionParser
import coverage
import django
import logging
import os
import patch
import re
import sys
import webbrowser


django_path = os.path.abspath(os.path.dirname(os.path.dirname(django.__file__)))
coverage_html_dir = os.path.join(os.getcwd(), 'diff_coverage_html')
line_end = '(?:\n|\r\n?)'

patch_logger = logging.getLogger('patch')
patch_logger.addHandler(logging.NullHandler())

# pattern to use to insert new stylesheet
# this is currently pretty brittle - but lighterweight than doing something with
# lxml and/or pyquery
current_style = "<link rel='stylesheet' href='style.css' type='text/css'>"

def parse_patch(patch_file):
    """
    returns a dictionary of {filepath:[lines patched]}
    """
    patch_set = patch.fromfile(patch_file)
    target_files = set()
    target_files.update([os.path.join(django_path, p.target.lstrip('/ab')) for p in patch_set.items])
    target_files = [p for p in target_files if 'test' not in p]
    target_files = [p for p in target_files if 'docs' not in p]
    target_files = [p for p in target_files if os.path.exists(p)]
    target_lines = defaultdict(list)

    for p in patch_set.items:
        source_file = os.path.join(django_path, p.target)
        if source_file not in target_files:
            continue
        source_lines = []
        last_hunk_offset = 1
        for hunk in p.hunks:
            patched_lines = []
            line_offset = hunk.starttgt
            for hline in hunk.text:
                if hline.startswith('-'):
                    continue
                if hline.startswith('+'):
                    patched_lines.append(line_offset)
                line_offset += 1
            target_lines[p.target].extend(patched_lines)
    return target_lines




def generate_css(targets, target_lines):
    coverage_files = os.listdir(coverage_html_dir)

    for target in targets:
        target_name = target.replace('/', '_')
        fname = target_name.replace(".py", ".css")
        html_name = target_name.replace(".py", ".html")
        css = ','.join(["#n%s" %l for l in target_lines[target]])
        css += " {background: red;}"
        css_file = os.path.join(coverage_html_dir, fname)
        with open(css_file, 'w') as f:
            f.write(css)
        html_pattern = re.compile(html_name)
        html_file = [p for p in coverage_files if html_pattern.search(p)]
        if len(html_file) != 1:
            raise ValueError("Found wrong number of matching html files")
        html_file = os.path.join(coverage_html_dir,html_file[0])

        html_source  = open(html_file, 'r').read()
        style_start = html_source.find(current_style)
        new_html = html_source[:style_start]
        new_html += "<link rel='stylesheet' href='%s' type='text/css'>\n" % fname
        new_html += html_source[style_start:]
        os.unlink(html_file)
        with open(html_file, 'w') as f:
            f.write(new_html)




if __name__ == "__main__":
    opt = OptionParser()
    (options, args) = opt.parse_args()
    if not args:
        print "No patch file provided"
        sys.exit(1)
    patchfile = args[0]

    target_lines = parse_patch(patchfile)
    targets = []

    # generate coverage reports
    cov = coverage.coverage(data_file = os.path.join(django_path, 'tests', '.coverage'))
    cov.load()

    for t in target_lines.keys():
        path = os.path.join(django_path, t)
        if not path.endswith('.py'):
            continue
        f, exe, exl, mis, misr = cov.analysis2(path)
        missing_patched = set(mis) & set(target_lines[t])
        if missing_patched:
            targets.append(t)
            target_lines[t] = list(missing_patched)
            missing_lines = ', '.join([str(x) for x in missing_patched])
            print '{} missing: {}'.format(t, missing_lines)


    target_files = [os.path.join(django_path, x) for x in targets]
    cov.html_report(morfs=target_files, directory=coverage_html_dir)

    generate_css(targets, target_lines)

    webbrowser.open(os.path.join(coverage_html_dir, 'index.html'))

