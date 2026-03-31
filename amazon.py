import time
import random
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# Configuration
URL_BASE = "https://www.amazon.fr/s?k=laptop+ordinateur+portable&page={}"
NB_PAGES = 2
FICHIER  = "amazon_laptops.xlsx"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]


def creer_driver():
    # Lance Chrome avec les options pour eviter la detection
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(f"user-agent={random.choice(USER_AGENTS)}")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    # Supprime la signature webdriver pour ne pas etre detecte comme bot
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })
    driver.set_page_load_timeout(30)
    return driver


def nettoyer_prix(texte):
    # Convertit un texte comme "1 299,99 EUR" en float 1299.99
    try:
        return float(
            texte
            .replace("€", "")
            .replace("\xa0", "")
            .replace("\u202f", "")
            .replace(" ", "")
            .replace(",", ".")
            .strip()
        )
    except (ValueError, AttributeError):
        return None


def nettoyer_lien(href):
    # Nettoie le lien et enleve les parametres inutiles
    if not href:
        return None
    if href.startswith("/"):
        return "https://www.amazon.fr" + href.split("?")[0]
    if "amazon.fr" in href:
        return href.split("?")[0]
    return None


def extraire_produits(driver, page):
    url = URL_BASE.format(page)
    print(f"Page {page} : {url}")

    time.sleep(random.uniform(4, 7))
    driver.get(url)
    time.sleep(random.uniform(2, 3))

    # Si Amazon bloque on arrete la page
    titre_page = driver.title.lower()
    if "robot" in titre_page or "captcha" in titre_page or "excuse" in titre_page:
        print(f"Bloque par Amazon - titre recu : {driver.title}")
        return []

    # Scroll pour charger tous les produits
    for _ in range(4):
        driver.execute_script("window.scrollBy(0, 700)")
        time.sleep(random.uniform(0.6, 1.2))
    driver.execute_script("window.scrollTo(0, 0)")
    time.sleep(1)

    cards = driver.find_elements(By.CSS_SELECTOR, "div[data-component-type='s-search-result']")
    print(f"{len(cards)} produits trouves sur la page {page}")

    if not cards:
        return []

    produits = []
    vus = set()

    for card in cards:
        try:
            # Titre
            titre = None
            for sel in ["span.a-text-normal", "h2 span", "h2 a span"]:
                els = card.find_elements(By.CSS_SELECTOR, sel)
                for el in els:
                    txt = el.text.strip()
                    if txt and len(txt) > 10:
                        titre = txt
                        break
                if titre:
                    break

            if not titre or titre in vus:
                continue
            vus.add(titre)

            # Prix - Amazon cache les prix dans des spans invisibles
            prix = None
            for sel in ["span.a-price span.a-offscreen", "span.a-price-whole"]:
                els = card.find_elements(By.CSS_SELECTOR, sel)
                for el in els:
                    txt = driver.execute_script("return arguments[0].textContent", el).strip()
                    p = nettoyer_prix(txt)
                    if p and p > 30:
                        prix = p
                        break
                if prix:
                    break

            # Note
            note = "N/A"
            try:
                note_el = card.find_element(By.CSS_SELECTOR, "span.a-icon-alt")
                note = driver.execute_script(
                    "return arguments[0].textContent", note_el
                ).strip().split(" ")[0].replace(",", ".")
            except Exception:
                pass

            # Lien - on essaie deux selecteurs differents
            lien = None
            try:
                lien_el = card.find_element(By.CSS_SELECTOR, "h2 a")
                lien = nettoyer_lien(lien_el.get_attribute("href"))
            except Exception:
                pass

            if not lien:
                try:
                    lien_el = card.find_element(By.CSS_SELECTOR, "a.a-link-normal")
                    lien = nettoyer_lien(lien_el.get_attribute("href"))
                except Exception:
                    pass

            produits.append({
                "Titre"    : titre,
                "Prix (€)" : prix,
                "Note /5"  : note,
                "Lien"     : lien if lien else "N/A",
                "Page"     : page,
            })

            print(f"  {titre[:50]} | {f'{prix} euro' if prix else 'N/A'}")

        except Exception:
            continue

    return produits


def exporter(produits):
    df = pd.DataFrame(produits)
    df = df.drop_duplicates(subset=["Titre"]).reset_index(drop=True)

    prix_valides = df["Prix (€)"].dropna()

    print(f"\n{len(df)} produits collectes")
    print(f"Avec prix : {len(prix_valides)}")
    print(f"Sans prix : {df['Prix (€)'].isna().sum()}")
    print(f"Avec lien : {(df['Lien'] != 'N/A').sum()}")

    if not prix_valides.empty:
        print(f"Prix moyen : {prix_valides.mean():.2f} euro")
        print(f"Prix min   : {prix_valides.min():.2f} euro")
        print(f"Prix max   : {prix_valides.max():.2f} euro")

    df.to_excel(FICHIER, index=False)
    print(f"Fichier '{FICHIER}' cree")


def main():
    print("Amazon.fr Laptop Scraper")
    print("-" * 40)

    driver = creer_driver()
    produits = []

    try:
        for page in range(1, NB_PAGES + 1):
            resultats = extraire_produits(driver, page)
            produits.extend(resultats)
            print(f"Total cumule : {len(produits)} produits")
            time.sleep(random.uniform(2, 4))

    except Exception as e:
        print(f"Erreur : {e}")

    finally:
        driver.quit()
        print("Chrome ferme")

    if produits:
        exporter(produits)
    else:
        print("Aucun produit collecte")
        print("Conseil : ouvre amazon.fr dans Chrome d'abord puis relance")


if __name__ == "__main__":
    main()