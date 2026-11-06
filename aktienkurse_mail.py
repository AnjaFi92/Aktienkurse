"""
Aktienkurse abrufen und per E-Mail verschicken – Version für GitHub Actions.
Läuft bei jedem Aufruf genau EINMAL (den Zeitplan übernimmt GitHub).
Die Mail ist eine HTML-Tabelle mit Tageshoch und Tagestief in Grün.

Die Zugangsdaten kommen aus den GitHub-Secrets:
    GMAIL_ADRESSE, GMAIL_APP_PASSWORT, EMPFAENGER
"""

import os
import smtplib
from datetime import datetime
from zoneinfo import ZoneInfo
from email.mime.multipart import MIMEMultipart
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

GRUEN = "#1a8f3c"
ROT = "#c62828"

ABSENDER = os.environ["GMAIL_ADRESSE"]
PASSWORT = os.environ["GMAIL_APP_PASSWORT"]
EMPFAENGER = os.environ["EMPFAENGER"]

# Auf True setzen, um ausserhalb der Börsenzeit zu testen (danach wieder False!)
MANUELL = False


def boerse_offen():
    """US-Börse: Mo–Fr, 9:30–16:00 New Yorker Zeit."""
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
        return {
            "preis": preis,
            "waehrung": info["currency"],
            "veraenderung": (preis - vortag) / vortag * 100 if vortag else 0.0,
            "hoch": info["day_high"],
            "tief": info["day_low"],
        }
    except Exception as e:
        print(f"Fehler bei {symbol}: {e}")
        return None


def berichte_erstellen():
    """Gibt (Text-Version, HTML-Version) zurück."""
    text_zeilen = []
    html_zeilen = []
    zelle = 'style="padding:6px 12px; border-bottom:1px solid #ddd;"'
    zelle_r = 'style="padding:6px 12px; border-bottom:1px solid #ddd; text-align:right;"'

    for symbol, name in TICKER.items():
        d = kurs_abrufen(symbol)
        if not d:
            text_zeilen.append(f"{name} ({symbol}) – keine Daten")
            html_zeilen.append(
                f"<tr><td {zelle}><b>{name}</b> ({symbol})</td>"
                f'<td {zelle} colspan="4">keine Daten</td></tr>'
            )
            continue

        pfeil = "▲" if d["veraenderung"] >= 0 else "▼"
        farbe = GRUEN if d["veraenderung"] >= 0 else ROT
        w = d["waehrung"]

        text_zeilen.append(
            f"{name} ({symbol}): {d['preis']:.2f} {w}  {pfeil} {d['veraenderung']:+.2f}%  "
            f"| Hoch {d['hoch']:.2f}  Tief {d['tief']:.2f}"
        )
        html_zeilen.append(
            f"<tr>"
            f"<td {zelle}><b>{name}</b> ({symbol})</td>"
            f"<td {zelle_r}>{d['preis']:.2f} {w}</td>"
            f'<td {zelle_r}><span style="color:{farbe};">{pfeil} {d["veraenderung"]:+.2f}%</span></td>'
            f'<td {zelle_r}><span style="color:{GRUEN}; font-weight:bold;">{d["hoch"]:.2f}</span></td>'
            f'<td {zelle_r}><span style="color:{GRUEN}; font-weight:bold;">{d["tief"]:.2f}</span></td>'
            f"</tr>"
        )

    kopf = 'style="padding:6px 12px; background:#f2f2f2; text-align:left;"'
    html = f"""
    <html><body style="font-family:Arial, sans-serif; font-size:14px;">
    <table style="border-collapse:collapse;">
      <tr>
        <th {kopf}>Aktie</th>
        <th {kopf}>Kurs</th>
        <th {kopf}>Heute</th>
        <th {kopf}>Tageshoch</th>
        <th {kopf}>Tagestief</th>
      </tr>
      {''.join(html_zeilen)}
    </table>
    </body></html>
    """
    return "\n".join(text_zeilen), html


def mail_senden(betreff, text, html):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = betreff
    msg["From"] = ABSENDER
    msg["To"] = EMPFAENGER
    msg.attach(MIMEText(text, "plain", "utf-8"))   # Ersatz, falls HTML nicht angezeigt wird
    msg.attach(MIMEText(html, "html", "utf-8"))
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(ABSENDER, PASSWORT)
        server.send_message(msg)


def main():
    if not MANUELL and not boerse_offen():
        print("Börse geschlossen – keine Mail.")
        return
    zeit = datetime.now(ZoneInfo("Europe/Zurich")).strftime("%d.%m.%Y %H:%M")
    text, html = berichte_erstellen()
    print(text)
    mail_senden(f"Aktienkurse {zeit}", text, html)
    print("Mail gesendet.")


if __name__ == "__main__":
    main()
