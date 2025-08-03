#!/usr/bin/env python

import argparse
import contextlib
import functools
import http.server
import os
import os.path
import pathlib
import shutil
import subprocess
import sys
import threading
import types
import webbrowser


# Sphinx' command scripts, as defined by sphinx' own setup.py
#
# Unfortunately we cannot just go for the pythonic way by importing Sphinx' main
# modules and execute them in our process space. This is because Sphinx actually
# imports the target modules to be able to process them, mechanically implying
# the usual issues due to the way the Python's import machinery is implemented.
# At least in CPython.
#
# For instance, some code artifacts may remain in memory between two calls to
# the sphinx.cmd.build command, with docstrings referencing a class that does
# not actually exist anymore since last run. Due to a renaming or a move to an
# other namespace for instance. This invariably leads to Sphinx having an
# inconsistent behavior and complaining about unknown artifacts.
SPHINX_SCRIPT_BUILD = "sphinx.cmd.build"
# SPHINX_SCRIPT_APIDOC = "sphinx.ext.apidoc"
# SPHINX_SCRIPT_AUTOSUMMARY = "sphinx.ext.autosummary.generate"


THIS_DIR = os.path.abspath(os.path.dirname(__file__))

SPHINX_SOURCE_DIR = THIS_DIR
SPHINX_BUILD_DIR = os.path.join(THIS_DIR, "_build")

SPHINX_HTML_BUILD_DIR = os.path.join(SPHINX_BUILD_DIR, "html")
SPHINX_HTML_STATIC_DIR = os.path.join(THIS_DIR, "_static")


class QuietHTTPHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass


def die(*objs, exit_code=1, **kwargs):
    kwargs["file"] = sys.stderr
    kwargs["flush"] = True
    print("ERROR:", *objs, **kwargs)
    sys.exit(exit_code)


def get_python_cmd():
    if sys.executable:
        return sys.executable

    return "python" + str(sys.version_info[0])


def _invoke_sphinx_build(*args, **kwargs):
    kwargs.setdefault("cwd", THIS_DIR)
    cmd = [get_python_cmd(), "-B", "-m", SPHINX_SCRIPT_BUILD] + list(args)
    res = subprocess.run(cmd, **kwargs)
    return res.returncode


def _pre_sphinx_html(context):
    """Everything that must be done before a call to ``sphinx-build -b html``"""
    # sphinx-build fails if these directories do not exist
    for path in (SPHINX_BUILD_DIR, SPHINX_HTML_STATIC_DIR):
        with contextlib.suppress(FileExistsError):
            os.mkdir(path)


def _post_sphinx_html(context):
    """Everything that must be done after a call to ``sphinx-build -b html``"""
    pass


def _clean_sphinx_html():
    with contextlib.suppress(FileNotFoundError):
        shutil.rmtree(SPHINX_HTML_BUILD_DIR)


def _clean_sphinx_all():
    with contextlib.suppress(FileNotFoundError):
        shutil.rmtree(SPHINX_BUILD_DIR)

    with contextlib.suppress(FileNotFoundError, OSError):  # OSError: dir not empty
        os.rmdir(SPHINX_HTML_STATIC_DIR)


def do_clean(args):
    _clean_sphinx_all()


def do_build_html(args):
    http_server = None
    http_thread = None
    http_url = None
    home_html_file = pathlib.Path(SPHINX_HTML_BUILD_DIR, "index.html")

    # cleanup first?
    if args.rebuild:
        _clean_sphinx_html()

    leave = False
    try:
        while not leave:
            if args.serve:
                print("")
                print("")
                print("*" * 75)
                print("*" * 75)

            # generate documentation
            context = types.SimpleNamespace()
            _pre_sphinx_html(context)
            # exit_code = sphinx_build_cmd.main([
            #     "-b", "html", SPHINX_SOURCE_DIR, SPHINX_HTML_BUILD_DIR] +
            #     args.extra_args)
            exit_code = _invoke_sphinx_build(
                "-b", "html", SPHINX_SOURCE_DIR, SPHINX_HTML_BUILD_DIR,
                *args.extra_args)
            _post_sphinx_html(context)
            del context

            print("")
            if home_html_file.exists():
                print("HTML home:", home_html_file.as_uri())

            # leave the interactive loop if --server not specified
            if not args.serve:
                # ... but open web browser before if requested
                # it feels more consistent to test the existence of the
                # index.html file than doing a exit_code == 0 test here
                if args.browse:
                    if home_html_file.exists():
                        webbrowser.open_new(home_html_file.as_uri())

                return exit_code

            # spacer
            print("")

            # launch the http service if not up already
            if not http_thread:
                # prepare http handler class
                http_handler_class = functools.partial(
                    QuietHTTPHandler, directory=SPHINX_HTML_BUILD_DIR)
                # http_handler_class.protocol_version = "HTTP/1.0"

                # create the http server object
                http_server = http.server.ThreadingHTTPServer(
                    (args.bind, args.port), http_handler_class)

                # create thread object
                http_thread = threading.Thread(target=http_server.serve_forever)
                http_thread.daemon = True

                # launch thread
                http_thread.start()

                # build http url to docs
                if not args.bind or args.bind == "0.0.0.0":
                    url_host = "localhost"
                elif ":" in args.bind:
                    url_host = "[" + args.bind + "]"
                else:
                    url_host = args.bind
                http_url = "http://{}:{}/".format(url_host, args.port)
                del url_host

            print("Listening on", http_url)
            print("")

            # enter interactive mode
            while True:
                try:
                    ans = input(
                        "(B)uild, (R)ebuild, bro(W)se, (C)lean, (Q)uit? [B] ")
                    ans = ans.strip().lower()

                    if not ans or ans == "b":
                        print("")
                        break
                    elif ans == "r":
                        _clean_sphinx_html()
                        print("")
                        break
                    elif ans == "w":
                        webbrowser.open_new(http_url)
                        continue
                    elif ans == "c":
                        _clean_sphinx_all()  # _clean_sphinx_html()
                        continue
                    elif ans in ("q", "quit", "exit"):
                        leave = True
                        break
                    else:
                        print("Invalid input. Try again.")
                        continue
                except KeyboardInterrupt:
                    leave = True
                    break
                except Exception as exc:
                    print("An exception occurred:", str(exc))
                    print("")
    finally:
        if http_server:
            print("Shutting down HTTP server...")
            http_server.shutdown()  # blocking call
            print("HTTP server shut down.")


def do_unknown(args):
    die("unknown action or no action specified")
    return 1


def main(args=None):
    if args is None:
        args = sys.argv[1:]

    # split args if a double dash "--" is found
    try:
        idx = args.index("--")
        extra_args = args[idx+1:]
        args = args[0:idx]
    except ValueError:
        extra_args = []

    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.set_defaults(
        action_func=do_unknown,
        extra_args=extra_args)
    subparsers = parser.add_subparsers()

    # action: clean
    parser_clean = subparsers.add_parser(
        "clean", aliases=[], allow_abbrev=False,
        help="Cleanup documentation output directory")
    parser_clean.set_defaults(action_func=do_clean)

    # action: html
    parser_html = subparsers.add_parser(
        "html", aliases=[], allow_abbrev=False,
        help="Generate documentation in HTML format")
    parser_html.add_argument(
        "--browse", "-w", action="store_true",
        help=(
            "Launch system's default web browser with the homepage of the "
            "generated documentation open. Only if --serve is not used."))
    parser_html.add_argument(
        "--rebuild", "-r", action="store_true",
        help=(
            "Rebuild documentation instead of just updating it. This fully "
            "cleanups the output directory first."))
    parser_html.add_argument(
        "--serve", "-s", action="store_true",
        help=(
            "Launch an HTTP service to serve the result and enter in "
            "interactive mode"))
    parser_html.add_argument(
        "--bind", "-b", metavar="HOST", default="localhost",
        help="The local HTTP host to bind to (default: %(default)s)")
    parser_html.add_argument(
        "--port", "-p", metavar="PORT", default=8008, type=int,
        help="The HTTP listen port (default: %(default)s)")
    parser_html.set_defaults(action_func=do_build_html)

    args = parser.parse_args(args)

    return args.action_func(args)


if __name__ == "__main__":
    if not sys.flags.optimize:
        sys.dont_write_bytecode = True

    sys.exit(main(sys.argv[1:]))
