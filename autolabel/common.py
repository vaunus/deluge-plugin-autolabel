# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 Vaughan Reid <vaunus@gmail.com>
#
# This file is part of AutoLabel and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

"""
Common utilities for the AutoLabel plugin.
"""

from __future__ import unicode_literals

import os.path

from pkg_resources import resource_filename


def get_resource(filename):
    """Get the path to a resource file in the data directory.

    Args:
        filename: The name of the resource file.

    Returns:
        The full path to the resource file.
    """
    return resource_filename(__package__, os.path.join('data', filename))
