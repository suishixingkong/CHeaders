import os
import re
import copy
import glob

import sublime
import sublime_plugin


_obj_exists = lambda obj: os.path.exists(obj)
_join = lambda x, y: os.path.join(x, y)
_is_dir = lambda obj: os.path.isdir(obj)
_is_file = lambda obj: os.path.isfile(obj)

SETTINGS_FILE = 'CHeaders.sublime-settings'
settings = {}

GNU_INCLUDE = '/usr/include/'
GNU_LOCAL_INCLUDE = '/usr/local/include/'
GNU_INCLUDE_32BITS = '/usr/include/i386-linux-gnu/'
GNU_INCLUDE_64BITS = '/usr/include/x86_64-linux-gnu/'
GNU_INCLUDE_CPP = '/usr/include/c++/'
GNU_INCLUDE_CPP_32BITS = '/usr/include/i386-linux-gnu/c++/'
GNU_INCLUDE_CPP_64BITS = '/usr/include/x86_64-linux-gnu/c++/'

# this function only works with 
# MINGW32_INCLUDE_FIXED
# MINGW32_INCLUDE_FIXED2
def _win_include_fixed(path, versions):
    for version in versions:
        if _obj_exists(path % version):
            return path % version

MINGW_INCLUDE = 'C:\\Mingw\\include\\'
MINGW32_INCLUDE = 'C:\\MinGW\\mingw32\\include\\'
MINGW32_SYS = 'C:\\MinGW\\msys\\1.0\\include\\'
MINGW32_INCLUDE_FIXED = 'C:\\MinGW\\mingw32\\lib\\gcc\\mingw32\\%s\\include\\'
MINGW32_INCLUDE_FIXED2 = 'C:\\MinGW\\mingw32\\lib\\gcc\\mingw32\\%s\\include-fixed\\'
MINGW_CPP_INCLUDE = 'C:\\MinGW\\mingw32\\lib\\gcc\\mingw32\\%s\\include\\c++\\'

CYWING_INCLUDE = 'C:\\cygwin\\usr\\include\\'
CYWING_INCLUDE_CPP_32BITS = 'C:\\cygwin\\lib\\gcc\\i686-pc-cygwin\\%s\\include\\c++\\'
CYWING_INCLUDE_CPP_64BITS = 'C:\\cygwin\\lib\\gcc\\x86_64-pc-cygwin\\%s\\include\\c++\\'

IS_C_FILE = re.compile(r'(.*\.(%s|%s|%s|%s|%s|%s|%s|%s|%s))$' % (
    re.escape('c'),
    re.escape('cpp'),
    re.escape('cc'),
    re.escape('c++'),
    re.escape('cxx'),
    re.escape('CXX'),
    re.escape('C'),
    re.escape('CPP'),
    re.escape('cp'),
))

IS_CH_FILE = re.compile(r'(.*\.(%s|%s|%s|%s|%s|%s|%s))$' % (
    re.escape('h'),
    re.escape('hpp'),
    re.escape('hh'),
    re.escape('hxx'),
    re.escape('Hxx'),
    re.escape('HXX'),
    re.escape('H')
))

IS_C_FILE_OTHERS = re.compile(r'(.*\.(%s))$' % (
    re.escape('ipp'),
))

IS_OTHER_FILE = re.compile(r'(.*\.(%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s))$' % (
    re.escape('am'),
    re.escape('m4'),
    re.escape('am'),
    re.escape('gccgo'),
    re.escape('eot'),
    re.escape('glyphs'),
    re.escape('woff'),
    re.escape('scss'),
    re.escape('styl'),
    re.escape('less'),
    re.escape('sass'),
    re.escape('cabal'),
    re.escape('hs'),
    re.escape('org'),
    re.escape('el'),
    re.escape('lua'),
    re.escape('dmg'),
    re.escape('iso'),
    re.escape('ent'),
    re.escape('cfg'),
    re.escape('gradle'),
    re.escape('stylus'),
    re.escape('pdb'),
    re.escape('sln'),
    re.escape('markdown'),
    re.escape('scala'),
    re.escape('xsit'),
    re.escape('asc'),
    re.escape('sup'),
    re.escape('dep'),
    re.escape('conf'),
    re.escape('ml'),
    re.escape('mli'),
    re.escape('ocp'),
    re.escape('opam'),
    re.escape('ac'),
    re.escape('cmake'),
    re.escape('rst'),
    re.escape('coffee'),
    re.escape('toml'),
    re.escape('rs'),
    re.escape('lock'),
    re.escape('in'),
    re.escape('swift'),
    re.escape('pbxproj'),
    re.escape('xib'),
    re.escape('png'),
    re.escape('yml'),
    re.escape('vim'),
    re.escape('md'),
    re.escape('apk'),
    re.escape('go'),
    re.escape('css'),
    re.escape('rb'),
    re.escape('pyc'),
    re.escape('py'),
    re.escape('zip'),
    re.escape('yxx'),
    re.escape('xpm'),
    re.escape('xrb'),
    re.escape('y'),
    re.escape('wav'),
    re.escape('wmf'),
    re.escape('xml'),
    re.escape('VMS'),
    re.escape('vor'),
    re.escape('W32'),
    re.escape('UNX'),
    re.escape('urd'),
    re.escape('url'),
    re.escape('txt'),
    re.escape('TXT'),
    re.escape('unx'),
    re.escape('tsc'),
    re.escape('ttf'),
    re.escape('TTF'),
    re.escape('TFM'),
    re.escape('thm'),
    re.escape('tpt'),
    re.escape('tab'),
    re.escape('Static'),
    re.escape('SSLeay'),
    re.escape('srs'),
    re.escape('src'),
    re.escape('soh'),
    re.escape('sog'),
    re.escape('soe'),
    re.escape('sod'),
    re.escape('soc'),
    re.escape('soh'),
    re.escape('sob'),
    re.escape('so'),
    re.escape('sms'),
    re.escape('smf'),
    re.escape('sid'),
    re.escape('sh'),
    re.escape('sgl'),
    re.escape('Set'),
    re.escape('SEG'),
    re.escape('seg'),
    re.escape('sdi'),
    re.escape('sdw'),
    re.escape('sdv'),
    re.escape('sds'),
    re.escape('sdm'),
    re.escape('sdg'),
    re.escape('sdd'),
    re.escape('sdc'),
    re.escape('sdb'),
    re.escape('sda'),
    re.escape('scr'),
    re.escape('scp'),
    re.escape('sbl'),
    re.escape('S'),
    re.escape('s'),
    re.escape('res'),
    re.escape('rdb'),
    re.escape('rc'),
    re.escape('r'),
    re.escape('ptr'),
    re.escape('PS'),
    re.escape('prt'),
    re.escape('PRJ'),
    re.escape('pre'),
    re.escape('pmk'),
    re.escape('pm'),
    re.escape('plf'),
    re.escape('PLD'),
    re.escape('pld'),
    re.escape('plc'),
    re.escape('PL'),
    re.escape('pl'),
    re.escape('pfb'),
    re.escape('pfa'),
    re.escape('par'),
    re.escape('obj'),
    re.escape('o'),
    re.escape('NT2'),
    re.escape('mod'),
    re.escape('MK'),
    re.escape('map'),
    re.escape('MacOS'),
    re.escape('mac'),
    re.escape('lst'),
    re.escape('LOG'),
    re.escape('lnx'),
    re.escape('lnk'),
    re.escape('lng'),
    re.escape('LN3'),
    re.escape('ll'),
    re.escape('lin'),
    re.escape('lib'),
    re.escape('lgt'),
    re.escape('l'),
    re.escape('kdelnk'),
    re.escape('jsp'),
    re.escape('js'),
    re.escape('jpg'),
    re.escape('jnl'),
    re.escape('jar'),
    re.escape('java'),
    re.escape('ins'),
    re.escape('inl'),
    re.escape('ini'),
    re.escape('inf'),
    re.escape('inc'),
    re.escape('ilb'),
    re.escape('ih'),
    re.escape('IDL'),
    re.escape('idl'),
    re.escape('ico'),
    re.escape('html'),
    re.escape('HRC'),
    re.escape('hrc'),
    re.escape('hid'),
    re.escape('hdl'),
    re.escape('hdb'),
    re.escape('gif'),
    re.escape('fmt'),
    re.escape('ft'),
    re.escape('fp'),
    re.escape('font'),
    re.escape('fmt'),
    re.escape('ftl'),
    re.escape('mm'),
    re.escape('m'),
    re.escape('a'),
    re.escape('asp'),
    re.escape('asm'),
    re.escape('awk'),
    re.escape('bat'),
    re.escape('bmp'),
    re.escape('btm'),
    re.escape('BTM'),
    re.escape('class'),
    re.escape('cmd'),
    re.escape('csv'),
    re.escape('cur'),
    re.escape('db'),
    re.escape('def'),
    re.escape('DES'),
    re.escape('dlg'),
    re.escape('dll'),
    re.escape('don'),
    re.escape('dpc'),
    re.escape('dpj'),
    re.escape('dtd'),
    re.escape('dump'),
    re.escape('dxp'),
    re.escape('eng'),
    re.escape('mk'),
    re.escape('exe'),
))

GET_CH_DIR = re.compile(r"(\w+(-*\.*\w+/*|/\w+)*(?=/))")

# architecture
ARCH = sublime.arch()

# distribution
IS_LINUX = sublime.platform() == "linux"
IS_WINDOW = sublime.platform() == "windows"


# gnu cpp versions
CPP_SUPPORTED_VERSIONS = [
    '4.0.0',
    '4.0.1',
    '4.0.2',
    '4.0.3',
    '4.0.4',
    '4.0.5',
    '4.0.6',
    '4.0.7',
    '4.0.8',
    '4.0.9',
    '4.1.0',
    '4.1.1',
    '4.1.2',
    '4.1.3',
    '4.1.4',
    '4.1.5',
    '4.1.6',
    '4.1.7',
    '4.1.8',
    '4.1.9',
    '4.2.0',
    '4.2.1',
    '4.2.2',
    '4.2.3',
    '4.2.4',
    '4.2.5',
    '4.2.6',
    '4.2.7',
    '4.2.8',
    '4.2.9',
    '4.3.0',
    '4.3.1',
    '4.3.2',
    '4.3.3',
    '4.3.4',
    '4.3.5',
    '4.3.6',
    '4.3.7',
    '4.3.8',
    '4.3.9',
    '4.4.0',
    '4.4.1',
    '4.4.2',
    '4.4.3',
    '4.4.4',
    '4.4.5',
    '4.4.6',
    '4.4.7',
    '4.4.8',
    '4.4.9',
    '4.5.0',
    '4.5.1',
    '4.5.2',
    '4.5.3',
    '4.5.4',
    '4.5.5',
    '4.5.6',
    '4.5.7',
    '4.5.8',
    '4.5.9',
    '4.6.0',
    '4.6.1',
    '4.6.2',
    '4.6.3',
    '4.6.4',
    '4.6.5',
    '4.6.6',
    '4.6.7',
    '4.6.8',
    '4.6.9',
    '4.7.0',
    '4.7.1',
    '4.7.2',
    '4.7.3',
    '4.7.4',
    '4.7.5',
    '4.7.6',
    '4.7.7',
    '4.7.8',
    '4.7.9',
    '4.8.0',
    '4.8.1',
    '4.8.2',
    '4.8.3',
    '4.8.4',
    '4.8.5',
    '4.8.6',
    '4.8.7',
    '4.8.8',
    '4.8.9',
    '4.9.0',
    '4.9.1',
    '4.9.2',
    '4.9.3',
    '4.9.4',
    '4.9.5',
    '4.9.6',
    '4.9.7',
    '4.9.8',
    '4.9.9',
    '5.0.0',
    '5.0.1',
    '5.0.2',
    '5.0.3',
    '5.0.4',
    '5.0.5',
    '5.0.6',
    '5.0.7',
    '5.0.8',
    '5.0.9',
    '5.1.0',
    '5.1.1',
    '5.1.2',
    '5.1.3',
    '5.1.4',
    '5.1.5',
    '5.1.6',
    '5.1.7',
    '5.1.8',
    '5.1.9',
    '5.2.0',
    '5.2.1',
    '5.2.2',
    '5.2.3',
    '5.2.4',
    '5.2.5',
    '5.2.6',
    '5.2.7',
    '5.2.8',
    '5.2.9',
    '5.3.0',
    '5.3.1',
    '5.3.2',
    '5.3.3',
    '5.3.4',
    '5.3.5',
    '5.3.6',
    '5.3.7',
    '5.3.8',
    '5.3.9',
    '5.4.0',
    '5.4.1',
    '5.4.2',
    '5.4.3',
    '5.4.4',
    '5.4.5',
    '5.4.6',
    '5.4.7',
    '5.4.8',
    '5.4.9',
    '5.5.0',
    '5.5.1',
    '5.5.2',
    '5.5.3',
    '5.5.4',
    '5.5.5',
    '5.5.6',
    '5.5.7',
    '5.5.8',
    '5.5.9',
    '5.6.0',
    '5.6.1',
    '5.6.2',
    '5.6.3',
    '5.6.4',
    '5.6.5',
    '5.6.6',
    '5.6.7',
    '5.6.8',
    '5.6.9',
    '5.7.0',
    '5.7.1',
    '5.7.2',
    '5.7.3',
    '5.7.4',
    '5.7.5',
    '5.7.6',
    '5.7.7',
    '5.7.8',
    '5.7.9',
    '5.8.0',
    '5.8.1',
    '5.8.2',
    '5.8.3',
    '5.8.4',
    '5.8.5',
    '5.8.6',
    '5.8.7',
    '5.8.8',
    '5.8.9',
    '5.9.0',
    '5.9.1',
    '5.9.2',
    '5.9.3',
    '5.9.4',
    '5.9.5',
    '5.9.6',
    '5.9.7',
    '5.9.8',
    '5.9.9',
    '6.0.0',
    '6.0.1',
    '6.0.2',
    '6.0.3',
    '6.0.4',
    '6.0.5',
    '6.0.6',
    '6.0.7',
    '6.0.8',
    '6.0.9',
    '6.1.0',
    '6.1.1',
    '6.1.2',
    '6.1.3',
    '6.1.4',
    '6.1.5',
    '6.1.6',
    '6.1.7',
    '6.1.8',
    '6.1.9',
    '6.2.0',
    '6.2.1',
    '6.2.2',
    '6.2.3',
    '6.2.4',
    '6.2.5',
    '6.2.6',
    '6.2.7',
    '6.2.8',
    '6.2.9',
    '6.3.0',
    '6.3.1',
    '6.3.2',
    '6.3.3',
    '6.3.4',
    '6.3.5',
    '6.3.6',
    '6.3.7',
    '6.3.8',
    '6.3.9',
    '6.4.0',
    '6.4.1',
    '6.4.2',
    '6.4.3',
    '6.4.4',
    '6.4.5',
    '6.4.6',
    '6.4.7',
    '6.4.8',
    '6.4.9',
    '6.5.0',
    '6.5.1',
    '6.5.2',
    '6.5.3',
    '6.5.4',
    '6.5.5',
    '6.5.6',
    '6.5.7',
    '6.5.8',
    '6.5.9',
    '6.6.0',
    '6.6.1',
    '6.6.2',
    '6.6.3',
    '6.6.4',
    '6.6.5',
    '6.6.6',
    '6.6.7',
    '6.6.8',
    '6.6.9',
    '6.7.0',
    '6.7.1',
    '6.7.2',
    '6.7.3',
    '6.7.4',
    '6.7.5',
    '6.7.6',
    '6.7.7',
    '6.7.8',
    '6.7.9',
    '6.8.0',
    '6.8.1',
    '6.8.2',
    '6.8.3',
    '6.8.4',
    '6.8.5',
    '6.8.6',
    '6.8.7',
    '6.8.8',
    '6.8.9',
    '6.9.0',
    '6.9.1',
    '6.9.2',
    '6.9.3',
    '6.9.4',
    '6.9.5',
    '6.9.6',
    '6.9.7',
    '6.9.8',
    '6.9.9',
]

if IS_LINUX:
    CPP_PATHS = [GNU_INCLUDE_CPP]

    # 32 bits
    if ARCH == 'x32':
        CPP_PATHS.append(GNU_INCLUDE_CPP_32BITS)
    # 64 bits
    elif ARCH == 'x64':
        CPP_PATHS.append(GNU_INCLUDE_CPP_64BITS)

    _CPP_ABSOLUTE_PATH = [
        _join(CPP_PATH, version) 
        for version in CPP_SUPPORTED_VERSIONS
        for CPP_PATH in CPP_PATHS
        if _obj_exists(_join(CPP_PATH, version))
    ]

    # this code shall be executed, when linux user has two
    # cpp versions, and the lastest will be choseen
    if len(_CPP_ABSOLUTE_PATH) >= 3:
        _CPP_ABSOLUTE_PATH = _CPP_ABSOLUTE_PATH[len(CPP_PATHS):]

elif IS_WINDOW:
    CPP_PATHS = []
    if _obj_exists(MINGW_INCLUDE):
        CPP_PATHS = [MINGW_CPP_INCLUDE]
    else:
        if ARCH == 'x32':
            CPP_PATHS.append(CYWING_INCLUDE_CPP_32BITS)
        elif ARCH == 'x64':
            CPP_PATHS.append(CYWING_INCLUDE_CPP_64BITS)

    _CPP_ABSOLUTE_PATH = [
        (CPP_PATH % VERSION)
        for VERSION in CPP_SUPPORTED_VERSIONS
        for CPP_PATH in CPP_PATHS
        if _obj_exists((CPP_PATH % VERSION))
    ]

# all cpp paths, on the SO(linux, windows, etc).
CPP_ABSOLUTE_PATH = _CPP_ABSOLUTE_PATH


class LoadPluginCommand(sublime_plugin.WindowCommand):

    def run(self, **kwargs):
        # load the CHeaders plugin.
        sublime.status_message(kwargs.get("message"))
        sublime_plugin.reload_plugin(__name__)


class CompleteCHeadersCommand(sublime_plugin.EventListener):

    def __init__(self):
        sublime_plugin.EventListener.__init__(self)
        global settings


        # include wrappers
        self._include_global_files = "#include <%s>"
        self._include_global_dirs = "#include <%s/"
        # self._include_local_files = "#include \"%s\""
        # self._include_local_dirs = "#include \"%s/"

        # loading settings
        settings = sublime.load_settings(SETTINGS_FILE)
        self._cache_paths = settings.get("PATHS_HEADERS", [])

        if self._cache_paths:
            self._cache_paths = self.parse_settings(self._cache_paths)

        if IS_LINUX:
            self._cache_paths.append(GNU_INCLUDE)
            self._cache_paths.append(GNU_LOCAL_INCLUDE)

            if ARCH == 'x32':
                self._cache_paths.append(GNU_INCLUDE_32BITS)
            elif ARCH == 'x64':
                self._cache_paths.append(GNU_INCLUDE_64BITS)

        if IS_WINDOW:
            error_msg = ""

            # cpp windows supported version 4.8.1
            # cywing and mingw
            if _obj_exists("C:\\cygwin"):
                self._cache_paths.append(CYWING_INCLUDE)

            elif _obj_exists("C:\\Mingw"):
                self._cache_paths.append(MINGW_INCLUDE)
                self._cache_paths.append(MINGW32_INCLUDE)
                self._cache_paths.append(MINGW32_SYS)
                self._cache_paths \
                    .append(_win_include_fixed(MINGW32_INCLUDE_FIXED, CPP_SUPPORTED_VERSIONS))
                self._cache_paths \
                    .append(_win_include_fixed(MINGW32_INCLUDE_FIXED2, CPP_SUPPORTED_VERSIONS))

            else:
                error_msg = """*  You should download Mingw, this is the webpage:
http://sourceforge.net/projects/mingw/files/ or cywing at http://cygwin.com/install.html"""
                sublime.error_msg(error_msg)

        # adding cpp std headers
        self._cpp_h = {}
        for path in CPP_ABSOLUTE_PATH:
            if path.endswith(os.sep):
                self._cache_paths.append(path)
            else:
                self._cache_paths.append(path + os.sep)


        # this list will contain a copy of self._cache_paths
        self._paths = self.copy_cache()

    def copy_cache(self):
        # deep copy of settings paths
        return copy.deepcopy(self._cache_paths)

    def clean(self):
        # clean self._paths.
        self._paths = []

    def file_name(self):
        # Will return the actual buffer name
        return sublime.active_window().active_view().name() or\
            sublime.active_window().active_view().file_name()

    def is_c_file(self, file):
        # will test, if the file, it's a c or c header file
        # else, return false.
        #
        # :file file to test.
        return IS_C_FILE.search(file) or IS_CH_FILE.search(file) or \
                IS_C_FILE_OTHERS.search(file)

    def is_cpp_file(self, filename):
        # Will test, if the file, without any extention,
        # is a c++, file.
        if _is_file(filename):
            file_content = ''
            with open(filename, 'r') as cpp_file:
                file_content = cpp_file.read()
            return re.search(r'#(include|define|pragma|ifndef|if).*', file_content)
        return None

    def parse_settings(self, settings):
        # will parse, settings user input
        # sample linux:
        #
        #   /home/leoxnidas/include/ -> normal
        #   ~/include/ -> /home/user/include/
        #   $HOME/include/ -> /home/usr/include
        #
        # sample windows:
        #   C:\ -> normal
        #   %HOME%\example -> C:\example
        #
        # :settings json settings.
        #
        _settings = []
        for _setting in settings:
            if _setting.startswith("~"):
                _setting = _setting.replace("~", os.environ["HOME"])
            if _setting.startswith("$HOME"):
                _setting = _setting.replace("$HOME", os.environ["HOME"])
            if _setting.startswith("%HOME%"):
                _setting = _setting.replace("%HOME%", "C:\\")
            _settings.append(_setting)
        return _settings

    def current_line(self, view, location):
        # will return the current line, where the programmer
        # is writting.
        #
        # :view current active view
        # :location current cursor location on the buffer
        substr = view.substr(sublime.Region(0, location))
        if '#' in substr:
            sharp_index = substr.rindex('#')

            if '>' in substr:
                great_index = substr.rindex('>')
                if sharp_index > great_index:
                    return substr[sharp_index:]
                else:
                    return ''
            else:
                return substr[sharp_index:]
        else:
            return ''

    def parse_result(self, substr, header, type):
        # Return a tuple, specifying if the header object
        # is a module or a directory, if it needs include macro
        # or not, if it is local or no.
        #
        # :substr where the user, it is writting
        # :header current header, example: stdio.h
        # :type the header type, if it is a directory or a module
        _caption = header + '\t' + type
        if type == "directory":
            if "#include" not in substr:
                _r = self._include_global_dirs % header
            if "#include <" in substr or "#include \"" in substr:
                _r = header + "/"

        if type == "module":
            if "#include" not in substr:
                _r = self._include_global_files % header
            if "#include <" in substr:
                _r = header + ">"
            if "#include \"" in substr:
                _r = header + "\""

        return _caption, _r

    def on_query_completions(self, view, prefix, location):
        result = []
        substr = ""

        # if it is a c file, then execute code.
        if self.is_c_file(self.file_name()):

            substr = self.current_line(view, location[0])
            rx = GET_CH_DIR.search(substr)

            # clean self._paths.
            self.clean()
            
            if rx:
                # add current path, to self._paths,
                # to autocomplete, c headers or others 
                # directories.
                # 
                # sample:
                #
                # #include <linux/ <-- current posible path
                #                         /usr/include/linux
                #                         /usr/local/include/linux
                start = rx.start()
                end = rx.end()

                for _path in self._cache_paths:
                    _abs_path = _path + substr[start:end] + os.sep
                    if _obj_exists(_abs_path):
                        self._paths.append(_abs_path)

            else:
                # add all paths again to self._paths
                self._paths = self.copy_cache()

            for path in self._paths:
                _glob_result = glob.glob(path + prefix + "*")
                if _glob_result:
                    for item in _glob_result:
                        
                        if item.replace(path, "").startswith(prefix) and \
                            not IS_C_FILE.match(item) and \
                            (self.is_cpp_file(item) or _is_dir(item)) and \
                            not IS_OTHER_FILE.match(item):

                            if _is_dir(item):
                                _r = self.parse_result(
                                    substr,
                                    item.replace(path, ""),
                                    "directory",
                                )
                            elif _is_file(item):
                                _r = self.parse_result(
                                    substr,
                                    item.replace(path, ""),
                                    "module",
                                )

                            # to eliminate repeteable values
                            if _r not in result:
                                result.append(_r)
        return result

