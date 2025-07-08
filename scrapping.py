from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import time
import random
from bs4 import BeautifulSoup
from selenium_stealth import stealth
import pandas as pd
from datetime import datetime, timedelta # Importe timedelta pour l'heure du prochain run
import os
import tempfile

# --- Importation pour Telegram ---
from telegram import Bot # Importe la classe Bot
import asyncio # Nécessaire pour exécuter les fonctions async de Telegram
import subprocess

from telegram import InputFile

async def send_telegram_file(file_path, caption=None):
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    for chat_id in TELEGRAM_CHAT_ID:
        try:
            with open(file_path, 'rb') as f:
                await bot.send_document(chat_id=chat_id, document=InputFile(f), caption=caption or "")
                print(f"✅ Fichier {file_path} envoyé à {chat_id}.")
        except Exception as e:
            print(f"❌ Erreur lors de l'envoi du fichier à {chat_id} : {e}")

def git_commit_push(commit_message="Mise à jour des données valuebets"):
    try:
        subprocess.run(["git", "config", "--global", "user.email", "ton_email@example.com"], check=True)
        subprocess.run(["git", "config", "--global", "user.name", "TonNomGit"], check=True)

        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", commit_message], check=True)
        subprocess.run(["git", "push"], check=True)
        print("Commit et push Git effectués avec succès.")
    except subprocess.CalledProcessError as e:
        print(f"Erreur lors du commit/push Git : {e}")

# --- Configuration Telegram (À REMPLIR PAR TES INFORMATIONS) ---
TELEGRAM_BOT_TOKEN = "7741033479:AAGsYS9YumE_Fn4ISt7nNNwpL2NVfr8X5v4"
TELEGRAM_CHAT_ID = ["5597205494", "5127101598"]

LOGIN_URL = "https://fr.surebet.com/users/sign_in"
TARGET_URL = "https://fr.surebet.com/valuebets"

async def send_telegram_message(message):
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    chat_ids_to_send = TELEGRAM_CHAT_ID if isinstance(TELEGRAM_CHAT_ID, list) else [TELEGRAM_CHAT_ID]

    for chat_id in chat_ids_to_send:
        try:
            await bot.send_message(chat_id=chat_id, text=message, parse_mode='HTML')
            print(f"Message Telegram envoyé avec succès à l'ID de chat : {chat_id}.")
        except Exception as e:
            print(f"Échec de l'envoi du message Telegram à l'ID de chat {chat_id} : {e}")
            print(f"Vérifiez le CHAT_ID ({chat_id}).")

async def main_scrape_and_notify():
    driver = None
    try:
        options = webdriver.ChromeOptions()
        options.add_argument("--disable-blink-features=AutomationControlled")
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/120.0"
        ]
        options.add_argument(f"user-agent={random.choice(user_agents)}")
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-extensions")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")

        driver = webdriver.Chrome(options=options)

        tmp_profile_dir = tempfile.mkdtemp()
        options.add_argument(f"--user-data-dir={tmp_profile_dir}")

        stealth(driver,
                languages=["fr-FR", "fr"],
                vendor="Google Inc.",
                platform="Win32",
                webgl_vendor="Intel Inc.",
                renderer="ANGLE (Intel, Intel(R) Iris(R) Xe Graphics Direct3D11 vs_5_0 ps_5_0)",
                fix_hairline=True,
                )

        wait = WebDriverWait(driver, 20)

        print("Début du processus de connexion...")
        driver.get(LOGIN_URL)

        email_field = wait.until(EC.presence_of_element_located((By.NAME, "user[email]")))
        username = "mathieu.dujardin1@orange.fr"
        password = "BEJmp13450!"

        for char in username:
            email_field.send_keys(char)
            time.sleep(random.uniform(0.05, 0.2))

        time.sleep(random.uniform(1, 2))

        password_field = wait.until(EC.presence_of_element_located((By.NAME, "user[password]")))
        for char in password:
            password_field.send_keys(char)
            time.sleep(random.uniform(0.05, 0.2))

        time.sleep(random.uniform(1, 2))

        commit_button = wait.until(EC.element_to_be_clickable((By.NAME, "commit")))
        actions = ActionChains(driver)
        actions.move_to_element(commit_button).perform()
        time.sleep(random.uniform(0.5, 1.5))
        commit_button.click()

        time.sleep(random.uniform(5, 10))

        driver.get(TARGET_URL)
        time.sleep(random.uniform(5, 10))

        current_request_time = datetime.now()
        today_date_str = current_request_time.strftime("%Y-%m-%d")
        
        folder = './data'

        if not os.path.exists(folder):
            os.makedirs(folder)

        DATABASE_FILE = f"{folder}/valuebets_database_{today_date_str}.xlsx"

        if not os.path.exists(DATABASE_FILE):
            print(f"📅 Nouveau jour détecté : {today_date_str}")
            yesterday_date_str = (current_request_time - timedelta(days=1)).strftime('%Y-%m-%d')
            yesterday_file = f"{folder}/valuebets_database_{yesterday_date_str}.xlsx"
            
            if os.path.exists(yesterday_file):
                print(f"📤 Envoi du fichier Excel d'hier : {yesterday_file}")
                await send_telegram_file(yesterday_file, caption=f"📈 Fichier valuebets du {yesterday_date_str}")
            else:
                print(f"📁 Aucun fichier trouvé pour hier ({yesterday_file}), rien à envoyer.")
        
        print(f"\n--- Scraping des valuebets à {current_request_time.strftime('%Y-%m-%d %H:%M:%S')} ---")
        print(f"Les données seront sauvegardées dans : {DATABASE_FILE}")

        time.sleep(random.uniform(5, 10))

        print("Début du scraping des données...")
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')

        rows = soup.select('table tbody tr')
        newly_scraped_data = []

        if not rows:
            print("Aucune ligne de tableau trouvée avec le sélecteur 'table tbody tr'.")
        else:
            print(f"Nombre de lignes trouvées : {len(rows)}")
            for i, row in enumerate(rows, 1):
                cols = row.find_all('td')
                valuebet_data = [col.get_text(strip=True) for col in cols]

                if len(valuebet_data) >= 9:
                    date_raw = valuebet_data[2]
                    date_reformatted = f'{date_raw[:5]} {date_raw[5:]}'
                    
                    data_row = {
                        'bookmaker': valuebet_data[1],
                        'date': date_reformatted,
                        'event': valuebet_data[3],
                        'bet': valuebet_data[4],
                        'odd': valuebet_data[5],
                        'proba': valuebet_data[7],
                        'overvalue': valuebet_data[8],
                        'request_time': current_request_time
                    }
                    newly_scraped_data.append(data_row)
                else:
                    print(f"Valuebet {i} : Moins de colonnes que prévu ({len(valuebet_data)}). Impossible d'extraire. Données brutes : {valuebet_data}")

        if newly_scraped_data:
            df_new_scrape = pd.DataFrame(newly_scraped_data)
            print("\n--- DataFrame des nouvelles données scrapées (5 premières lignes) ---")
            print(df_new_scrape.head())

            df_existing = pd.DataFrame()
            if os.path.exists(DATABASE_FILE):
                try:
                    df_existing = pd.read_excel(DATABASE_FILE)
                    print(f"Base de données existante chargée ({len(df_existing)} entrées).")
                except pd.errors.EmptyDataError:
                    print("La base de données existante est vide.")
                except Exception as e:
                    print(f"Erreur lors du chargement de la base de données existante : {e}")
            else:
                print("Création d'une nouvelle base de données.")

            # --- Nouvelle gestion des doublons et index avec ID ---
            # Assurer que df_existing a au moins les colonnes nécessaires
            required_cols = ['bookmaker', 'event', 'bet']
            for col in required_cols:
                if col not in df_existing.columns:
                    df_existing[col] = ""

            df_new_scrape["event_short"] = df_new_scrape["event"].str[:10]
            df_existing["event_short"] = df_existing["event"].str[:10]

            df_new_scrape["ID"] = df_new_scrape["bookmaker"] + " | " + df_new_scrape["bet"] + " | " + df_new_scrape["event_short"]
            df_existing["ID"] = df_existing["bookmaker"] + " | " + df_existing["bet"] + " | " + df_existing["event_short"]

            df_new_scrape = df_new_scrape.drop_duplicates(subset="ID")
            df_existing = df_existing.drop_duplicates(subset="ID")

            df_new_scrape = df_new_scrape.set_index("ID")
            df_existing = df_existing.set_index("ID")

            new_entries = df_new_scrape.loc[~df_new_scrape.index.isin(df_existing.index)]

            if not new_entries.empty:
                df_final = pd.concat([df_existing, new_entries])
            else:
                df_final = df_existing.copy()

            print(df_final.head())
            df_final = df_final.reset_index(drop=True)  # Remettre un index simple

            df_final.to_excel(DATABASE_FILE, index=False)
            print(f"✅ Données sauvegardées dans {DATABASE_FILE} avec {len(df_final)} entrées.")

            await send_telegram_message(f"✅ Scraping terminé à {current_request_time.strftime('%Y-%m-%d %H:%M:%S')}\nNombre total d'entrées : {len(df_final)}")

            # Git commit/push
            git_commit_push()

        else:
            print("Aucune nouvelle donnée scrapée, rien à sauvegarder.")

    except Exception as e:
        print(f"Erreur critique durant le scraping ou la sauvegarde : {e}")

    finally:
        if driver:
            driver.quit()
            print("Driver fermé.")

if __name__ == "__main__":
    asyncio.run(main_scrape_and_notify())
