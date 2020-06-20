from setuptools import setup, find_packages
from pathlib import Path

from dgg_chat_bot import __version__

long_description = Path('README.md').read_text()

setup(
    name='dgg-chat-bot',
    packages=find_packages(),
    version=__version__,
    license='MIT',
    description='Build chat bots for the destiny.gg chat',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Gabriel Jablonski',
    author_email='contact@gabrieljablonski.com',
    url='https://github.com/gabrieljablonski/dgg-chat-bot',
    keywords=['chat-bot', 'chat', 'destinygg', 'dgg'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.8',
    ],
    python_requires='>=3.8',
    install_requires=[
        'dgg_chat',
    ],
)
