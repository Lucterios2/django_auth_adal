from setuptools import setup

setup(
    name='django-auth-adal',
    version='0.1',
    packages=['django_auth_adal'],
    url='https://github.com/Lucterios2/django_auth_adal',
    license='GPL V3',
    author='Pierre-Olivier VERSCHOORE',
    author_email='po.verschoore@sd-libre.fr',
    description='very simple authentication module for python3 / django / Azur AD - Office365 using MS ADAL Lib',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django :: 2.0',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
    install_requires=["Django>=2.0", "adal>=1.2.0"],
)
