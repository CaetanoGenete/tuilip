from argparse import ArgumentParser


def on_select(options: list[str]) -> int:
    from tuilip_cli.select import select

    return select(options)


def main() -> int:
    parser = ArgumentParser()
    subparsers = parser.add_subparsers(required=True)

    parser_select = subparsers.add_parser("select")
    parser_select.set_defaults(func=on_select)
    parser_select.add_argument(
        "options",
        nargs="*",
        help="Lines to choose between",
    )

    args = parser.parse_args()
    return args.func(args.options)
