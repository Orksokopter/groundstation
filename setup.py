import sys
from cx_Freeze import setup, Executable

setup(
    name='Bodenpython',
    version='0.1',
    description='Orksokopter Bodenstation',
    executables=[
        Executable('serial_port_handler.py'),
        Executable('gui/main_window.py',
                   icon='gui/resources/app.ico',
                   base="Win32GUI" if sys.platform == "win32" else None)
    ],
    options={
        'build_exe' : {
            'compressed' : True,
            'optimize' : 2,
        }
    }
)
