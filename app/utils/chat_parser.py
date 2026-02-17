import re
from datetime import datetime


def _clean_line(x: str) -> str:
    x = (x or "").strip()
    x = x.replace("\u200e", "").replace("\u200f", "")
    return x


def parse_whatsapp_chat(text: str):
    """
    Basic WhatsApp export parser (works for most formats).

    Supports:
    12/31/23, 9:30 PM - Name: message
    31/12/23, 21:30 - Name: message
    """

    lines = [l for l in (text or "").splitlines() if l.strip()]
    events = []

    # Format examples:
    # 12/31/23, 9:30 PM - John: Hello
    # 31/12/23, 21:30 - John: Hello
    pattern = re.compile(
        r"^(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}),\s*(\d{1,2}:\d{2})(?:\s*([APap][Mm]))?\s*-\s*(.*?):\s*(.*)$"
    )

    for raw in lines:
        raw = _clean_line(raw)
        m = pattern.match(raw)
        if not m:
            continue

        date_str = m.group(1)
        time_str = m.group(2)
        ampm = m.group(3)
        sender = m.group(4).strip()
        msg = m.group(5).strip()

        # Normalize datetime
        dt = None
        try:
            # Try DD/MM/YY
            dt = datetime.strptime(date_str, "%d/%m/%y")
        except Exception:
            try:
                dt = datetime.strptime(date_str, "%m/%d/%y")
            except Exception:
                try:
                    dt = datetime.strptime(date_str, "%d/%m/%Y")
                except Exception:
                    try:
                        dt = datetime.strptime(date_str, "%m/%d/%Y")
                    except Exception:
                        dt = None

        # Normalize time
        if dt is not None:
            try:
                if ampm:
                    dt_time = datetime.strptime(f"{time_str} {ampm.upper()}", "%I:%M %p").time()
                else:
                    dt_time = datetime.strptime(time_str, "%H:%M").time()
                dt = datetime.combine(dt.date(), dt_time)
            except Exception:
                pass

        events.append(
            {
                "datetime": dt.isoformat() if dt else None,
                "date": date_str,
                "time": f"{time_str} {ampm}".strip() if ampm else time_str,
                "sender": sender,
                "message": msg,
            }
        )

    return events


def chat_to_summary(events, max_lines=12):
    """
    Converts parsed events into a short summary text.
    """
    if not events:
        return ""

    # Keep only meaningful lines
    important = []
    for e in events:
        msg = (e.get("message") or "").strip()
        if not msg:
            continue
        if "<media omitted>" in msg.lower():
            continue
        important.append(e)

    # limit
    important = important[:max_lines]

    lines = []
    for e in important:
        sender = e.get("sender", "Unknown")
        msg = e.get("message", "")
        lines.append(f"{sender}: {msg}")

    return "\n".join(lines)


def extract_threat_obscene_signals(events):
    """
    Quick heuristic signal extractor.
    """
    text = " ".join([(e.get("message") or "").lower() for e in events])

    signals = []

    if any(w in text for w in ["kill", "hurt", "beat", "ruin", "destroy", "threat"]):
        signals.append("Threat / intimidation language detected")

    if any(w in text for w in ["nude", "nudes", "porn", "sex", "dick", "boobs"]):
        signals.append("Obscene / sexual language detected")

    if any(w in text for w in ["blackmail", "leak", "share your video", "send your photo"]):
        signals.append("Possible blackmail / sextortion language detected")

    if any(w in text for w in ["boss", "manager", "hr", "office"]):
        signals.append("Possible workplace context detected")

    return signals
