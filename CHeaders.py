import os
import re
import copy
import glob

import sublime
import sublime_plugin

SETTINGS_FILE = 'CHeaders.sublime-settings'
settings = {}


class LoadPluginCommand(sublime_plugin.WindowCommand):

    def run(self, **kwargs):
        sublime.status_message(kwargs.get("message"))
        sublime_plugin.reload_plugin(__name__)


class CompleteCHeaders(sublime_plugin.EventListener):

    def __init__(self):
        sublime_plugin.EventListener.__init__(self)

        # loading settings
        self._settings_paths = settings.get("PATHS_HEADERS", [])
        if not self._settings_paths:
            _settings = self._view.settings()
            self._settings_paths = _settings.get("PATHS_HEADERS", [])
        self._paths = copy.deepcopy(self._settings_paths)

        # include wrappers
        self._include_wrapper_files = "#include <%s>"
        self._include_wrapper_dirs = "#include <%s/"

        self._cpp_libs = []
        self._cpp_paths = []
        self._cpp_versions = ["4.9", "4.8", "4.7"]

        if sublime.platform() == "linux":
            for _p in self._paths:
                for v in self._cpp_versions:
                    if os.path.exists(_p + "c++/" + v):
                        for _f in glob.glob(_p + "c++/" + v + "/*"):
                            if os.path.isdir(_f):
                                _caption = _f.rsplit("/", 1)[1]
                                _r = self._include_wrapper_dirs % _caption
                                self._cpp_libs.append(
                                    (_caption + "\tdirectory", _r)
                                )
                            elif os.path.isfile(_f):
                                _caption = _f.rsplit("/", 1)[1]
                                _r = self._include_wrapper_files % _caption
                                self._cpp_libs.append(
                                    (_caption + "\tmodule", _r)
                                )
                    break

    @property
    def _view(self):
        return self._window.active_view()

    @property
    def _window(self):
        return sublime.active_window()

    @staticmethod
    def _parse_response():
        return ("_caption", "_result")

    @staticmethod
    def _find_substring(viewsubstr, location):
        pass

    def on_query_context(self, view, key, operator, operand, match_all):
        pass

    def on_query_completions(self, view, prefix, location):
        result = []
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

            for _p in self._settings_paths:
                if _p in self._paths:
                    result += self._cpp_libs
                    break

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
                                    _result = self._include_wrapper_dirs % _result
                                if not _result.endswith("/"):
                                    _result = _result + "/"
                                _caption += "\tdirectory"
                                result.append((_caption,
                                               _result))
                            elif os.path.isfile(item):
                                _caption = item.replace(path, "") + "\tmodule"
                                _i = item.replace(path, "")

                                if "include" not in _i and \
                                        "include" not in substr:
                                    _i = self._include_wrapper_files % _i

                                if not _i.endswith(">") and \
                                        not substr.endswith(">"):
                                    _i += ">"

                                result.append((_caption, _i))

        return result


def plugin_loaded():
    global settings
    settings = sublime.load_settings(SETTINGS_FILE)

plugin_loaded()
