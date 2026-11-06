"""
Aktienkurse abrufen und per E-Mail verschicken – Version für GitHub Actions.
Läuft bei jedem Aufruf genau EINMAL (den Zeitplan übernimmt GitHub).

Die Zugangsdaten kommen aus den GitHub-Secrets:
    GMAIL_ADRESSE, GMAIL_APP_PASSWORT, EMPFAENGER
"""

import os
import smtplib
from datetime import datetime
from zoneinfo import ZoneInfo
from email.mime.text import MIMEText

import yfinance as yf

TICKER = {
    "INTC": "Intel Corp",
    "NVDA": "Nvidia",
    "RDDT": "Reddit",
    "SNAP": "Snap",
    "SPCX": "Space Exploration (SpaceX)",
    "SMCI": "Super Micro Computer",
    "TSLA": "Tesla",
}

ABSENDER = os.environ["GMAIL_ADRESSE"]
PASSWORT = os.environ["GMAIL_APP_PASSWORT"]
EMPFAENGER = os.environ["EMPFAENGER"]

# Beim manuellen Test über GitHub ("Run workflow") wird immer gesendet
MANUELL = os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch"


def boerse_offen():
    """US-Börse: Mo–Fr, 9:30–16:00 New Yorker Zeit (Sommerzeit wird automatisch beachtet)."""
    ny = datetime.now(ZoneInfo("America/New_York"))
    if ny.weekday() >= 5:
        return False
    minuten = ny.hour * 60 + ny.minute
    return 9 * 60 + 30 <= minuten <= 16 * 60


def kurs_abrufen(symbol):
    try:
        info = yf.Ticker(symbol).fast_info
        preis = info["last_price"]
        vortag = info["previous_close"]
        veraenderung = (preis - vortag) / vortag * 100 if vortag else 0.0
        return preis, info["currency"], veraenderung
    except Exception as e:
        print(f"Fehler bei {symbol}: {e}")
        return None


def bericht_erstellen():
    zeilen = []
    for symbol, name in TICKER.items():
        daten = kurs_abrufen(symbol)
        if daten:
            preis, waehrung, veraenderung = daten
            pfeil = "▲" if veraenderung >= 0 else "▼"
            zeilen.append(f"{name:<28} ({symbol:<5}) {preis:>10.2f} {waehrung}  "
                          f"{pfeil} {veraenderung:+.2f}%")
        else:
            zeilen.append(f"{name:<28} ({symbol:<5}) – keine Daten")
    return "\n".join(zeilen)


def mail_senden(betreff, text):
    msg = MIMEText(text, "plain", "utf-8")
    msg["Subject"] = betreff
    msg["From"] = ABSENDER
    msg["To"] = EMPFAENGER
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(ABSENDER, PASSWORT)
        server.send_message(msg)


def main():
    if not MANUELL and not boerse_offen():
        print("Börse geschlossen – keine Mail.")
        return
    zeit = datetime.now(ZoneInfo("Europe/Zurich")).strftime("%d.%m.%Y %H:%M")
    text = bericht_erstellen()
    print(text)
    mail_senden(f"Aktienkurse {zeit}", text)
    print("Mail gesendet.")


if __name__ == "__main__":
    main()
