#!/usr/bin/env python
#encoding:utf-8
# Adapted from:
#author:dbr/Ben
#project:tvdb_api
#repository:http://github.com/dbr/tvsubtitles_api
#license:unlicense (http://unlicense.org/)

"""Custom exceptions used or raised by tvsubtitles_api
"""

__author__ = "dbr/Ben"
__version__ = "1.5"

__all__ = ["tvsubtitles_error", "tvsubtitles_userabort", "tvsubtitles_shownotfound",
"tvsubtitles_seasonnotfound", "tvsubtitles_episodenotfound","tvsubtitles_languagenotfound", 
"tvsubtitles_attributenotfound"]

class tvsubtitles_exception(Exception):
    """Any exception generated by tvsubtitles_api
    """
    pass

class tvsubtitles_error(tvsubtitles_exception):
    """An error with www.thetvsubtitles.com (Cannot connect, for example)
    """
    pass

class tvsubtitles_shownotfound(tvsubtitles_exception):
    """Show cannot be found on www.thetvsubtitles.com (non-existant show)
    """
    pass

class tvsubtitles_seasonnotfound(tvsubtitles_exception):
    """Season cannot be found on www.thetvsubtitles.com
    """
    pass

class tvsubtitles_episodenotfound(tvsubtitles_exception):
    """Episode cannot be found on www.thetvsubtitles.com
    """
    pass

class tvsubtitles_languagenotfound(tvsubtitles_exception):
    """Language cannot be found on www.thetvsubtitles.com
    """
    pass

class tvsubtitles_attributenotfound(tvsubtitles_exception):
    """Raised if an episode does not have the requested
    attribute (such as a episode name)
    """
    pass
