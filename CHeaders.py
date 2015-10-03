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

        if self.is_linux:
            self._settings_paths.append("/usr/include/")
            self._settings_paths.append("/usr/local/include/")
        if self.is_window:

            # cpp windows supported version 4.8.1

            if not os.path.exists("C:\\Mingw"):
                sublime.error_message("You should download Mingw")
            else:
                self._settings_paths.append("C:\\Mingw\\include\\")
                self._settings_paths.append("C:\\MinGW\\mingw32\\include\\")
                self._settings_paths.append("C:\\MinGW\\msys\\1.0\\include\\")
                self._settings_paths.append(
                    "C:\\MinGW\\mingw32\\lib\\gcc\\mingw32\\4.8.1\\include\\")
                self._settings_paths.append(
                    "C:\\MinGW\\mingw32\\lib\\gcc\\mingw32\\4.8.1\\include-fixed\\")

        # this list will contain a copy of self._settings_paths
        self._paths = copy.deepcopy(self._settings_paths)

        # include wrappers
        self._include_wrapper_files = "#include <%s>"
        self._include_wrapper_dirs = "#include <%s/"

        if self.is_linux:

            # looking for c++ headers
            # as iostream, deque, vector, list
            # in linux systems
            self._cpp_gnu_h = {}
            self._cpp_path = "/usr/include/c++/"
            self._cpp_supported_versions = ["4.7", "4.8", "4.9"]
            self._cpp_version = None

            for v in self._cpp_supported_versions:
                if os.path.exists(self._cpp_path + v):
                    self._cpp_version = v
                    break

            for _f in glob.glob(self._cpp_path + self._cpp_version + "/*"):
                self._cpp_gnu_h.update(self._update(_f))

            self._cpp_path += v + os.sep

            # looking for linux gnu headers
            # as sys/socket.h ...
            self._linux_gnu_h = {}
            self._linux_gnu_path = "/usr/include/i386-linux-gnu/"

            for _f in glob.glob(self._linux_gnu_path + "*"):
                self._linux_gnu_h.update(self._update(_f))

        if self.is_window:

            # looking for c++ headers
            self._cpp_windows_h = {}
            self._cpp_path = "C:\\MinGW\\mingw32\\lib\\gcc\\mingw32\\4.8.1\\include\\c++\\"

            for _f in glob.glob(self._cpp_path + "*"):
                self._cpp_windows_h.update(self._update(_f))

    @property
    def is_linux(self):
        return sublime.platform() == "linux"

    @property
    def is_window(self):
        return sublime.platform() == "windows"

    @property
    def _view(self):
        return sublime.active_window().active_view()

    @property
    def _is_main_path(self):
        for _sp in self._settings_paths:
            if _sp in self._paths:
                return True
        return

    @staticmethod
    def _update(file):
        if os.path.isdir(file):
            caption = file.rsplit(os.sep, 1)[1]
            return {caption: "directory"}
        if os.path.isfile(file):
            caption = file.rsplit(os.sep, 1)[1]
            return {caption: "module"}

    @staticmethod
    def _find_substring(view, location):
        for x in range(location):
            _sub = view.substr(sublime.Region(location - (x + 1), location))
            if _sub.startswith(">\n"):
                return view.substr(
                    sublime.Region(location - (x + 1) + len(">\n"),
                                   location)
                )
        return view.substr(
            sublime.Region(0, location)
        )

    def _parse_result(self, substr, header, type):
        _caption = header + '\t' + type
        if type == "directory":
            if "#include" not in substr:
                _r = self._include_wrapper_dirs % header
            else:
                _r = header + "/"
        if type == "module":
            if "#include" not in substr:
                _r = self._include_wrapper_files % header
            else:
                _r = header + ">"

        return _caption, _r

    def on_query_context(self, view, key, operator, operand, match_all):
        pass

    def on_query_completions(self, view, prefix, location):
        result = []
        regex = r"(\.(c|cp{2}|c{2}|c\+{2}|cx{2}|C|CP{2}|cp))$"
        file_name = view.name() or view.file_name()
        substr = ""
        if re.search(regex, file_name):

            substr = self._find_substring(view, location[0])
            rx = re.search(r"(\w+(-*\.*\w+/*|/\w+)*(?=/))", substr)

            if rx:
                self._paths = []
                start = rx.start()
                end = rx.end()

                for _p in self._settings_paths:
                    _f = _p + substr[start:end] + os.sep
                    if os.path.exists(_f):
                        self._paths.append(_f)

                # if is linux
                if self.is_linux:

                    # add cpp linux headers path to self._paths
                    _f = self._cpp_path + substr[start:end] + os.sep
                    if os.path.exists(_f):
                        self._paths.append(_f)

                    # add linux gnu headers path to self._paths
                    _f = self._linux_gnu_path + substr[start:end] + os.sep
                    if os.path.exists(_f):
                        self._paths.append(_f)

                if self.is_window:
                    # add cpp window headers to self._paths
                    _f = self._cpp_path + substr[start:end] + os.sep
                    if os.path.exists(_f):
                        self._paths.append(_f)

            else:
                self._paths = []
                for _p in self._settings_paths:
                    self._paths.append(_p)

            if self._is_main_path:

                # if is windows
                if self.is_window:
                    if self._is_main_path:
                        for _p in self._cpp_windows_h:
                            _r = self._parse_result(
                                substr,
                                _p,
                                self._cpp_windows_h[_p]
                            )
                            result.append(_r)

                # if is linux
                if self.is_linux:

                    if not re.search(r"\.c$", file_name):
                        for _p in self._cpp_gnu_h:
                            _r = self._parse_result(
                                substr,
                                _p,
                                self._cpp_gnu_h[_p])

                            result.append(_r)

                    # adding linux gnu libs
                    for _p in self._linux_gnu_h:
                        _r = self._parse_result(
                            substr,
                            _p,
                            self._linux_gnu_h[_p])

                        result.append(_r)

            for path in self._paths:
                _glob_result = glob.glob(path + prefix + "*")
                if _glob_result:
                    for item in _glob_result:
                        if item.replace(path, "").startswith(prefix):
                            if os.path.isdir(item):
                                _r = self._parse_result(
                                    substr,
                                    item.replace(path, ""),
                                    "directory"
                                )
                                result.append(_r)
                            elif os.path.isfile(item):
                                _r = self._parse_result(
                                    substr,
                                    item.replace(path, ""),
                                    "module"
                                )
                                result.append(_r)

        return result


def plugin_loaded():
    global settings
    settings = sublime.load_settings(SETTINGS_FILE)

plugin_loaded()
