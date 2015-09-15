import os
import re

try:
    import thrading
except ImportError:
    pass

import sublime
import sublime_plugin


CACHE_HEADERS = {}


def _load_settings():
    return sublime.load_settings("C-headers.sublime-settings")


def _get_paths():
    return _load_settings().get("PATHS_HEADERS")


class CHeaderCompleteCommand(sublime_plugin.EventListener):

    def on_query_completions(self, view, prefix, location):
        result = []
        regex = r"(\.(c|cpp|cc|c\+\+|cxx|C|CPP|cp))$"

        if view.name():
            file_name = view.name()
        else:
            file_name = view.file_name()

        if re.search(regex, file_name):
            for _p in _get_paths():
                for _path, _, _files in os.walk(_p):
                    for _file in _files:
                        if os.path.exists(_path + "/" + _file):
                            path = _path + '/' + _file
                        if os.path.exists(_p + _file):
                            path = _p + _file
                        path = path.replace(_p, "")
                        if prefix == "include <":
                            result.append((path, path + ">"))
                        if path.startswith(prefix):
                            result.append(
                                (path, "#include <" + path + ">"))

        return result
