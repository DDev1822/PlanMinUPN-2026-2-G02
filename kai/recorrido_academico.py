"""Compatibilidad del punto de entrada antiguo con el controlador G02 activo."""
from __future__ import annotations

import json
from pathlib import Path
import sys

import recorrido_g02

REQUEST = Path(__file__).resolve().parent.parent / '.kai_solicitud_recorrido_academico.json'
process = recorrido_g02.process


def main():
    if sys.argv[1:] != ['procesar-pendiente']:
        print('Uso: python kai/recorrido_academico.py procesar-pendiente', file=sys.stderr)
        return 2
    try:
        if REQUEST.stat().st_size > 65536:
            raise ValueError('Solicitud demasiado larga')
        request = json.loads(REQUEST.read_text(encoding='utf-8-sig'))
        result = process(request)
        REQUEST.unlink()
        print(json.dumps(result, ensure_ascii=True, allow_nan=False))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({'ok': False, 'error': str(exc), 'solicitud_conservada': REQUEST.exists()},
                         ensure_ascii=True), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
