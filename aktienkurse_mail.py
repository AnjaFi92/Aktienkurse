"""
Aktienkurse alle 3 Minuten abrufen und per E-Mail verschicken.

Installation (einmalig):
    pip install yfinance

Vor dem Start unten bei "E-MAIL EINSTELLUNGEN" deine Daten eintragen.
Start:   python aktienkurse_mail.py
Beenden: Ctrl+C
"""

import time
import smtplib
from datetime import datetime
from email.mime.text import MIMEText

import yfinance as yf

# ----------------- AKTIEN -----------------
TICKER = {
    "INTC": "Intel Corp",
    "NVDA": "Nvidia",
    "RDDT": "Reddit",
    "SNAP": "Snap",
    "SPCX": "Space Exploration (SpaceX)",
    "SMCI": "Super Micro Computer",
    "TSLA": "Tesla",
}
INTERVALL_SEKUNDEN = 10 * 60   # 10 Minuten

# ----------------- E-MAIL EINSTELLUNGEN -----------------
# Gmail:   smtp.gmail.com, Port 587  (App-Passwort nötig!)
# Outlook: smtp.office365.com, Port 587
# GMX:     mail.gmx.net, Port 587
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
ABSENDER = "anjafischer92@gmail.com"
PASSWORT = "pzoq tpkc wvib vwfr"        # NICHT dein normales Passwort, sondern App-Passwort
EMPFAENGER = "anja-fischer@hotmail.com"

# Nur während US-Börsenzeiten senden? (15:30–22:00 Schweizer Zeit, Mo–Fr)
NUR_BOERSENZEITEN = True


def boerse_offen():
    jetzt = datetime.now()
    if jetzt.weekday() >= 5:          # Samstag/Sonntag
        return False
    minuten = jetzt.hour * 60 + jetzt.minute
    return 15 * 60 + 30 <= minuten <= 22 * 60


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
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(ABSENDER, PASSWORT)
        server.send_message(msg)


def main():
    print("Kurs-Mailer gestartet. Beenden mit Ctrl+C\n")
    try:
        while True:
            if NUR_BOERSENZEITEN and not boerse_offen():
                print(f"{datetime.now():%H:%M} – Börse geschlossen, warte ...")
            else:
                zeit = datetime.now().strftime("%d.%m.%Y %H:%M")
                text = bericht_erstellen()
                print(f"=== {zeit} ===\n{text}\n")
                try:
                    mail_senden(f"Aktienkurse {zeit}", text)
                    print("→ Mail gesendet\n")
                except Exception as e:
                    print(f"→ Mail-Fehler: {e}\n")
            time.sleep(INTERVALL_SEKUNDEN)
    except KeyboardInterrupt:
        print("\nBeendet.")


if __name__ == "__main__":
    main()
