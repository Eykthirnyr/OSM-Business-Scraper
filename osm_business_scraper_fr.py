import sys
import subprocess

# Vérifier les modules requis et installer si manquant
modules_requis = ['requests', 'tkinter', 'openpyxl', 'tkintermapview']
for module in modules_requis:
    try:
        __import__(module)
    except ImportError:
        print(f"Le module '{module}' n'est pas installé. Installation en cours...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", module])

import requests
import tkinter as tk
from tkinter import messagebox, ttk
from openpyxl import Workbook
from openpyxl.styles import Font
from collections import defaultdict
import tkintermapview
import webbrowser

def rechercher_entreprises():
    try:
        latitude = float(entree_latitude.get())
        longitude = float(entree_longitude.get())
        rayon = float(entree_rayon.get())  # Rayon en kilomètres
    except ValueError:
        messagebox.showerror("Erreur d'entrée", "Veuillez entrer des valeurs numériques valides.")
        return

    # Collecter les catégories sélectionnées
    categories_selectionnees = []
    for (tag, value), var in variables_categories.items():
        if var.get():
            categories_selectionnees.append((tag, value))

    if not categories_selectionnees:
        messagebox.showerror("Erreur de sélection", "Veuillez sélectionner au moins une catégorie.")
        return

    # Construire la requête Overpass API basée sur les catégories sélectionnées
    url_overpass = "http://overpass-api.de/api/interpreter"

    # Regrouper les catégories sélectionnées par tag
    valeurs_tags = defaultdict(list)
    for tag, values in categories_selectionnees:
        valeurs_tags[tag].append(values)

    # Construire les parties de la requête
    parties_requete = []
    for tag, values in valeurs_tags.items():
        if None in values:
            # Pour les tags sans valeurs spécifiques (par exemple, 'shop', 'office')
            parties_requete.append(f'  node(around:{rayon * 1000},{latitude},{longitude})["name"]["{tag}"];')
            parties_requete.append(f'  way(around:{rayon * 1000},{latitude},{longitude})["name"]["{tag}"];')
        else:
            # Pour les tags avec des valeurs spécifiques
            regex = '|'.join(values)
            parties_requete.append(f'  node(around:{rayon * 1000},{latitude},{longitude})["name"]["{tag}"~"{regex}"];')
            parties_requete.append(f'  way(around:{rayon * 1000},{latitude},{longitude})["name"]["{tag}"~"{regex}"];')

    requete_overpass = f"""
    [out:json];
    (
    {'\n'.join(parties_requete)}
    );
    out center;
    """

    response = requests.get(url_overpass, params={'data': requete_overpass})
    data = response.json()

    global tous_les_resultats  # Rendre tous_les_resultats global pour y accéder dans d'autres fonctions
    tous_les_resultats = []
    compte_traite = 0

    for element in data.get('elements', []):
        tags = element.get('tags', {})
        nom = tags.get('name')
        adresse = construire_adresse(tags)
        telephone = tags.get('phone', None)  # Obtenir le numéro de téléphone, None si absent

        # Vérifier si la case "Exclure les entrées sans numéro de téléphone" est cochée
        exclure_sans_telephone = var_exclure_sans_telephone.get()

        # Déterminer si l'entrée doit être incluse
        inclure_entree = True
        if exclure_sans_telephone and not telephone:
            inclure_entree = False

        if nom and inclure_entree:
            tous_les_resultats.append({
                'Nom': nom,
                'Adresse': adresse,
                'Téléphone': telephone if telephone else 'N/A'
            })
            compte_traite += 1
            label_compteur.config(text=f"Nombre d'entreprises : {compte_traite}")
            root.update_idletasks()

    if tous_les_resultats:
        messagebox.showinfo("Données récupérées", f"Données récupérées avec succès. Total des entreprises : {compte_traite}")
    else:
        messagebox.showinfo("Aucune donnée", "Aucune entreprise trouvée avec les critères spécifiés.")

def supprimer_doublons():
    global tous_les_resultats
    if not tous_les_resultats:
        messagebox.showinfo("Aucune donnée", "Aucune donnée à traiter. Veuillez d'abord rechercher des entreprises.")
        return

    resultats_uniques = []
    noms_vus = set()

    for entree in tous_les_resultats:
        nom = entree['Nom']
        if nom not in noms_vus:
            noms_vus.add(nom)
            resultats_uniques.append(entree)

    doublons_supprimes = len(tous_les_resultats) - len(resultats_uniques)
    tous_les_resultats = resultats_uniques  # Mettre à jour tous_les_resultats avec les entrées uniques

    label_compteur.config(text=f"Nombre d'entreprises : {len(tous_les_resultats)}")
    root.update_idletasks()
    messagebox.showinfo("Doublons supprimés", f"{doublons_supprimes} entrées en double supprimées.")

def enregistrer_donnees():
    if not tous_les_resultats:
        messagebox.showinfo("Aucune donnée", "Aucune donnée à enregistrer. Veuillez d'abord rechercher des entreprises.")
        return

    sauvegarder_dans_excel(tous_les_resultats)
    messagebox.showinfo("Succès", f"Données enregistrées dans 'entreprises.xlsx'. Total des entreprises : {len(tous_les_resultats)}")

def construire_adresse(tags):
    # Construire l'adresse à partir des tags disponibles
    parties_adresse = []
    for key in ['addr:housenumber', 'addr:street', 'addr:city', 'addr:postcode', 'addr:country']:
        if tags.get(key):
            parties_adresse.append(tags[key])
    return ', '.join(parties_adresse) if parties_adresse else 'N/A'

def sauvegarder_dans_excel(data):
    wb = Workbook()
    ws = wb.active
    ws.title = "Entreprises"

    # Définir les en-têtes
    entetes = ['Nom', 'Adresse', 'Téléphone']
    ws.append(entetes)

    # Appliquer le gras aux en-têtes
    for cell in ws[1]:
        cell.font = Font(bold=True)

    # Ajouter les données à la feuille
    for entree in data:
        ws.append([entree['Nom'], entree['Adresse'], entree['Téléphone']])

    # Ajuster la largeur des colonnes
    for column_cells in ws.columns:
        length = max(len(str(cell.value)) for cell in column_cells if cell.value)
        ws.column_dimensions[column_cells[0].column_letter].width = length + 2

    # Enregistrer le classeur
    wb.save('entreprises.xlsx')

# Nouvelles fonctions pour "Tout cocher" et "Tout décocher"
def tout_cocher():
    for var in variables_categories.values():
        var.set(True)

def tout_decocher():
    for var in variables_categories.values():
        var.set(False)

# Fonction pour ouvrir la carte et sélectionner un lieu
def ouvrir_carte():
    fenetre_carte = tk.Toplevel(root)
    fenetre_carte.title("Sélectionner un lieu")
    fenetre_carte.geometry("600x400")

    # Créer le widget de carte
    widget_carte = tkintermapview.TkinterMapView(fenetre_carte, width=600, height=400, corner_radius=0)
    widget_carte.pack(fill="both", expand=True)

    # Centrer la carte sur la position actuelle si disponible
    try:
        lat_actuelle = float(entree_latitude.get())
        lon_actuelle = float(entree_longitude.get())
        widget_carte.set_position(lat_actuelle, lon_actuelle)
        widget_carte.set_zoom(15)
    except ValueError:
        # Position par défaut (0,0) si entrées invalides
        widget_carte.set_position(0, 0)
        widget_carte.set_zoom(2)

    # Fonction pour gérer les clics sur la carte
    def on_left_click_event(coordinates_tuple):
        lat, lon = coordinates_tuple
        # Mettre à jour les entrées
        entree_latitude.delete(0, tk.END)
        entree_latitude.insert(0, str(lat))
        entree_longitude.delete(0, tk.END)
        entree_longitude.insert(0, str(lon))
        # Placer un marqueur
        widget_carte.set_marker(lat, lon, text="Lieu sélectionné")
        # Fermer la fenêtre de la carte
        fenetre_carte.destroy()

    widget_carte.add_left_click_map_command(on_left_click_event)

# Fonction pour ouvrir le site web
def ouvrir_site_web(event):
    webbrowser.open_new("https://clement.business/")

# Fonction pour ouvrir le dépôt GitHub
def ouvrir_github():
    webbrowser.open_new("https://github.com/Eykthirnyr/OSM-Business-Scraper")

# Initialiser la variable globale
tous_les_resultats = []

# Configuration de l'interface graphique
root = tk.Tk()
root.title("Scrapeur d'entreprises OpenStreetMap")
root.geometry("850x900")
root.resizable(False, False)

# Configuration du style
style = ttk.Style(root)
style.configure('TLabel', font=('Arial', 10))
style.configure('TButton', font=('Arial', 10))
style.configure('TCheckbutton', font=('Arial', 10))

# Titre et description
label_titre = ttk.Label(root, text="Scrapeur d'entreprises OpenStreetMap", font=("Arial", 16, "bold"))
label_titre.pack(pady=(10, 5))

label_description = ttk.Label(root, text="Recherchez des entreprises depuis OpenStreetMap en fonction de la localisation et des catégories.")
label_description.pack(pady=(0, 10))

# Cadre pour les entrées de latitude, longitude et rayon
cadre_entrees = ttk.Frame(root)
cadre_entrees.pack(pady=5)

# Entrées pour la latitude et la longitude
ttk.Label(cadre_entrees, text="Latitude :").grid(row=0, column=0, sticky='e', padx=5, pady=5)
entree_latitude = ttk.Entry(cadre_entrees)
entree_latitude.grid(row=0, column=1, padx=5, pady=5)

ttk.Label(cadre_entrees, text="Longitude :").grid(row=1, column=0, sticky='e', padx=5, pady=5)
entree_longitude = ttk.Entry(cadre_entrees)
entree_longitude.grid(row=1, column=1, padx=5, pady=5)

# Entrée pour le rayon
ttk.Label(cadre_entrees, text="Rayon (km) :").grid(row=2, column=0, sticky='e', padx=5, pady=5)
entree_rayon = ttk.Entry(cadre_entrees)
entree_rayon.grid(row=2, column=1, padx=5, pady=5)

# Bouton pour ouvrir la carte
bouton_selectionner_lieu = ttk.Button(cadre_entrees, text="Sélectionner un lieu sur la carte", command=ouvrir_carte)
bouton_selectionner_lieu.grid(row=0, column=2, rowspan=3, padx=5, pady=5)

# Catégories pour la sélection
categories = [
    ('Magasin', 'shop', None),
    ('Bureau', 'office', None),
    ('Restaurant', 'amenity', 'restaurant'),
    ('Café', 'amenity', 'cafe'),
    ('Bar', 'amenity', 'bar'),
    ('Pub', 'amenity', 'pub'),
    ('Restauration rapide', 'amenity', 'fast_food'),
    ('Banque', 'amenity', 'bank'),
    ('Pharmacie', 'amenity', 'pharmacy'),
    ('Hôpital', 'amenity', 'hospital'),
    ('Clinique', 'amenity', 'clinic'),
    ('Dentiste', 'amenity', 'dentist'),
    ('Médecins', 'amenity', 'doctors'),
    ('Théâtre', 'amenity', 'theatre'),
    ('Cinéma', 'amenity', 'cinema'),
    ('Boîte de nuit', 'amenity', 'nightclub'),
    ("Jardin d'enfants", 'amenity', 'kindergarten'),
    ('Bibliothèque', 'amenity', 'library'),
    ('Collège', 'amenity', 'college'),
    ('Université', 'amenity', 'university'),
    # Tags additionnels
    ('Parking', 'amenity', 'parking'),
    ('Station-service', 'amenity', 'fuel'),
    ('Hôtel', 'tourism', 'hotel'),
    ('Motel', 'tourism', 'motel'),
    ("Maison d'hôtes", 'tourism', 'guest_house'),
    ('Supermarché', 'shop', 'supermarket'),
    ('Supérette', 'shop', 'convenience'),
    ('Boulangerie', 'shop', 'bakery'),
    ('Boucherie', 'shop', 'butcher'),
    ('Magasin de vêtements', 'shop', 'clothes'),
    ("Magasin d'électronique", 'shop', 'electronics'),
    ('Magasin de meubles', 'shop', 'furniture'),
    ('Bijouterie', 'shop', 'jewelry'),
    ('Magasin de sport', 'shop', 'sports'),
    ('Coiffeur', 'shop', 'hairdresser'),
    ('Salon de beauté', 'shop', 'beauty'),
    ('Musée', 'tourism', 'museum'),
    ('Parc', 'leisure', 'park'),
    ('Distributeur automatique', 'amenity', 'atm'),
    ('Bureau de poste', 'amenity', 'post_office'),
    ('Poste de police', 'amenity', 'police'),
    ('Caserne de pompiers', 'amenity', 'fire_station'),
    ('Ambassade', 'amenity', 'embassy'),
    ('Tribunal', 'amenity', 'courthouse'),
    ('Lieu de culte', 'amenity', 'place_of_worship'),
    ('Clinique vétérinaire', 'amenity', 'veterinary'),
    ('Piscine', 'leisure', 'swimming_pool'),
    ('Salle de sport', 'leisure', 'fitness_centre'),
    ('Aire de jeux', 'leisure', 'playground'),
    ('Gare routière', 'amenity', 'bus_station'),
    ('Gare ferroviaire', 'railway', 'station'),
    ('Aéroport', 'aeroway', 'aerodrome'),
    ('Station de taxis', 'amenity', 'taxi'),
    ('Location de voitures', 'amenity', 'car_rental'),
    ('Lavage de voitures', 'amenity', 'car_wash'),
    ('Station de recharge', 'amenity', 'charging_station'),
    ('École', 'amenity', 'school'),
    ('Casino', 'amenity', 'casino'),
    ("Œuvre d'art", 'tourism', 'artwork'),
    ('Information', 'tourism', 'information'),
    ('Point de vue', 'tourism', 'viewpoint'),
    ('Zoo', 'tourism', 'zoo'),
    ("Parc d'attractions", 'tourism', 'theme_park'),
    ('Parc aquatique', 'leisure', 'water_park'),
]

# Cadre pour les cases à cocher
cadre_cases = ttk.LabelFrame(root, text="Catégories à inclure")
cadre_cases.pack(pady=10, padx=10, fill="both", expand=True)

variables_categories = {}
colonnes = 5
for idx, (nom_affichage, tag, value) in enumerate(categories):
    var = tk.BooleanVar(value=True)  # sélectionné par défaut
    variables_categories[(tag, value)] = var
    row = idx // colonnes
    col = idx % colonnes
    case = ttk.Checkbutton(cadre_cases, text=nom_affichage, variable=var)
    case.grid(row=row, column=col, sticky='w', padx=5, pady=2)

# Cadre pour les boutons "Tout cocher" et "Tout décocher"
cadre_boutons = ttk.Frame(root)
cadre_boutons.pack(pady=5)

bouton_tout_cocher = ttk.Button(cadre_boutons, text="Tout cocher", command=tout_cocher)
bouton_tout_cocher.pack(side='left', padx=20)

bouton_tout_decocher = ttk.Button(cadre_boutons, text="Tout décocher", command=tout_decocher)
bouton_tout_decocher.pack(side='left', padx=20)

# Case à cocher pour exclure les entrées sans numéro de téléphone
var_exclure_sans_telephone = tk.BooleanVar()
case_exclure_sans_telephone = ttk.Checkbutton(root, text="Exclure les entrées sans numéro de téléphone", variable=var_exclure_sans_telephone)
case_exclure_sans_telephone.pack(pady=5)

# Boutons d'action
bouton_recuperer = ttk.Button(root, text="Rechercher les entreprises", command=rechercher_entreprises)
bouton_recuperer.pack(padx=5, pady=10)

bouton_supprimer_doublons = ttk.Button(root, text="Supprimer les noms en double", command=supprimer_doublons)
bouton_supprimer_doublons.pack(padx=5, pady=10)

label_compteur = ttk.Label(root, text="Nombre d'entreprises : 0")
label_compteur.pack()

bouton_sauvegarder = ttk.Button(root, text="Enregistrer les entreprises", command=enregistrer_donnees)
bouton_sauvegarder.pack(padx=5, pady=10)

# Bouton GitHub
bouton_github = ttk.Button(root, text="Dépôt GitHub", command=ouvrir_github)
bouton_github.pack(pady=5)

# Label "Réalisé par" avec hyperlien
label_realise_par = ttk.Label(root, text="Réalisé par Clément GHANEME", foreground="blue", cursor="hand2")
label_realise_par.pack(pady=(10, 5))
label_realise_par.bind("<Button-1>", ouvrir_site_web)

root.mainloop()
