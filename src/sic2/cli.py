# cli.py — the command-line interface (CLI) for sic2.
#
# This file is the entry point: when a user types `sic2 scan ./myproject`
# in their terminal, Python calls the `main` function defined here.
#
# We use the `click` library to define commands and options declaratively.
# click handles argument parsing, help text generation, and error messages
# so we don't have to write that boilerplate ourselves.

from __future__ import annotations

from pathlib import Path  # object-oriented file-path handling

import click  # third-party CLI framework

from sic2 import reporter, scanner  # our own modules


# ---------------------------------------------------------------------------
# Root command group
# ---------------------------------------------------------------------------
# @click.group() turns `main` into a command group — a parent command that
# has sub-commands (like `git` has `git commit`, `git push`, etc.).

@click.group()
@click.version_option("0.1.0", prog_name="sic2")  # enables `sic2 --version`
def main() -> None:
    """sic2 — scan source code for leaked secrets."""
    # This function body is intentionally empty.
    # click uses the docstring above as the help text for `sic2 --help`.


# ---------------------------------------------------------------------------
# `sic2 scan` sub-command
# ---------------------------------------------------------------------------

@main.command("scan")
@click.argument(
    "path",
    # click.Path validates the argument exists on disk before our code runs.
    type=click.Path(exists=True, path_type=Path),
)
@click.option(
    "--format",
    "output_format",          # maps the CLI flag to the Python variable name
    type=click.Choice(["text", "json"], case_sensitive=False),
    default="text",
    show_default=True,        # shows "(default: text)" in --help output
    help="Output format.",
)
@click.option(
    "--no-colour",
    is_flag=True,             # presence of the flag means True, absence means False
    default=False,
    help="Disable ANSI colour codes in text output.",
)
def scan_cmd(path: Path, output_format: str, no_colour: bool) -> None:
    """Scan PATH for secrets.

    PATH can be a file or a directory. When a directory is given, sic2
    recursively scans every text file inside it.

    \b
    Examples:
      sic2 scan .
      sic2 scan src/config.py --format json
    """
    # `\b` in a click docstring disables click's automatic line-wrapping for
    # the block that follows, which keeps the examples neatly formatted.

    click.echo(f"Scanning {path} …")

    # Delegate the actual scanning to scanner.scan_path().
    findings = scanner.scan_path(path)

    # Choose how to display results based on the --format flag.
    if output_format == "json":
        reporter.print_json(findings)
    else:
        reporter.print_text(findings, use_colour=not no_colour)

    # Print a summary line and exit with code 1 if secrets were found
    # (so CI pipelines can detect failures automatically).
    reporter.summarise(findings)
