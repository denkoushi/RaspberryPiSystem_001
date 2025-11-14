#!/usr/bin/env python3
"""
Prototype script for OnSiteLogistics handheld reader.

Reads barcode data from a USB HID scanner (tested with MINJCODE MJ2818A)
via evdev, drives the Waveshare 2.13" e-Paper HAT V4, and manages a
two-step workflow (A-code then B-code).

Run on Raspberry Pi Zero 2 W:
    sudo ./handheld_scan_display.py
"""

import argparse
import json
import logging
import os
import sqlite3
import sys
import time
import uuid
from pathlib import Path
from typing import Callable, Optional, Union

import requests
from evdev import InputDevice, categorize, ecodes
from PIL import Image, ImageDraw, ImageFont
from logging.handlers import RotatingFileHandler

EPAPER_LIB_DEFAULT = Path.home() / "e-Paper/RaspberryPi_JetsonNano/python/lib"
if EPAPER_LIB_DEFAULT.exists():
    sys_path_entry = str(EPAPER_LIB_DEFAULT)
    if sys_path_entry not in sys.path:
        sys.path.append(sys_path_entry)

try:
    from waveshare_epd import epd2in13_V4  # legacy module name
except ImportError:
    try:
        from waveshare_epaper import epd2in13_V4  # pip package name
    except ImportError:
        import sys

        alt_paths = []
        sudo_user = os.environ.get("SUDO_USER")
        if sudo_user:
            alt_paths.append(Path("/home") / sudo_user / "e-Paper/RaspberryPi_JetsonNano/python/lib")

        alt_paths.append(Path(__file__).resolve().parent / "e-Paper/RaspberryPi_JetsonNano/python/lib")
        alt_paths.append(Path("/home") / Path.home().name / "e-Paper/RaspberryPi_JetsonNano/python/lib")

        for candidate in alt_paths:
            if candidate.exists():
                if str(candidate) not in sys.path:
                    sys.path.append(str(candidate))
                try:
                    from waveshare_epd import epd2in13_V4  # type: ignore
                    break
                except ImportError:
                    continue
        else:
            raise

# ====== Configurable parameters ======
# Default HID/serial candidates (override via env vars when必要)
DEFAULT_HID_PATHS_RAW = [
    os.environ.get("HANDHELD_INPUT_DEVICE"),
    "/dev/input/by-id/usb-MINJCODE_MINJCODE_MJ2818A_00000000011C-event-kbd",
    "/dev/input/by-path/platform-3f980000.usb-usb-0:1:1.0-event-kbd",
    "/dev/input/event0",
]
DEFAULT_HID_PATHS = [h for h in DEFAULT_HID_PATHS_RAW if h]
DEVICE_PATH = Path(next(iter(DEFAULT_HID_PATHS), "/dev/input/event0"))
SERIAL_FORCE_PATHS = [
    Path(p.strip())
    for p in os.environ.get("HANDHELD_SERIAL_PATHS", "/dev/minjcode0,/dev/ttyACM0").split(",")
    if p.strip()
]
SERIAL_GLOBS = ("minjcode*", "ttyACM*", "ttyUSB*")
SERIAL_BAUDS = (115200, 57600, 38400, 9600)
SERIAL_PROBE_RETRIES = 10
SERIAL_PROBE_DELAY_S = 1.0
HEADLESS_MODE = os.environ.get("HANDHELD_HEADLESS", "").lower() in {"1", "true", "yes", "on"}
IDLE_TIMEOUT_S = 30
PARTIAL_BATCH_N = 5
CANCEL_CODES = {"CANCEL", "RESET"}
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_SIZE = 22
MIRRORCTL_DISABLED = os.environ.get("HANDHELD_DISABLE_MIRRORCTL", "").lower() in {"1", "true", "yes", "on"}

CONFIG_SEARCH_PATHS = [
    os.environ.get("ONSITE_CONFIG"),
    "/etc/onsitelogistics/config.json",
    str(Path(__file__).resolve().parent.parent / "config" / "config.json"),
]
DEFAULT_TIMEOUT = 3


class KeyboardScanner:
    """Read barcode strings via evdev from a HID scanner."""

    LETTER_PREFIX = "KEY_"

    SYMBOL_MAP = {
        "KEY_0": "0",
        "KEY_1": "1",
        "KEY_2": "2",
        "KEY_3": "3",
        "KEY_4": "4",
        "KEY_5": "5",
        "KEY_6": "6",
        "KEY_7": "7",
        "KEY_8": "8",
        "KEY_9": "9",
        "KEY_MINUS": "-",
        "KEY_EQUAL": "=",
        "KEY_SLASH": "/",
        "KEY_DOT": ".",
        "KEY_COMMA": ",",
        "KEY_SPACE": " ",
        "KEY_SEMICOLON": ";",
        "KEY_APOSTROPHE": "'",
        "KEY_BACKSLASH": "\\",
    }

    def __init__(self, device_path: Path):
        if not device_path.exists():
            raise FileNotFoundError(f"Scanner input device not found: {device_path}")
        self.device = InputDevice(str(device_path))
        self._buffer: list[str] = []
        self._shift = False
        try:
            self.device.grab()
            self._grabbed = True
        except OSError:
            self._grabbed = False

    def read_code(self, timeout: float = 0.1) -> Optional[str]:
        """Return a single barcode as text (delimited by Enter)."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            event = self.device.read_one()
            if event is None:
                time.sleep(0.01)
                continue
            if event.type != ecodes.EV_KEY:
                continue

            key = categorize(event)
            code = key.keycode
            state = key.keystate

            if code in ("KEY_LEFTSHIFT", "KEY_RIGHTSHIFT"):
                self._shift = bool(state)
                continue

            if state != 1:  # process only key-down events
                continue

            if code == "KEY_ENTER":
                text = "".join(self._buffer)
                self._buffer.clear()
                return text

            if code == "KEY_BACKSPACE":
                if self._buffer:
                    self._buffer.pop()
                continue

            ch = self._translate(code)
            if ch:
                self._buffer.append(ch.upper() if self._shift else ch)

        return None

    def close(self) -> None:
        if getattr(self, "_grabbed", False):
            try:
                self.device.ungrab()
            except OSError:
                pass
        self.device.close()

    def _translate(self, code: str) -> Optional[str]:
        if code in ("KEY_SEMICOLON",):
            return ":" if self._shift else ";"
        if code in ("KEY_APOSTROPHE",):
            return '"' if self._shift else "'"
        if code in ("KEY_COMMA",):
            return "<" if self._shift else ","
        if code in ("KEY_DOT",):
            return ">" if self._shift else "."
        if code in ("KEY_SLASH",):
            return "?" if self._shift else "/"
        if code in ("KEY_MINUS",):
            return "_" if self._shift else "-"
        if code in self.SYMBOL_MAP:
            return self.SYMBOL_MAP[code]
        if code.startswith(self.LETTER_PREFIX) and len(code) == 5:
            # e.g. KEY_A, KEY_Z
            return code[-1].lower()
        return None


class SerialScanner:
    """Read barcode strings via USB CDC (virtual serial) devices."""

    def __init__(self, device_path: Path, baudrate: int):
        try:
            import serial
        except ImportError as exc:
            raise RuntimeError(
                "pyserial is required to use USB-Serial scanners. "
                "Install it with 'sudo apt install python3-serial' or 'pip install pyserial'."
            ) from exc

        import serial  # type: ignore

        self._device_path = device_path
        self._baudrate = baudrate
        self._serial = serial.Serial(str(device_path), baudrate=baudrate, timeout=0.1)

    def read_code(self, timeout: float = 0.1) -> Optional[str]:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            line = self._serial.readline().decode(errors="ignore").strip()
            if line:
                return line
            time.sleep(0.01)
        return None

    def close(self) -> None:
        try:
            self._serial.close()
        except Exception:  # pragma: no cover - best effort cleanup
            pass


class EPaperUI:
    """Helper to render status on Waveshare 2.13\" e-Paper (V4)."""

    def __init__(self):
        self.epd = epd2in13_V4.EPD()
        self.epd.init()

        # For V4, width/height are swapped when rotated to landscape
        self.width, self.height = self.epd.height, self.epd.width
        self.line_height = self.height // 3
        self.font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
        self._partial_count = 0

        base = self._render("A: WAIT", "B: WAIT", "Status: WAIT")
        self.epd.displayPartBaseImage(self.epd.getbuffer(base))

    def _render(self, line_a: str, line_b: str, line_status: str) -> Image.Image:
        image = Image.new("1", (self.width, self.height), 255)
        draw = ImageDraw.Draw(image)
        draw.text((4, 2 + 0 * self.line_height), line_a, font=self.font, fill=0)
        draw.text((4, 2 + 1 * self.line_height), line_b, font=self.font, fill=0)
        draw.text((4, 2 + 2 * self.line_height), line_status, font=self.font, fill=0)
        return image

    def update(self, a: Optional[str] = None, b: Optional[str] = None,
               status: Optional[str] = None, force_full: bool = False) -> None:
        line_a = a if a is not None else "A: WAIT"
        line_b = b if b is not None else "B: WAIT"
        line_status = status if status is not None else "Status: WAIT"

        print(f"[UI] update -> a='{line_a}' b='{line_b}' status='{line_status}' force_full={force_full}")

        image = self._render(line_a, line_b, line_status)

        if force_full or self._partial_count >= PARTIAL_BATCH_N:
            buf = self.epd.getbuffer(image)
            self.epd.display(buf)
            # Reset the partial base so subsequent partial updates reflect this frame
            self.epd.displayPartBaseImage(buf)
            self._partial_count = 0
        else:
            self.epd.displayPartial(self.epd.getbuffer(image))
            self._partial_count += 1

    def sleep(self) -> None:
        self.epd.sleep()


class NullUI:
    """No-op UI used when HEADLESS_MODE is enabled."""

    def update(self, *_, **__):
        pass

    def sleep(self):
        pass


def format_line(prefix: str, code: str, done: bool, max_len: int = 24) -> str:
    suffix = " [OK]" if done else ""
    text = code
    ellipsis = "..."
    if len(text) > max_len:
        text = text[: max_len - len(ellipsis)] + ellipsis
    return f"{prefix}: {text}{suffix}"


class ScanTransmitter:
    def __init__(self, config: dict, mirrorctl_hook: Optional[Callable[[int, int], None]] = None):
        self.scan_api_url = config["api_url"]
        self.api_token = config["api_token"]
        self.device_id = config["device_id"]
        self.timeout = config.get("timeout_seconds", DEFAULT_TIMEOUT)
        self.logistics_api_url = config.get("logistics_api_url")
        self.logistics_default_from = config.get("logistics_default_from", "UNKNOWN")
        self.logistics_status = config.get("logistics_status", "completed")
        self.logistics_enabled = bool(self.logistics_api_url)
        self.mirrorctl_hook = mirrorctl_hook
        queue_path = Path(config.get("queue_db_path", "~/.onsitelogistics/scan_queue.db")).expanduser()
        queue_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(queue_path)
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS scan_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target TEXT NOT NULL,
                payload TEXT NOT NULL,
                retries INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            )
            """
        )
        self.conn.commit()
        self._migrate_queue_schema()

    def _migrate_queue_schema(self) -> None:
        cursor = self.conn.execute("PRAGMA table_info(scan_queue)")
        columns = {row[1] for row in cursor.fetchall()}
        if "target" not in columns:
            self.conn.execute("ALTER TABLE scan_queue ADD COLUMN target TEXT")
            self.conn.execute("UPDATE scan_queue SET target=?", (self.scan_api_url,))
            self.conn.commit()

    def _request_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }

    def _post(self, target_url: str, payload: dict) -> bool:
        try:
            logging.info("Posting to %s: %s", target_url, payload.get("scan_id") or payload.get("job_id"))
            response = requests.post(
                target_url,
                json=payload,
                headers=self._request_headers(),
                timeout=self.timeout,
            )
            response.raise_for_status()
            logging.info("Server accepted payload (target=%s)", target_url)
            return True
        except requests.RequestException as exc:
            logging.warning(
                "Failed to post payload to %s (%s): %s",
                target_url,
                payload.get("scan_id") or payload.get("job_id"),
                exc,
            )
            return False

    def enqueue(self, target_url: str, payload: dict, retries: int = 0) -> None:
        logging.info(
            "Queueing payload for retry (target=%s, id=%s)",
            target_url,
            payload.get("scan_id") or payload.get("job_id"),
        )
        self.conn.execute(
            "INSERT INTO scan_queue (target, payload, retries, created_at) VALUES (?, ?, ?, ?)",
            (
                target_url,
                json.dumps(payload),
                retries,
                time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            ),
        )
        self.conn.commit()

    def _report_mirrorctl(self, success: int, failure: int) -> None:
        if self.mirrorctl_hook and (success or failure):
            try:
                self.mirrorctl_hook(success, failure)
            except Exception as exc:  # pragma: no cover - defensive log
                logging.warning("mirrorctl hook failed: %s", exc)

    def send_or_queue(self, target_url: str, payload: dict, *, count_for_mirror: bool = True) -> bool:
        success = self._post(target_url, payload)
        if not success:
            self.enqueue(target_url, payload, payload.get("retries", 0))
        if count_for_mirror:
            self._report_mirrorctl(1 if success else 0, 0 if success else 1)
        return success

    def drain(self, limit: int = 20) -> bool:
        cursor = self.conn.execute(
            "SELECT id, target, payload, retries FROM scan_queue ORDER BY id ASC LIMIT ?",
            (limit,),
        )
        rows = cursor.fetchall()
        processed = False
        success_seen = 0
        failure_seen = 0
        for row_id, target_url, payload_json, retries in rows:
            payload = json.loads(payload_json)
            payload["retries"] = retries + 1
            if self._post(target_url, payload):
                self.conn.execute("DELETE FROM scan_queue WHERE id=?", (row_id,))
                self.conn.commit()
                processed = True
                success_seen += 1
            else:
                self.conn.execute(
                    "UPDATE scan_queue SET retries=? WHERE id=?",
                    (payload["retries"], row_id),
                )
                self.conn.commit()
                failure_seen += 1
                break
        if success_seen or failure_seen:
            self._report_mirrorctl(success_seen, failure_seen)
        return processed

    def queue_size(self) -> int:
        cursor = self.conn.execute("SELECT COUNT(*) FROM scan_queue")
        (count,) = cursor.fetchone()
        return int(count or 0)

    def send_logistics_job(self, part_code: str, to_location: str) -> None:
        if not self.logistics_enabled:
            return
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        payload = {
            "job_id": f"job-{uuid.uuid4().hex}",
            "part_code": part_code,
            "from_location": self.logistics_default_from or "UNKNOWN",
            "to_location": to_location,
            "status": self.logistics_status or "completed",
            "requested_at": timestamp,
            "updated_at": timestamp,
            "retries": 0,
        }
        self.send_or_queue(self.logistics_api_url, payload, count_for_mirror=False)


def iter_serial_candidates():
    dev_root = Path("/dev")
    for pattern in SERIAL_GLOBS:
        for path in sorted(dev_root.glob(pattern)):
            yield path


def create_scanner():
    def _info(message: str) -> None:
        logging.info(message)
        print(message)

    def _warn(message: str) -> None:
        logging.warning(message)
        print(message)

    forced = SERIAL_FORCE_PATHS or []
    for dev in forced:
        if not dev.exists():
            _warn(f"[SERIAL] forced path missing: {dev}")
            continue
        for baud in SERIAL_BAUDS:
            try:
                _info(f"[SERIAL] forcing {dev} @ {baud}bps")
                scanner = SerialScanner(dev, baud)
                _info(f"[SERIAL] scanner ready: {dev} (serial {baud}bps)")
                return scanner
            except Exception as exc:
                _warn(f"[SERIAL] force failed ({dev} @ {baud}): {exc}")

    for attempt in range(SERIAL_PROBE_RETRIES):
        _info(f"[SERIAL] probe attempt {attempt + 1}/{SERIAL_PROBE_RETRIES}")
        for candidate in iter_serial_candidates():
            for baud in SERIAL_BAUDS:
                try:
                    _info(f"[SERIAL] probing {candidate} @ {baud}bps")
                    scanner = SerialScanner(candidate, baud)
                    _info(f"[SERIAL] scanner ready: {candidate} (serial {baud}bps)")
                    return scanner
                except Exception as exc:
                    _warn(f"[SERIAL] probe failed ({candidate} @ {baud}): {exc}")
                    continue
        if attempt < SERIAL_PROBE_RETRIES - 1:
            _warn(
                f"[SERIAL] not detected on attempt {attempt + 1}. retrying in {SERIAL_PROBE_DELAY_S:.1f}s"
            )
            time.sleep(SERIAL_PROBE_DELAY_S)

    _warn(f"[SERIAL] not detected after retries. falling back to HID {DEVICE_PATH}")
    for hid in DEFAULT_HID_PATHS:
        if not hid:
            continue
        hid_path = Path(hid)
        if not hid_path.exists():
            continue
        scanner = KeyboardScanner(hid_path)
        _info(f"[SERIAL] HID fallback: {scanner.description()}")
        return scanner

    scanner = KeyboardScanner(DEVICE_PATH)
    _info(f"[SERIAL] HID fallback: {scanner.description()}")
    return scanner


def configure_logging(config: dict) -> None:
    log_dir = Path(config.get("log_dir", "~/.onsitelogistics/logs")).expanduser()
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "handheld.log"

    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    file_handler = RotatingFileHandler(log_path, maxBytes=1_000_000, backupCount=3)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)


def load_config(config_path: Optional[str] = None) -> dict:
    if config_path:
        path = Path(config_path).expanduser()
        if not path.is_file():
            raise FileNotFoundError(f"Config file not found: {path}")
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)

    for candidate in CONFIG_SEARCH_PATHS:
        if candidate and Path(candidate).expanduser().is_file():
            with open(Path(candidate).expanduser(), "r", encoding="utf-8") as fh:
                return json.load(fh)
    raise FileNotFoundError(
        "Config file not found. Set ONSITE_CONFIG or create /etc/onsitelogistics/config.json"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="OnSiteLogistics handheld controller")
    parser.add_argument(
        "--config",
        help="Path to config.json (overrides ONSITE_CONFIG/search order)",
    )
    parser.add_argument(
        "--drain-only",
        action="store_true",
        help="Process queued scans then exit",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    configure_logging(config)
    mirror_hook = None
    if not MIRRORCTL_DISABLED:
        try:
            from handheld.src import mirrorctl_client

            mirror_hook = mirrorctl_client.build_hook()
        except Exception as exc:  # pragma: no cover - best effort log
            logging.warning("mirrorctl hook unavailable: %s", exc)
    else:
        logging.info("mirrorctl hook disabled via HANDHELD_DISABLE_MIRRORCTL")

    transmitter = ScanTransmitter(config, mirrorctl_hook=mirror_hook)

    if args.drain_only:
        logging.info("Drain-only mode: processing queued scans")
        processed = True
        while processed:
            processed = transmitter.drain()
            if processed and transmitter.queue_size() > 0:
                time.sleep(0.5)
        logging.info("Drain-only mode completed. Pending queue size: %s", transmitter.queue_size())
        return

    scanner = create_scanner()
    if HEADLESS_MODE:
        logging.info("HEADLESS mode enabled (HANDHELD_HEADLESS). Skipping EPaperUI init.")
        ui: Union[EPaperUI, NullUI] = NullUI()
    else:
        ui = EPaperUI()

    state = "WAIT_A"
    code_a: Optional[str] = None
    last_action = time.monotonic()

    try:
        ui.update(force_full=True)

        while True:
            now = time.monotonic()
            if state != "WAIT_A" and now - last_action > IDLE_TIMEOUT_S:
                print("[WARN] Timeout. Resetting state.")
                state = "WAIT_A"
                code_a = None
                ui.update(status="Status: TIMEOUT→RESET", force_full=True)
                continue

            code = scanner.read_code(timeout=0.3)
            if code is None:
                continue

            last_action = now
            code = code.strip()
            if not code:
                print("[DEBUG] Empty code detected. Ignoring.")
                continue
            print(f"[DEBUG] Read code: {code}")
            print(f"[STATE] before transition: state={state}, code_a={code_a}")

            if code.upper() in CANCEL_CODES:
                state = "WAIT_A"
                code_a = None
                ui.update(status="Status: CANCELLED")
                continue

            # Handle based on current state (prefixes are hints only)
            if state == "WAIT_A":
                code_a = code[2:].strip() if code.startswith("A:") else code
                state = "WAIT_B"
                print(f"[STATE] transition -> WAIT_B (code_a={code_a})")
                ui.update(a=format_line("A", code_a, True), status="Status: A RECEIVED")
                continue

            # state == WAIT_B
            code_b = code[2:].strip() if code.startswith("B:") else code
            if code_a is None:
                ui.update(b=format_line("B", code_b, False),
                          status="Status: ONLY B → RESET", force_full=True)
            else:
                ui.update(a=format_line("A", code_a, True),
                          b=format_line("B", code_b, True),
                          status="Status: DONE", force_full=True)
                payload = {
                    "order_code": code_a,
                    "location_code": code_b,
                    "device_id": transmitter.device_id,
                    "metadata": {
                        "scan_id": str(uuid.uuid4()),
                        "scanned_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        "retries": 0,
                    },
                }
                transmitter.send_or_queue(transmitter.scan_api_url, payload)
                transmitter.send_logistics_job(code_a, code_b)
            transmitter.drain()
            print(f"[STATE] transition -> WAIT_A (completed) with B={code_b}")
            state = "WAIT_A"
            code_a = None

    except KeyboardInterrupt:
        print("\n[INFO] Stopped by user.")
    finally:
        if scanner:
            try:
                scanner.close()
            except AttributeError:
                pass
        ui.sleep()
        transmitter.conn.close()


if __name__ == "__main__":
    main()
