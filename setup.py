from setuptools import setup

setup(
    name='pyLBPM',
    version='0.1.0',    
    description='pyLBPM is a monitoring framework for the LBPM software',
    url='https://github.com/JamesEMcClure/pyLBPM',
    author='James E. McClure',
    author_email='jamesmcclure@lbpm-sim.org',
    license='BSD 2-clause',
    packages=['pyLBPM'],
    install_requires=['pandas',
                      'pyyaml',
                      'pathlib',
                      'matplotlib',
                      'numpy',
    ],
    scripts=['scripts/install_lbpm_dependencies.sh',
             'scripts/install_lbpm.sh',
             'scripts/run_lbpm_color.sh',
             'scripts/run_lbpm_permeability.sh',
    ],
    classifiers=[
        'Development Status :: 1 - Planning',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',  
        'Operating System :: POSIX :: Linux',        
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
)
