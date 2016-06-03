#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os
import sys

from subprocess import call


APP_HOME = os.environ.get('APP_HOME', '/app')
APP_ENV = os.path.join(APP_HOME, '.env')
APP_ETC = os.path.join(APP_HOME, 'etc')
APP_ROOT = os.path.join(APP_HOME, 'root')


class CommandManager(object):

    def __init__(self, before_command=None, after_command=None):
        self._commands = {}
        self._before_command = before_command
        self._after_command = after_command

    def reg(self, name, with_args=False):
        def decorator(fn):
            self._commands.update({
                name: {
                    'fn': fn,
                    'with_args': with_args
                }
            })
            return fn
        return decorator

    def before_command(self):
        if self._before_command:
            self._before_command()

    def after_command(self):
        if self._after_command:
            self._after_command()

    def not_found(self, name):
        print('the command "%s" not found in busybox!' % name)

    def _next_command(self, argv):
        name = argv[0]
        argv = argv[1:]

        return name, argv

    def _extract_args(self, argv, count=None):
        if count:
            return argv[:count], argv[count:]
        else:
            return argv, []

    def run(self, argv=None):
        argv = argv if argv else sys.argv[1:]

        self.before_command()
        while argv:
            cmd_name, argv = self._next_command(argv)
            cmd_data = self._commands.get(cmd_name, None)

            if cmd_data and cmd_data.get('with_args'):
                nargs = cmd_data.get('with_args')

                if nargs is True:
                    args, argv = self._extract_args(argv)
                else:
                    args, argv = self._extract_args(argv, nargs)

                cmd_data.get('fn')(*args)
            elif cmd_data and not cmd_data.get('with_args'):
                cmd_data.get('fn')()
            else:
                self.not_found(cmd_name)

        self.after_command()


def _fix_permissions():
    print('fix permissions...')
    directories = (
        APP_HOME,
    )

    for directory in directories:
        print('fixing "%s"' % directory)
        call(
            [
                '/bin/chown',
                'user.user',
                directory
            ],
            shell=False
        )


cm = CommandManager(before_command=_fix_permissions)


@cm.reg('configure')
def cmd_configure():
    os.setgid(1000)
    os.setuid(1000)
    os.chdir(APP_HOME)
    os.environ.update(HOME='/home/user')

    print('exists virtualenv?')
    if not os.path.exists(APP_ENV):
        print('need create virtualenv')
        call(
            [
                '/usr/bin/virtualenv',
                APP_ENV,
                '--python=python3'
            ],
            shell=False
        )

    if not os.path.exists(APP_ROOT):
        print('create root application directory')
        os.mkdir(APP_ROOT)

    if not os.path.exists(os.path.join(APP_ROOT, 'requiriments.txt')):
        print('create minimal requiriments.txt')
        with open(os.path.join(APP_ROOT, 'requiriments.txt'), 'wt') as fd:
            fd.write(
                '\n'.join([
                    'Django<1.9',
                    'ipython>=4.0.0',
                    'uwsgi>=2.0.0'
                ])
            )

    print('install requiriments')
    call(
        [
            os.path.join(APP_ENV, 'bin', 'pip'),
            'install',
            '-U',
            '-r',
            os.path.join(APP_ROOT, 'requiriments.txt')
        ],
        shell=False
    )

    print('exists root app?')
    if not os.path.exists(os.path.join(APP_ROOT, 'manage.py')):
        print('initialize django project')
        call(
            [
                os.path.join(APP_ENV, 'bin', 'django-admin'),
                'startproject',
                'app',
                APP_ROOT
            ],
            shell=False
        )

    if not os.path.exists(APP_ETC):
        print('create configuration directory')
        os.mkdir(APP_ETC)

    if not os.path.exists(os.path.join(APP_ETC, 'uwsgi.yml')):
        print('create uwsgi.yml for launche server')
        with open(os.path.join(APP_ETC, 'uwsgi.yml'), 'wt') as fd:
            fd.write(
                '\n'.join([
                    'uwsgi:',
                    '  master: 1',
                    '  workers: 1',
                    '  threads: 4',
                    '  http: 0.0.0.0:8000',
                    '  wsgi: app.wsgi',
                    '  home: %s' % APP_ENV,
                    '  env: PYTHONPATH=%s' % APP_ROOT,
                    '  py-autoreload: 1'
                ])
            )


@cm.reg('shell')
def cmd_shell():
    print('open shell in app directory')
    os.setgid(1000)
    os.setuid(1000)
    os.chdir(APP_HOME)
    os.environ.update(HOME='/home/user')

    call('/bin/bash'.split(' '), shell=False)


@cm.reg('start')
def cmd_start():
    print('start server')
    os.setgid(1000)
    os.setuid(1000)
    os.chdir(APP_HOME)
    os.environ.update(HOME='/home/user')

    call(
        [
            os.path.join(APP_ENV, 'bin', 'uwsgi'),
            '--yml',
            os.path.join(APP_ETC, 'uwsgi.yml')
        ],
        shell=False
    )


@cm.reg('root_shell')
def cmd_root_shell():
    print('open shell with root')
    call('/bin/bash'.split(' '), shell=False)


if __name__ == '__main__':
    cm.run()
