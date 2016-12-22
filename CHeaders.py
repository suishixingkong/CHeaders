import os
import re
import copy
import itertools

import sublime
import sublime_plugin

# regular expressions
IS_C_HEADER_EXP = r'.*\.[h|H|hpp|hxx]$'
IS_C_CPP_FILE_EXP = r'.*\.[c|C|h|H|hpp|hxx|cpp|cxx|cc]$'

# architecture
ARCH = sublime.arch()

# distribution
IS_LINUX = sublime.platform() == "linux"
IS_WINDOW = sublime.platform() == "windows"
IS_OSX = sublime.platform() == 'osx'

GNU_INCLUDE = '/usr/include/'
GNU_LOCAL_INCLUDE = '/usr/local/include/'
GNU_INCLUDE_32BITS = '/usr/include/i386-linux-gnu/'
GNU_INCLUDE_64BITS = '/usr/include/x86_64-linux-gnu/'
GNU_INCLUDE_CPP = '/usr/include/c++/'
GNU_INCLUDE_CPP_32BITS = '/usr/include/i386-linux-gnu/c++/'
GNU_INCLUDE_CPP_64BITS = '/usr/include/x86_64-linux-gnu/c++/'

MINGW_INCLUDE = 'C:\\Mingw\\include\\'
MINGW32_INCLUDE = 'C:\\MinGW\\mingw32\\include\\'
MINGW32_SYS = 'C:\\MinGW\\msys\\1.0\\include\\'
MINGW32_INCLUDE_FIXED = 'C:\\MinGW\\mingw32\\lib\\gcc\\mingw32\\%s\\include\\'
MINGW32_INCLUDE_FIXED2 = 'C:\\MinGW\\mingw32\\lib\\gcc\\mingw32\\%s\\include-fixed\\'
MINGW_CPP_INCLUDE = 'C:\\MinGW\\mingw32\\lib\\gcc\\mingw32\\%s\\include\\c++\\'

CYWING_INCLUDE = 'C:\\cygwin\\usr\\include\\'
CYWING_INCLUDE_CPP_32BITS = 'C:\\cygwin\\lib\\gcc\\i686-pc-cygwin\\%s\\include\\c++\\'
CYWING_INCLUDE_CPP_64BITS = 'C:\\cygwin\\lib\\gcc\\x86_64-pc-cygwin\\%s\\include\\c++\\'

VISUAL_STUDIO_14 = 'C:\\Program Files (x86)\\Microsoft Visual Studio 14.0'
VISUAL_STUDIO_12 = 'C:\\Program Files (x86)\\Microsoft Visual Studio 12.0'
VISUAL_STUDIO_11 = 'C:\\Program Files (x86)\\Microsoft Visual Studio 11.0'
WINDOWS_KITS = 'C:\\Program Files (x86)\\Windows Kits'

def parse_path(path):
    if path.startswith("~"):
        path = path.replace("~", os.environ["HOME"])
    if path.startswith("$HOME"):
        path = path.replace("$HOME", os.environ["HOME"])
    if path.startswith("%HOME%"):
        path = path.replace("%HOME%", "C:\\")
    return os.path.realpath(path)

class Logger(object):

    def log(self, msg):
        pass

class DummyLogger(Logger):
    pass

class SmallLogger(Logger):
    
    default_tag = 'CHeaders.py'

    def __init__(self, tag=None):
        self.tag = tag

    def log(self, msg):
        print('[%s] %s' % (self.tag or self.default_tag, msg))

class CHeadersSettings(object):

    def __init__(self):
        self.settings_filename = 'CHeaders.sublime-settings'
        self.settings = sublime.load_settings(self.settings_filename)

    def get_debug_mode(self):
        return self.settings.get('DEBUG', False)

    def get_debug_tag(self):
        return self.settings.get('DEBUG_TAG', None)

    def get_incs_paths(self):
        return self.settings.get('PATHS_HEADERS', [])

class Model(object):

    def __init__(self, abspath):
        self.name = os.path.basename(abspath)
        self.parent_path = os.path.dirname(abspath)
        self.type = None

    def parsed_name(self):
        return '%s\t%s' % (self.name, self.type)

    def parsed_include(self):
        return None

    def __str__(self):
        return self.name

    def __repr__(self):
        return '%s' % self.name

    def __eq__(self, o):
        if isinstance(o, str):
            return self.name == o
        return self.name == o.name and self.parent_path == o.parent_path

class FileModel(Model):
    
    def __init__(self, abspath):
        Model.__init__(self, abspath)
        self.type = 'module'

    def parsed_include(self):
        return '#include <%s>' % self.name

class DirModel(Model):

    def __init__(self, abspath):
        Model.__init__(self, abspath)
        self.type = 'directory'
        self.content = list(self.clean_non_c_content(abspath, os.listdir(abspath)))

    def clean_non_c_content(self, abspath, content):
        def _get_content(tmpContent, path):
            for fo in tmpContent:
                if os.path.isdir(os.path.join(path, fo)) or re.match(IS_C_HEADER_EXP, fo) or 'c++' in path:
                    yield fo
        for c in _get_content(content, abspath):
            fileobj = os.path.join(abspath, c)
            if os.path.isdir(fileobj):
                yield DirModel(fileobj)
            else:
                yield FileModel(fileobj)

    def parsed_includes(self):
        dirs = []
        for o in self.content:
            dirs.append(([o.parsed_name(), o.parsed_include()], o))
        return dirs

    def parsed_include(self):
        return '#include <%s/' % self.name

LAZY_CACHE = []
def get_cpp_supported_version(path):
    # will get supported cpp versions,
    # if the last version is found, a simple
    # cache will save that cpp version.
    global LAZY_CACHE
    versions = []
    if len(LAZY_CACHE) >= 1:
        versions = LAZY_CACHE
    else:
        versions = list(reversed(CPP_SUPPORTED_VERSIONS))
    for v in versions:
        if IS_LINUX:
            p = os.path.join(path, v)
            if os.path.exists(p):
                LAZY_CACHE.append(v)
                return DirModel(p)
        elif IS_WINDOW:
            p = path % v
            if os.path.exists(p):
                LAZY_CACHE.append(v)
                return p
        elif IS_OSX:
            pass

INCLUDES = []
if IS_LINUX:
    INCLUDES += DirModel(GNU_INCLUDE).parsed_includes()
    INCLUDES += DirModel(GNU_LOCAL_INCLUDE).parsed_includes()
    INCLUDES += get_cpp_supported_version(GNU_INCLUDE_CPP).parsed_includes()

    if ARCH == 'x32':
        INCLUDES += get_cpp_supported_version(GNU_INCLUDE_CPP_32BITS).parsed_includes()
        INCLUDES += DirModel(GNU_INCLUDE_32BITS).parsed_includes()
    elif ARCH == 'x64':
        INCLUDES += get_cpp_supported_version(GNU_INCLUDE_CPP_64BITS).parsed_includes()
        INCLUDES += DirModel(GNU_INCLUDE_64BITS).parsed_includes()

elif IS_WINDOW:
    if os.path.exists('C:\\cygwin'):
        INCLUDES += DirModel(CYWING_INCLUDE).parsed_includes()
        if ARCH == 'x32':
            INCLUDES += get_cpp_supported_version(CYWING_INCLUDE_CPP_32BITS).parsed_includes()
        elif ARCH == 'x64':
            INCLUDES += get_cpp_supported_version(CYWING_INCLUDE_CPP_64BITS).parsed_includes()

    elif os.path.exists('C:\\Mingw'):
        INCLUDES += DirModel(MINGW_INCLUDE).parsed_includes()

        if ARCH == 'x32':
            INCLUDES += DirModel(MINGW32_INCLUDE).parsed_includes()
            INCLUDES += DirModel(MINGW32_SYS).parsed_includes()
            INCLUDES += get_cpp_supported_version(MINGW32_INCLUDE_FIXED).parsed_includes()
            INCLUDES += get_cpp_supported_version(MINGW32_INCLUDE_FIXED2).parsed_includes()
            INCLUDES += get_cpp_supported_version(MINGW_CPP_INCLUDE).parsed_includes()
    elif os.path.exists(VISUAL_STUDIO_14) or os.path.exists(VISUAL_STUDIO_12) or os.path.exists(VISUAL_STUDIO_11):
        path = ''
        if os.path.exists(VISUAL_STUDIO_14):
            path = VISUAL_STUDIO_14 + '\\VC\\include'
        elif os.path.exists(VISUAL_STUDIO_12):
            path = VISUAL_STUDIO_12 + '\\VC\\include'
        elif os.path.exists(VISUAL_STUDIO_11):
            path = VISUAL_STUDIO_11 + '\\VC\\include'
        INCLUDES += DirModel(path).parsed_includes()

        if os.path.exists(WINDOWS_KITS):
            if os.path.exists(WINDOWS_KITS + '\\10\\Include\\10.0.10240.0\\ucrt\\'):
                INCLUDES += DirModel(WINDOWS_KITS + '\\10\\Include\\10.0.10240.0\\ucrt\\').parsed_includes()
            elif os.path.exists(WINDOWS_KITS + '\\10\\Include\\10.0.10150.0\\ucrt\\'):
                INCLUDES += DirModel(WINDOWS_KITS + '\\10\\Include\\10.0.10150.0\\ucrt\\').parsed_includes()

            if os.path.exists(WINDOWS_KITS + '\\8.1\\Include'):
                INCLUDES += DirModel(WINDOWS_KITS + '\\8.1\\Include').parsed_includes()
            if os.path.exists(WINDOWS_KITS + '\\NETFXSDK\\4.6.1\\Include'):
                INCLUDES += DirModel(WINDOWS_KITS + '\\NETFXSDK\\4.6.1\\Include').parsed_includes()

elif IS_OSX:
    sublime.message_dialog('mac is not supported, but you could try, it may work,'
                            ' if you want to contribute, this is the repository https://github.com/leoxnidas/CHeaders')
    INCLUDES += []
else:
    sublime.error_message('unknow platform...')


class CHeadersCommand(sublime_plugin.ViewEventListener):

    INCLUDES = []
    CACHE = {}

    def __init__(self, view):
        sublime_plugin.ViewEventListener.__init__(self, view)
        self.settings = CHeadersSettings()
        if self.settings.get_debug_mode():
            self.logger = SmallLogger(self.settings.get_debug_tag())
        else:
            self.logger = DummyLogger()

        self.restart_includes()

    def get_includes_from_settings(self):
        for dir in self.settings.get_incs_paths():
            path = parse_path(dir)
            if os.path.exists(path) and path not in self.CACHE.keys():
                self.CACHE[path] = DirModel(path).parsed_includes()
        return list(itertools.chain.from_iterable(list(v for k, v in self.CACHE.items())))

    def restart_includes(self):
        self.INCLUDES = self.get_includes_from_settings() + copy.deepcopy(INCLUDES)
        self.logger.log(self.INCLUDES)

    def optimize_nearly_future_include_header(self, location):
        # will try to optimize c headers if it can,
        # otherwise, headers will be the same.
        if location == 1:
            return

        substr = self.view.substr(sublime.Region(0, location))
        o = False # this variable stop the repetitive work when / is found
        i = location - 1
        j = location - 1
        tmp_includes = copy.deepcopy(self.INCLUDES)
        while substr[i] != '#':
            if substr[i] == '<':
                for m in range(len(tmp_includes)):
                    tmp_includes[m][0][1] = tmp_includes[m][0][1].replace('#include <', '')
                break
            elif substr[i] == '\n':
                break
            elif substr[i] == '/' and not o:
                # this statement, can only happends once
                # thanks to 'o' variable, every time developer
                # wants to include a folder.
                # 
                # example:
                #   #include <linux/android/binder.h>
                #   
                o = True
                def get_inner_includes(str_dir, includes):
                    # will return all includes already parsed
                    for inc in includes:
                        if inc[-1] == str_dir:
                            yield inc[-1].parsed_includes()

                def find_inner_includes(pos, nw_substr, includes):
                    tmp_dir = ''
                    dirs_where_to_find = []
                    tmp_i = pos
                    tmp_j = pos
                    while nw_substr[tmp_i] != '<':
                        tmp_dir = nw_substr[tmp_i] + tmp_dir
                        if nw_substr[tmp_i] == '/':
                            dirs_where_to_find.insert(len(dirs_where_to_find), nw_substr[tmp_i+1:tmp_j+1])
                            tmp_j = tmp_i - 1
                            tmp_dir = ''
                        tmp_i -= 1

                    tmp_includes2 = list(get_inner_includes(tmp_dir, includes))[0]
                    if len(dirs_where_to_find) >= 1:
                        for dwtf in reversed(dirs_where_to_find):
                            tmp_includes2 = list(get_inner_includes(dwtf, tmp_includes2))[0]
                    return tmp_includes2
                tmp_includes = find_inner_includes(i - 1, substr, tmp_includes)
            i -= 1

        substr = self.view.substr(sublime.Region(0, self.view.size()))
        while substr[j] != '\n':
            if substr[j] == '>':
                for i in range(len(tmp_includes)):
                    tmp_includes[i][0][1] = tmp_includes[i][0][1].replace('>', '')
                break
            if j + 1 == self.view.size():
                break
            j += 1

        self.INCLUDES = copy.deepcopy(tmp_includes)
        self.logger.log('modules or directories to include: ' + str(self.INCLUDES))

    def can_include_c_header(self, location):
        # test if user can or cannot include a c header.
        substr = self.view.substr(sublime.Region(0, location))
        i = location - 1
        n = 0

        while i >= 0:
            try:
                substr[i]
            except:
                break

            if substr[i] == '<' or substr[i] == '/':
                n += 1
                break
            elif substr[i] == '>' or substr[i-1] in 'qwertyuioplkjhgfdsazxcvbnm123456789 ':
                break
            i -= 1

        self.logger.log("can include c header" if n == 1 else "cannot include c header")
        return True if n == 1 else False

    def is_in_scope(self, location):
        # test is the cursor is in a
        # c or cpp scope.
        substr = self.view.substr(sublime.Region(0, self.view.size()))
        n = 0
        i = location - 1
        j = location
        while i >= 0:
            try:
                # testing to avoid IndexError, idex out of range.
                substr[i]
            except Exception as e:
                self.logger.log(str(e))
                break

            if substr[i] == '{':
                n += 1
                break
            elif substr[i] == '}':
                break

            i -= 1

        while j < self.view.size():
            if substr[j] == '}':
                n += 1
                break
            elif substr[j] == '{':
                break
            j += 1

        self.logger.log("in scope" if n == 2 else "out of scope")
        return True if n == 2 else False

    def is_c_or_cpp_file(self):
        return re.match(IS_C_CPP_FILE_EXP, self.filename())

    def filename(self):
        return os.path.basename(os.path.realpath(self.view.file_name()))

    def get_includes(self):
        return list(fo[0] for fo in self.INCLUDES if str(fo[1]) not in ('c++', 'x86_64-linux-gnu', 'i386-linux-gnu'))

    def on_query_completions(self, prefix, locations):
        self.restart_includes()
        if self.is_c_or_cpp_file() and not self.is_in_scope(locations[0]) and self.can_include_c_header(locations[0]):
            self.logger.log("file used is a c file")
            self.optimize_nearly_future_include_header(locations[0])
            return self.get_includes(), sublime.INHIBIT_WORD_COMPLETIONS | sublime.INHIBIT_EXPLICIT_COMPLETIONS
        else:
            self.logger.log("file used is not a c file")
            return [], sublime.INHIBIT_WORD_COMPLETIONS | sublime.INHIBIT_EXPLICIT_COMPLETIONS
