
from __future__ import annotations

import ctypes
import hashlib
import sys


class MachineIdError(RuntimeError):
    """Se lanza cuando no se puede obtener el Machine ID en este sistema."""


def _get_machine_guid_windows() -> str:
    import winreg  # disponible solo en Windows

    key_path = r"SOFTWARE\Microsoft\Cryptography"
    with winreg.OpenKey(
        winreg.HKEY_LOCAL_MACHINE,
        key_path,
        0,
        winreg.KEY_READ | winreg.KEY_WOW64_64KEY,
    ) as key:
        value, _ = winreg.QueryValueEx(key, "MachineGuid")
        return str(value).strip()


def _get_system_volume_serial_windows() -> str:
    """Número de serie del volumen de la unidad del sistema (ej. C:)."""
    system_drive = "C:\\"
    try:
        system_drive = (
            __import__("os").environ.get("SystemDrive", "C:") + "\\"
        )
    except Exception:
        pass

    volume_serial = ctypes.c_uint32(0)
    kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
    ok = kernel32.GetVolumeInformationW(
        ctypes.c_wchar_p(system_drive),
        None, 0,
        ctypes.byref(volume_serial),
        None, None,
        None, 0,
    )
    if not ok:
        return ""
    return format(volume_serial.value, "08X")


def get_raw_machine_identifier() -> str:
  
    if sys.platform != "win32":
        raise MachineIdError(
            "get_raw_machine_identifier() solo funciona en Windows. "
            "Este módulo está pensado para ejecutarse dentro de GeoAndina.exe "
            "en la PC del cliente."
        )
    try:
        guid = _get_machine_guid_windows()
    except OSError as exc:
        raise MachineIdError(f"No se pudo leer MachineGuid del registro: {exc}") from exc

    volume_serial = _get_system_volume_serial_windows()
    return f"{guid}|{volume_serial}"


def normalize_machine_id(raw_identifier: str) -> str:
  
    return hashlib.sha256(raw_identifier.encode("utf-8")).hexdigest()


def get_machine_id() -> str:
 
    raw = get_raw_machine_identifier()
    return normalize_machine_id(raw)


if __name__ == "__main__":
    try:
        mid = get_machine_id()
        print("Machine ID de esta computadora:")
        print(mid)
    except MachineIdError as exc:
        print(f"Error: {exc}")

    input("\nPresiona ENTER para cerrar...")
