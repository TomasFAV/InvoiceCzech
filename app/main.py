import argparse

from client.Client import Client
from invoice_enhancer.InvoiceEnhancer import InvoiceEnhancer
from invoice_annotator.DataAnnotator import DataAnnotator
from invoices_generator.InvoiceGenerator import InvoiceGenerator


def run_annotator() -> None:
    app = DataAnnotator()
    app.run()


def run_client() -> None:
    app = Client()
    app.run()


def generate_invoices(start: int, end: int, count: int, random_template:bool) -> None:
    InvoiceGenerator.generate(start, end, count, random_template)


def enhance_invoices(metadata_path: str, copies: int) -> None:
    InvoiceEnhancer.enhance(metadata_path, copies)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Spouštění anotátoru, klienta a generování/enhancování faktur."
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser(
        "annotator",
        help="Spustí DataAnnotator"
    )

    subparsers.add_parser(
        "client",
        help="Spustí Client"
    )

    generate_parser = subparsers.add_parser(
        "generate",
        help="Vygeneruje faktury"
    )
    generate_parser.add_argument(
        "--train",
        type=int,
        required=True,
        help="Počet iterací generování faktur pro trénování"
    )
    generate_parser.add_argument(
        "--test",
        type=int,
        required=True,
        help="Počet iterací generování faktur pro testování"
    )
    generate_parser.add_argument(
        "--validation",
        type=int,
        required=True,
        help="Počet iterací generování faktur pro validaci"
    )

    generate_parser.add_argument(
        "--random",
        action="store_true",
        help="Použít random layout šablony"
    )

    enhance_parser = subparsers.add_parser(
        "enhance",
        help="Enhancuje faktury"
    )
    enhance_parser.add_argument(
        "--metadata-path",
        type=str,
        required=True,
        help="Cesta k metadata layoutlmv3 JSONL souboru"
    )
    enhance_parser.add_argument(
        "--samples",
        type=int,
        required=True,
        help="Počet upravených verzí jednu původní fakturu"
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.command == "annotator":
        run_annotator()
    elif args.command == "client":
        run_client()
    elif args.command == "generate":
        generate_invoices(args.train, args.test, args.validation, args.random)
    elif args.command == "enhance":
        enhance_invoices(args.metadata_path, args.samples)


if __name__ == "__main__":
    main()