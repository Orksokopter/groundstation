import sys
from cx_Freeze import setup, Executable

setup(
    name='Bodenpython',
    version='0.1',
    description='Orksokopter Bodenstation',
    executables=[
        Executable('serial_port_handler.py')
    ],
    options={
        'build_exe' : {
            'compressed' : True,
            'optimize' : 2,
        }
    }
)
