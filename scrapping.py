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
        # Configure Git user si nécessaire (tu peux commenter si déjà configuré globalement)
        subprocess.run(["git", "config", "--global", "user.email", "ton_email@example.com"], check=True)
        subprocess.run(["git", "config", "--global", "user.name", "TonNomGit"], check=True)

        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", commit_message], check=True)
        subprocess.run(["git", "push"], check=True)
        print("Commit et push Git effectués avec succès.")
    except subprocess.CalledProcessError as e:
        print(f"Erreur lors du commit/push Git : {e}")

# --- Configuration Telegram (À REMPLIR PAR TES INFORMATIONS) ---
TELEGRAM_BOT_TOKEN = "7741033479:AAGsYS9YumE_Fn4ISt7nNNwpL2NVfr8X5v4" # Ton token
TELEGRAM_CHAT_ID = ["5597205494", "5127101598"]     # Ton chat ID


# Définir la page de connexion et la page cible (restent globales)
LOGIN_URL = "https://fr.surebet.com/users/sign_in"
TARGET_URL = "https://fr.surebet.com/valuebets"

# --- Fonction pour envoyer un message Telegram ---
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

# --- Fonction principale qui encapsule le scraping et l'envoi ---
async def main_scrape_and_notify():
    driver = None # Initialiser driver à None pour le bloc finally
    try:
        # --- Configuration et Initialisation du navigateur (Déplacé ICI) ---
        options = webdriver.ChromeOptions()

        # Désactiver le mode 'navigator.webdriver' (une signature de Selenium)
        options.add_argument("--disable-blink-features=AutomationControlled")

        # Utiliser un User-Agent réaliste et aléatoire
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/120.0"
        ]
        options.add_argument(f"user-agent={random.choice(user_agents)}")

        # Désactiver certaines fonctionnalités qui peuvent être détectées
        options.add_argument("--headless=new")  # ou "--headless" si la version de Chrome est ancienne
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-extensions")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")

        driver = webdriver.Chrome(options=options)

        tmp_profile_dir = tempfile.mkdtemp()
        options.add_argument(f"--user-data-dir={tmp_profile_dir}")

        # --- Intégration de selenium-stealth (Déplacé ICI) ---
        stealth(driver,
                languages=["fr-FR", "fr"],
                vendor="Google Inc.",
                platform="Win32",
                webgl_vendor="Intel Inc.",
                renderer="ANGLE (Intel, Intel(R) Iris(R) Xe Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)",
                fix_hairline=True,
                )

        wait = WebDriverWait(driver, 20)

        # --- Processus de CONNEXION ---
        print("Début du processus de connexion...")
        driver.get(LOGIN_URL) 

        email_field = wait.until(EC.presence_of_element_located((By.NAME, "user[email]")))
        username = "mathieu.dujardin1@orange.fr" # Ton nom d'utilisateur (dernière valeur fournie)
        password = "BEJmp13450!" # Ton mot de passe

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

        time.sleep(random.uniform(5, 10)) # Attendre le chargement

        driver.get(TARGET_URL)
        time.sleep(random.uniform(5, 10)) # Attendre le chargement
                    
        # --- DÉBUT DU SCRAPING ---
        current_request_time = datetime.now()
        today_date_str = current_request_time.strftime("%Y-%m-%d")
        today_date_str = datetime.now().strftime('%Y-%m-%d')
        
        folder = './data'

        if not os.path.exists(folder):
            os.makedirs(folder)

        DATABASE_FILE = f"{folder}/valuebets_database_{today_date_str}.xlsx"

        # Si le fichier du jour n'existe pas encore, on est dans un nouveau jour
        if not os.path.exists(DATABASE_FILE):
            print(f"📅 Nouveau jour détecté : {today_date_str}")
            
            # Envoi du fichier Excel d'hier si existant
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

        # --- Gestion de la base de données (fichier Excel) ---
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

            required_cols = ['bookmaker', 'event', 'bet']
            
            if not df_existing.empty and all(col in df_existing.columns for col in required_cols):
                df_existing['unique_key'] = df_existing['bookmaker'].astype(str) + df_existing['event'].astype(str) + df_existing['bet'].astype(str)
            else:
                df_existing = pd.DataFrame(columns=required_cols + ['request_time'])

            if all(col in df_new_scrape.columns for col in required_cols):
                df_new_scrape['unique_key'] = df_new_scrape['bookmaker'].astype(str) + df_new_scrape['event'].astype(str) + df_new_scrape['bet'].astype(str)
            else:
                print("Erreur: Colonnes requises manquantes dans le DataFrame nouvellement scrapé.")
                df_new_scrape = pd.DataFrame()

            if not df_new_scrape.empty and not df_existing.empty:
                new_entries = df_new_scrape[~df_new_scrape['unique_key'].isin(df_existing['unique_key'])]
            else:
                new_entries = df_new_scrape.copy()

            if 'unique_key' in df_existing.columns:
                df_existing = df_existing.drop(columns=['unique_key'])
            if 'unique_key' in new_entries.columns:
                new_entries = new_entries.drop(columns=['unique_key'])

            if not new_entries.empty:
                df_final = pd.concat([df_existing, new_entries], ignore_index=True)
                print(f"{len(new_entries)} nouvelles entrées ajoutées à la base de données.")
                
                # --- Réordonnancement des colonnes ---
                cols = df_final.columns.tolist()
                if 'request_time' in cols:
                    cols.remove('request_time')
                    cols.insert(0, 'request_time')
                    df_final = df_final[cols]
                
                df_final.to_excel(DATABASE_FILE, index=False)
                print(f"Base de données mise à jour et sauvegardée dans '{DATABASE_FILE}'. Taille totale: {len(df_final)}.")

                # Commit & push automatique du fichier Excel et autres changements
                git_commit_push(commit_message=f"Mise à jour valuebets {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

                # --- Envoi d'UN SEUL message avec toutes les nouvelles lignes ---
                print("Préparation de l'envoi du message Telegram consolidé...")
                telegram_messages = []
                
                # Ajout d'un en-tête au message
                telegram_messages.append(
                    f"✨ <b>Nouvelles Value Bets détectées, </b> (j'ai trouvé {len(new_entries)} nouveaux bets)\n"
                    f"Heure du scan: {current_request_time.strftime('%H:%M:%S')}\n\n"
                )
                
                # En-tête des colonnes pour la lisibilité
                header_line = "<code>{:<10} {:<20} {:<15} {:<6} {:<8}</code>".format(
                    "Bookmaker", "Événement", "Pari", "Cote", "Overval."
                )
                telegram_messages.append(header_line)
                telegram_messages.append("<code>" + "-" * 75 + "</code>") 
                
                for index, row in new_entries.iterrows():
                    # Applique le filtre overvalue > 6% ici
                    overvalue_cleaned = float(row['overvalue'].replace('%', '').replace(',', '.'))
                    if overvalue_cleaned > 6:
                        # Formatage de chaque ligne avec un alignement fixe pour la lisibilité
                        line = "<code>{:<10} {:<20} {:<15} {:<6} {:<8}</code>".format(
                            row['bookmaker'],
                            row['event'],
                            row['bet'],
                            row['odd'],
                            row['overvalue']
                        )
                        telegram_messages.append(line)

                if len(telegram_messages) > 3: # Si il y a plus que l'en-tête et la ligne de séparation
                    full_message = "\n".join(telegram_messages)
                    
                    if len(full_message) > 4000:
                        print(f"ATTENTION: Le message Telegram est très long ({len(full_message)} caractères). Il pourrait être tronqué ou échouer.")
                        
                    await send_telegram_message(full_message)
                else:
                    print("Aucune nouvelle entrée avec overvalue > 6% n'a été trouvée pour être notifiée.")
                    await send_telegram_message(
                        f"🟢 Nouveaux value bets, mais aucune overvalue > 6% détectée lors du scan de {current_request_time.strftime('%H:%M:%S')}."
                    )

            else:
                df_final = df_existing
                print("Aucune nouvelle entrée trouvée pour être ajoutée.")
                await send_telegram_message(
                    f"🟢 Aucune nouvelle Value Bet détectée lors du scan de {current_request_time.strftime('%H:%M:%S')}."
                )

        else:
            print("\nAucune donnée de valuebet n'a pu être collectée lors de ce rafraîchissement. La base de données n'est pas mise à jour.")
            await send_telegram_message(
                f"🔴 Échec du scraping à {current_request_time.strftime('%H:%M:%S')}. Aucune donnée n'a pu être collectée."
            )

        print("\nCycle de scraping terminé.")

    except Exception as e:
        print(f"Une erreur est survenue : {e}")
        import traceback
        traceback.print_exc()
        print("Fermeture du navigateur suite à une erreur.")
        await send_telegram_message(f"🚨 Erreur lors du scraping : {e}\nVérifiez le script ou le site.")
    finally:
        if driver is not None and driver.service.is_connectable(): # Vérifier si driver a été initialisé
            print("Fermeture du navigateur.")
            driver.quit()

# --- Nouvelle fonction pour planifier les exécutions ---
async def schedule_runs():
    print(f"\n--- DÉBUT DE L'EXÉCUTION DU SCRIPT À {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")
    await main_scrape_and_notify()
        
    print(f"\n--- FIN DE L'EXÉCUTION). ---")
    
# --- Exécution de la fonction asynchrone pour la planification ---
if __name__ == "__main__":
    try:
        asyncio.run(schedule_runs())
    except KeyboardInterrupt:
        print("\nPlanification interrompue par l'utilisateur.")
        # Le finally de main_scrape_and_notify s'occupera de fermer le driver si une exécution était en cours.
    except Exception as e:
        print(f"Une erreur fatale est survenue dans la boucle de planification : {e}")
        import traceback
        traceback.print_exc()