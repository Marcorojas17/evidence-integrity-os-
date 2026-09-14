"""Verificador CLI independiente.

Uso:
    evidence-verify --package case.evidence
    evidence-verify --package case.evidence --json
    evidence-verify --package case.evidence --trust-store ca_chain.pem
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from src.evidence.verifier import VerifyResult, verify_evidence_package

RESET = "\x1b[0m"
GREEN = "\x1b[32m"
RED = "\x1b[31m"
CYAN = "\x1b[36m"
DIM = "\x1b[2m"
YELLOW = "\x1b[33m"


def _print_step(index: int, total: int, name: str, passed: bool, detail: str) -> None:
    mark = f"{GREEN}ok{RESET}" if passed else f"{RED}fail{RESET}"
    line = f"[{index}/{total}] {name} ... {mark}"
    if detail:
        line += f" {DIM}({detail}){RESET}"
    print(line)


def _run(args: argparse.Namespace) -> int:
    package_path = Path(args.package)
    if not package_path.is_file():
        print(f"{RED}Error:{RESET} archivo no encontrado: {package_path}")
        return 2

    package_bytes = package_path.read_bytes()
    result: VerifyResult = verify_evidence_package(package_bytes)

    if args.json:
        print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
        return 0 if result.valid else 1

    total = len(result.steps)
    for i, step in enumerate(result.steps, start=1):
        _print_step(i, total, step.name, step.passed, step.detail)

    print()
    if result.valid:
        print(f"{CYAN}->{RESET} RESULTADO: {GREEN}VALIDO{RESET}")
        if result.evidence_id:
            print(f"{DIM}   evidence_id: {result.evidence_id}{RESET}")
        if result.manifest_digest:
            print(f"{DIM}   manifest_digest: {result.manifest_digest}{RESET}")
        if result.tsa_gen_time:
            print(f"{DIM}   tsa_gen_time: {result.tsa_gen_time}{RESET}")
        if result.revocation_state:
            print(f"{DIM}   revocacion: {result.revocation_state}{RESET}")
        return 0

    print(f"{CYAN}->{RESET} RESULTADO: {RED}INVALIDO{RESET}")
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="evidence-verify",
        description="Verifica un paquete .evidence de forma independiente.",
    )
    parser.add_argument(
        "--package",
        required=True,
        help="Ruta al archivo .evidence",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Salida en JSON para integracion",
    )
    parser.add_argument(
        "--trust-store",
        default=None,
        help="(pendiente) Ruta a la cadena de confianza para validar el certificado de firma",
    )
    args = parser.parse_args(argv)
    return _run(args)


if __name__ == "__main__":
    sys.exit(main())
