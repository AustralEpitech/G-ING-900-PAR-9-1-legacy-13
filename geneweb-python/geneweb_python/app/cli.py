import argparse
import sys

CLI_TOOLS = [
    # "gwd" implemented with real logic below (custom parser)
    # "gwu" implemented with real logic below (custom parser)
    # "gwb2ged" implemented with real logic below (custom parser)
    # "ged2gwb" implemented with real logic below (custom parser)
    # "check" implemented with real logic below (custom parser)
    # "gwdiff" implemented with real logic below (custom parser)
    # "gwexport" implemented with real logic below (custom parser)
    # "gwc" implemented with real logic below (custom parser)
]


def _placeholder(name: str):
    def run(args: argparse.Namespace):
        print(f"{name}: placeholder CLI.\n")
        print("This command will be implemented to mirror the OCaml behavior.")
        print("Status and milestones are tracked in geneweb-python/PORTING_STATUS.md.")
        if getattr(args, "verbose", False):
            print("Args:", vars(args))
    return run


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="geneweb-python",
        description="Python reimplementation scaffold of GeneWeb commands",
    )
    subparsers = parser.add_subparsers(dest="command", metavar="<command>")

    for tool in CLI_TOOLS:
        sub = subparsers.add_parser(tool, help=f"Run {tool} (placeholder)")
        sub.add_argument("--verbose", action="store_true", help="Verbose output")
        sub.set_defaults(func=_placeholder(tool))

    # Real implementation: gwb2ged
    from .gwb2ged import export_gedcom
    gwb2ged = subparsers.add_parser("gwb2ged", help="Export Database (pickle) to GEDCOM (minimal)")
    gwb2ged.add_argument("--db-file", default="database.pkl", help="Path to Database pickle file")
    gwb2ged.add_argument("-o", "--output", default="-", help="Output file path or '-' for stdout")
    gwb2ged.add_argument("--verbose", action="store_true", help="Verbose output")

    def _run_gwb2ged(args: argparse.Namespace):
        from core.database import Database
        db = Database(storage_file=args.db_file)
        if args.output == "-":
            import sys as _sys
            export_gedcom(db, _sys.stdout)
        else:
            with open(args.output, "w", encoding="utf-8") as f:
                export_gedcom(db, f)

    gwb2ged.set_defaults(func=_run_gwb2ged)

    # Real implementation: ged2gwb
    from .ged2gwb import import_gedcom
    ged2gwb = subparsers.add_parser("ged2gwb", help="Import GEDCOM into Database (pickle)")
    ged2gwb.add_argument("input", help="Path to GEDCOM file")
    ged2gwb.add_argument("--db-file", default="database.pkl", help="Path to Database pickle file")
    ged2gwb.add_argument("--verbose", action="store_true", help="Verbose output")

    def _run_ged2gwb(args: argparse.Namespace):
        from core.database import Database
        db = Database(storage_file=args.db_file)
        import_gedcom(args.input, db)
        if args.verbose:
            print(f"Imported {args.input} into {args.db_file}")

    ged2gwb.set_defaults(func=_run_ged2gwb)

    # Real implementation: gwd (HTTP daemon)
    from .gwd import serve
    gwd = subparsers.add_parser("gwd", help="Start GeneWeb HTTP daemon (REST API)")
    gwd.add_argument("--db-file", default="database.pkl", help="Path to Database pickle file")
    gwd.add_argument("--host", default="127.0.0.1", help="Host to bind (default: 127.0.0.1)")
    gwd.add_argument("--port", type=int, default=2317, help="Port to bind (default: 2317)")
    gwd.add_argument("--verbose", action="store_true", help="Verbose output")

    def _run_gwd(args: argparse.Namespace):
        from core.database import Database
        db = Database(storage_file=args.db_file)
        serve(db, host=args.host, port=args.port)

    gwd.set_defaults(func=_run_gwd)

    # Real implementation: check (data validation)
    from .check import check_database, print_issues
    check_cmd = subparsers.add_parser("check", help="Run data consistency checks")
    check_cmd.add_argument("--db-file", default="database.pkl", help="Path to Database pickle file")
    check_cmd.add_argument("--verbose", action="store_true", help="Verbose output")

    def _run_check(args: argparse.Namespace):
        from core.database import Database
        db = Database(storage_file=args.db_file)
        issues = check_database(db)
        print_issues(issues)
        return 0 if not any(i.severity == "error" for i in issues) else 1

    check_cmd.set_defaults(func=_run_check)

    # Real implementation: gwu (utilities)
    from .gwu import stats, print_stats, optimize, print_optimize_results, export_names, list_surnames, print_surnames
    gwu = subparsers.add_parser("gwu", help="Database utilities")
    gwu_subparsers = gwu.add_subparsers(dest="gwu_command", metavar="<subcommand>")

    # gwu stats
    gwu_stats = gwu_subparsers.add_parser("stats", help="Display database statistics")
    gwu_stats.add_argument("--db-file", default="database.pkl", help="Path to Database pickle file")
    gwu_stats.add_argument("--verbose", action="store_true", help="Verbose output")

    def _run_gwu_stats(args: argparse.Namespace):
        from core.database import Database
        db = Database(storage_file=args.db_file)
        result = stats(db)
        print_stats(result)

    gwu_stats.set_defaults(func=_run_gwu_stats)

    # gwu optimize
    gwu_optimize = gwu_subparsers.add_parser("optimize", help="Optimize database (remove orphans, fix broken links)")
    gwu_optimize.add_argument("--db-file", default="database.pkl", help="Path to Database pickle file")
    gwu_optimize.add_argument("--verbose", action="store_true", help="Verbose output")

    def _run_gwu_optimize(args: argparse.Namespace):
        from core.database import Database
        db = Database(storage_file=args.db_file)
        result = optimize(db)
        print_optimize_results(result)
        db.save()
        if args.verbose:
            print(f"Database saved to {args.db_file}")

    gwu_optimize.set_defaults(func=_run_gwu_optimize)

    # gwu export-names
    gwu_export_names = gwu_subparsers.add_parser("export-names", help="Export all unique names to a text file")
    gwu_export_names.add_argument("--db-file", default="database.pkl", help="Path to Database pickle file")
    gwu_export_names.add_argument("-o", "--output", required=True, help="Output text file")
    gwu_export_names.add_argument("--verbose", action="store_true", help="Verbose output")

    def _run_gwu_export_names(args: argparse.Namespace):
        from core.database import Database
        db = Database(storage_file=args.db_file)
        export_names(db, args.output)
        if args.verbose:
            print(f"Exported names to {args.output}")

    gwu_export_names.set_defaults(func=_run_gwu_export_names)

    # gwu list-surnames
    gwu_list_surnames = gwu_subparsers.add_parser("list-surnames", help="List all surnames with counts")
    gwu_list_surnames.add_argument("--db-file", default="database.pkl", help="Path to Database pickle file")
    gwu_list_surnames.add_argument("--limit", type=int, help="Limit output to top N surnames")
    gwu_list_surnames.add_argument("--verbose", action="store_true", help="Verbose output")

    def _run_gwu_list_surnames(args: argparse.Namespace):
        from core.database import Database
        db = Database(storage_file=args.db_file)
        surnames = list_surnames(db)
        print_surnames(surnames, limit=args.limit)

    gwu_list_surnames.set_defaults(func=_run_gwu_list_surnames)

    # Real implementation: gwdiff (database comparison)
    from .gwdiff import compare_databases, print_diff_report, export_diff_json
    gwdiff = subparsers.add_parser("gwdiff", help="Compare two databases and show differences")
    gwdiff.add_argument("db1", help="Path to first database (baseline)")
    gwdiff.add_argument("db2", help="Path to second database (comparison target)")
    gwdiff.add_argument("-o", "--output", help="Export diff as JSON to this file")
    gwdiff.add_argument("--verbose", action="store_true", help="Verbose output")

    def _run_gwdiff(args: argparse.Namespace):
        from core.database import Database
        db1 = Database(storage_file=args.db1)
        db2 = Database(storage_file=args.db2)
        report = compare_databases(db1, db2)
        print_diff_report(report, args.db1, args.db2)
        if args.output:
            export_diff_json(report, args.output)

    gwdiff.set_defaults(func=_run_gwdiff)

    # Real implementation: gwexport (export to multiple formats)
    from .gwexport import export_csv, export_json, export_html
    gwexport = subparsers.add_parser("gwexport", help="Export database to multiple formats")
    gwexport_subparsers = gwexport.add_subparsers(dest="gwexport_command", metavar="<format>")

    # gwexport csv
    gwexport_csv = gwexport_subparsers.add_parser("csv", help="Export to CSV files (persons.csv, families.csv)")
    gwexport_csv.add_argument("--db-file", default="database.pkl", help="Path to Database pickle file")
    gwexport_csv.add_argument("-o", "--output-dir", default=".", help="Output directory for CSV files")
    gwexport_csv.add_argument("--verbose", action="store_true", help="Verbose output")

    def _run_gwexport_csv(args: argparse.Namespace):
        from core.database import Database
        db = Database(storage_file=args.db_file)
        export_csv(db, args.output_dir)

    gwexport_csv.set_defaults(func=_run_gwexport_csv)

    # gwexport json
    gwexport_json = gwexport_subparsers.add_parser("json", help="Export to JSON (full database dump)")
    gwexport_json.add_argument("--db-file", default="database.pkl", help="Path to Database pickle file")
    gwexport_json.add_argument("-o", "--output", default="database.json", help="Output JSON file")
    gwexport_json.add_argument("--verbose", action="store_true", help="Verbose output")

    def _run_gwexport_json(args: argparse.Namespace):
        from core.database import Database
        db = Database(storage_file=args.db_file)
        export_json(db, args.output)

    gwexport_json.set_defaults(func=_run_gwexport_json)

    # gwexport html
    gwexport_html = gwexport_subparsers.add_parser("html", help="Export to HTML (family tree view)")
    gwexport_html.add_argument("--db-file", default="database.pkl", help="Path to Database pickle file")
    gwexport_html.add_argument("-o", "--output", default="family_tree.html", help="Output HTML file")
    gwexport_html.add_argument("--verbose", action="store_true", help="Verbose output")

    def _run_gwexport_html(args: argparse.Namespace):
        from core.database import Database
        db = Database(storage_file=args.db_file)
        export_html(db, args.output)

    gwexport_html.set_defaults(func=_run_gwexport_html)

    # Real implementation: gwc (interactive console)
    from .gwc import run_console
    gwc = subparsers.add_parser("gwc", help="Interactive console for database queries")
    gwc.add_argument("--db-file", default="database.pkl", help="Path to Database pickle file")
    gwc.add_argument("--verbose", action="store_true", help="Verbose output")

    def _run_gwc(args: argparse.Namespace):
        from core.database import Database
        db = Database(storage_file=args.db_file)
        run_console(db)

    gwc.set_defaults(func=_run_gwc)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 2
    args.func(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
