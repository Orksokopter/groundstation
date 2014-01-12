set PYTHONPATH=%PYTHONPATH%;%~dp0

for /f "delims=" %%a in ('python -c "from distutils.sysconfig import get_python_lib; print (get_python_lib())"') do @set pathofpythonexe=%%a

set PATH=%PATH%;%pathofpythonexe%\PyQt4

pyrcc4 -py3 "%~dp0\gui\resources.qrc" > "%~dp0\gui\resources_rc.py"

python "%~dp0\gui\main_window.py"
