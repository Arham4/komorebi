project('komorebi',
    version: '2.2.1',
    meson_version: '>=0.50',
    default_options: ['prefix=/usr/local']
)

# Internationalisation / Localisation. This is currently only used to configure the .desktop files;
i18n = import('i18n')
po_dir = meson.source_root() / 'po'
gettext_package = meson.project_name()
add_project_arguments('-DGETTEXT_PACKAGE=' + gettext_package, language: 'c')
i18n.gettext(meson.project_name(),
    args: '--directory=' + meson.source_root()
)

py_mod = import('python')
py_installation = py_mod.find_installation('python3')
if not py_installation.found()
      error('Couldn\'t find valid Python3 binary')
else
      message('Python3 binary found')
endif

# Set some variables
prefix = get_option('prefix')
bindir = get_option('bindir')
datadir = get_option('datadir')
pkgdatadir = join_paths(prefix, datadir, meson.project_name())
py_dir = join_paths(prefix, py_installation.get_install_dir())

# Compile resources (images, etc,) so that they're built into the app.
# TODO: Generate separate resource bundles for Komorebi & Wallpaper Creator;
# There's enough overlap that I'm not going to do it right now, but it'd be more elegant.
gnome = import('gnome')
komorebiresources = gnome.compile_resources(
    'komorebi', 'data/resources/komorebi.gresource.xml',
    source_dir: 'data/resources',
    gresource_bundle: true,
    install: true, install_dir: pkgdatadir
)

dependencies = [
    dependency('glib-2.0', version: '>=2.38'),
    dependency('gobject-2.0'),
    dependency('gtk+-3.0', version: '>=3.14'),
    dependency('gee-0.8'),
    dependency('webkit2gtk-4.0'),
    dependency('clutter-gtk-1.0'),
    dependency('clutter-1.0'),
    dependency('clutter-gst-3.0'),
]

subdir('data')

# Setup install dirs
install_subdir(
    'komorebi',
     exclude_files: [
        '__init__.in'
    ],
    exclude_directories: [
        '__pycache__',
        'bubblemenu/__pycache__',
        'overlays/__pycache__',
        'wallpaper_creator/__pycache__',
        'wallpapers/__pycache__'
    ],
    install_dir: py_dir
)

configure_file(
    input: 'komorebi.py',
    output: 'komorebi',
    copy: true,
    install_dir: bindir
)

configure_file(
    input: 'komorebi-wallpaper-creator.py',
    output: 'komorebi-wallpaper-creator',
    copy: true,
    install_dir: bindir
)

# Configure __init__.py
conf = configuration_data()
conf.set_quoted('PACKAGE_NAME', meson.project_name())
conf.set_quoted('PACKAGE_VERSION', meson.project_version())
conf.set_quoted('PKGDATADIR', pkgdatadir)
conf.set_quoted('DATADIR', join_paths(prefix, datadir))

configure_file(
      input: 'komorebi/__init__.in',
      output: '__init__.py',
      configuration: conf,
      install: true,
      install_dir: join_paths(py_dir, 'komorebi')
)

# Postinst script needs work. Let's not run it blindly.
# Frankly, I doubt that there's many (any?) users that have yet to update wallpapers to the new format, so maybe do away with it?
#meson.add_install_script('data/Other/postinst')
