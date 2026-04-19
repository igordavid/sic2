# __main__.py — allows running the package directly with `python -m sic2`.
#
# When Python sees `python -m sic2` it looks for a __main__.py inside the
# sic2 package and runs it. This file simply delegates to the CLI entry point
# so both `sic2 scan .` and `python -m sic2 scan .` behave identically.

from sic2.cli import main

if __name__ == "__main__":
    # The `standalone_mode=True` default in click means it handles exceptions
    # and calls sys.exit() for us, so we don't need any extra error handling.
    main()
