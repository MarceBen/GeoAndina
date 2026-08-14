
from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.exceptions import InvalidSignature

EXPECTED_PRODUCT = "GeoAndina"


def canonical_bytes(data: dict[str, Any]) -> bytes:
   
    return json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")


def load_embedded_public_key(pem_bytes: bytes) -> Ed25519PublicKey:
    key = serialization.load_pem_public_key(pem_bytes)
    if not isinstance(key, Ed25519PublicKey):
        raise TypeError("Clave pública embebida inválida (no es Ed25519).")
    return key


def verify_license_file(
    license_path: Path,
    public_key: Ed25519PublicKey,
    current_machine_id: str,
    expected_product: str = EXPECTED_PRODUCT,
) -> tuple[bool, str]:
    try:
        raw = Path(license_path).read_text(encoding="utf-8")
        license_obj = json.loads(raw)
    except Exception:
        return False, "El archivo de licencia está corrupto o no es válido."

    data = license_obj.get("data")
    signature_b64 = license_obj.get("signature")
    if not data or not signature_b64:
        return False, "El archivo de licencia tiene un formato inesperado."

    try:
        signature = base64.b64decode(signature_b64)
    except Exception:
        return False, "La firma del archivo de licencia está mal codificada."

    try:
        public_key.verify(signature, canonical_bytes(data))
    except InvalidSignature:
        return False, "La licencia fue modificada o no es auténtica (firma inválida)."

    if data.get("product") != expected_product:
        return False, f"Esta licencia no corresponde a {expected_product}."

    if str(data.get("machine_id", "")).strip().lower() != current_machine_id.strip().lower():
        return False, "Esta licencia fue emitida para otra computadora."

    return True, "Licencia válida."
