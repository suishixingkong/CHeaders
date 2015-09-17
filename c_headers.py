import os
import re
import copy
import glob

import sublime
import sublime_plugin


def _load_settings():
    return sublime.load_settings("C-headers.sublime-settings")


def _get_paths():
    return _load_settings().get("PATHS_HEADERS")


class CompleteCHeadersCommand(sublime_plugin.EventListener):

    def __init__(self):
        sublime_plugin.EventListener.__init__(self)
        self._settings_paths = _get_paths()
        self._paths = copy.deepcopy(self._settings_paths)

    @staticmethod
    def _parse_response():
        return ("_caption", "_result")

    def on_query_context(self, view, key, operator, operand, match_all):
        pass

    def on_query_completions(self, view, prefix, location):
        result = []
        include_wrapper_files = "#include <%s>"
        include_wrapper_dirs = "#include <%s/"
        regex = r"(\.(c|cp{2}|c{2}|c\+{2}|cx{2}|C|CP{2}|cp))$"
        file_name = view.name() or view.file_name()
        substr = ""

        if re.search(regex, file_name):

            for x in range(location[0]):
                subs = view.substr(
                    sublime.Region(location[0] - (x + 1), location[0]))
                if subs.startswith(">\n"):
                    substr = view.substr(
                        sublime.Region(location[0] - ((x + 1) - len(">\n")),
                                       location[0]))
                    break

            rx = re.search(r"(\w+(-*\.*\w+/*|/\w+)*(?=/))", substr)

            if rx:
                for i, _p in enumerate(self._settings_paths):
                    self._paths[i] = _p + substr[rx.start():rx.end()] + '/'
            else:
                self._paths = []
                for _p in self._settings_paths:
                    self._paths.append(_p)

            print(self._paths, prefix, substr)
            for path in self._paths:
                _glob_result = glob.glob(path + prefix + "*")
                if _glob_result:
                    for item in _glob_result:
                        if item.replace(path, "").startswith(prefix):
                            if os.path.isdir(item):
                                for _p in self._settings_paths:
                                    if _p in item:
                                        _caption = item.replace(
                                            _p, "")
                                        break
                                _result = copy.deepcopy(_caption)
                                if "#include" not in substr:
                                    _result = include_wrapper_dirs % _result
                                if not _result.endswith("/"):
                                    _result = _result + "/"
                                _caption += "\tdirectory"
                                result.append((_caption,
                                               _result))
                            elif os.path.isfile(item):
                                for _p in self._settings_paths:
                                    if _p in item:
                                        _caption = item.replace(
                                            _p, "") + "\tmodule"
                                        break
                                _i = item.replace(path, "")

                                if "include" not in _i and \
                                        "include" not in substr:
                                    _i = include_wrapper_files % _i

                                if not _i.endswith(">") and \
                                        not substr.endswith(">"):
                                    _i += ">"

                                result.append((_caption, _i))

        return result
