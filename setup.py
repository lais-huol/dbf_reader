from setuptools import setup
# from distutils.core import setup
setup(
    name='suap_ead',
    description='Utils and theme classes for SUAP-EAD project services',
    long_description='Utils and theme classes for SUAP-EAD project services',
    license='MIT',
    author='Kelson da Costa Medeiros, Luiz Antonio Freitas de Assis',
    author_email='kelsoncm@gmail.com, luizvpc@gmail.com',
    packages=['suap_ead'],
    include_package_data=True,
    version='0.1.9',
    download_url='https://github.com/suap-ead/lib_suap_ead/releases/tag/0.1.9',
    url='https://github.com/suap-ead/lib_suap_ead',
    keywords=['SUAP', 'EAD', 'complemento', 'JWT', 'Django', 'Auth', 'SSO', 'client', 'Theme', ],
    install_requires=['PyJWT==1.7.1', 'django>=3.0.3', 'djangorestframework==3.11.0', 'sc4py>=0.1.3', 'sc4net==0.1.2'],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ]
)
