import glob
import os
import shutil
import sys
from cx_Freeze import setup, Executable

from PyQt5 import QtCore

app = QtCore.QCoreApplication(sys.argv)
qt_library_path = QtCore.QCoreApplication.libraryPaths()

buildexe_options = {
    'compressed': True,
    'optimize': 2
}

imageformats_path = None
for path in qt_library_path:
    if os.path.exists(os.path.join(path, 'imageformats')):
        imageformats_path = os.path.join(path, 'imageformats')
        local_imageformats_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'imageformats')

        buildexe_options['include_files'] = ['imageformats']

        if not os.path.exists(local_imageformats_path):
            os.mkdir(local_imageformats_path)
        for file in glob.glob(os.path.join(imageformats_path, '*')):
            shutil.copy(file, os.path.join(local_imageformats_path, os.path.basename(file)))

setup(
    name='Bodenpython',
    version='0.1',
    description='Orksokopter Bodenstation',
    executables=[
        Executable('serial_port_handler.py'),
        Executable('gui/main_window.py',
                   icon='gui/resources/app.ico',
                   base="Win32GUI" if sys.platform == "win32" else None,
                   targetName='Bodenpython.exe' if sys.platform == "win32" else "bodenpython")
    ],
    options={
        'build_exe': buildexe_options
    }
)
