from distutils.core import setup
from setuptools.command.install import install


class install_utidylib(install):
    def run(self):
        install.run(self)
        print "*** This library requires that you have two libraries ***"
        print "***           installed: ctypes and libtidy.          ***"
        print "***   Please make sure they are installed correctly   ***"
        print "***              before reporting a bug.              ***"
        print "*** See:                                              ***"
        print "***  http://starship.python.net/crew/theller/ctypes/  ***"
        print "***         and http://tidy.sourceforge.net           ***"
        print "*** (or consult your vendor documentation for binary  ***"
        print "***                    packages.)                     ***"


setup_data = dict(packages=['tidy', ],
                  data_files=[],
                  cmdclass=dict(
                                install=install_utidylib,
                                ),
                  name='uTidylib',
                  version='0.2',
                  author='Cory Dodt',
                  author_email='corydodt@twistedmatrix.com',
                  url='http://utidylib.sf.net',
                  description='Wrapper for HTML Tidy at '
                              'http://tidy.sourceforge.net',
                  long_description='''\
A wrapper for the relocatable version of HTML Tidy (see
http://tidy.sourceforge.net for details).  This allows you to
tidy HTML files through a Pythonic interface.'''
                  )

if __name__ == '__main__':
    setup(**setup_data)
