# Compatibilité

État à la v0.1 (alpha). **Rien n'a encore été testé sur du vrai matériel** : la colonne « État » indique
ce qui est attendu d'après les composants inclus, pas un résultat de test. Mettez-la à jour à chaque
vérification, avec la date et le matériel utilisé.

Légende : ✅ vérifié · 🟡 attendu, à vérifier · ⚠️ partiel ou avec contournement · ❌ non pris en charge

## Documents

| Usage | Logiciel | État | Remarques |
| --- | --- | --- | --- |
| Word (.docx, .doc) | OnlyOffice | 🟡 | Protocole de test : [validation-mvp.md](validation-mvp.md) |
| Excel (.xlsx, .xls, .csv) | OnlyOffice | 🟡 | Tableaux croisés et graphiques à vérifier |
| PowerPoint (.pptx) | OnlyOffice | 🟡 | Animations et transitions à vérifier |
| OpenDocument (.odt, .ods, .odp) | OnlyOffice | 🟡 | |
| Macros VBA | | ❌ | OnlyOffice utilise des macros JavaScript |
| Access, Visio, Publisher | | ❌ | Pas d'équivalent inclus |
| PDF : lecture, annotation, formulaires | Okular | 🟡 | |
| PDF : création | Imprimante PDF, export OnlyOffice | 🟡 | Impression vers PDF couverte par le test en VM |
| Polices Calibri, Cambria, Arial, Times New Roman, Courier New | Carlito, Caladea, Liberation | 🟡 | Substitution contrôlée à chaque build ; même métrique, dessin différent |
| Autres polices Microsoft (Segoe UI, Verdana, Tahoma…) | | ⚠️ | Remplacées par une police par défaut : mise en page possiblement décalée |

## Communication

| Usage | Logiciel | État | Remarques |
| --- | --- | --- | --- |
| Courriel IMAP/SMTP, Gmail, Microsoft 365 | Thunderbird | 🟡 | Microsoft 365 via OAuth (connexion Microsoft dans Thunderbird) |
| Microsoft 365 en ligne (Outlook, Word, Excel, PowerPoint, OneDrive) | Web apps du menu (Chromium) | 🟡 | Mêmes fonctions que dans le navigateur ; l'édition à plusieurs se fait ici |
| Exchange sur site (EWS) | Thunderbird | ⚠️ | Selon la version de Thunderbird et la configuration du serveur |
| Microsoft Teams | Web app (Chromium) | 🟡 | Version web de Teams : quelques fonctions du client Windows manquent |
| Zoom | Web app (Chromium) | 🟡 | Client web Zoom : fonctions avancées (arrière-plans virtuels…) limitées |
| Slack | Web app (Chromium) | 🟡 | |
| Partage d'écran (Wayland) | PipeWire + portail KDE | 🟡 | Une fenêtre KDE demande quel écran ou quelle fenêtre partager |
| Stockage Nextcloud | Client Nextcloud | 🟡 | |
| OneDrive, SharePoint | Navigateur | ⚠️ | Pas de client de synchronisation officiel |

## Matériel

| Matériel | État | Remarques |
| --- | --- | --- |
| Imprimantes réseau récentes (IPP Everywhere, AirPrint) | 🟡 | Détectées sans pilote : la majorité des modèles depuis 2015 |
| Imprimantes USB récentes (IPP-over-USB) | 🟡 | Via ipp-usb |
| Imprimantes HP | 🟡 | hplip |
| Imprimantes Brother, Samsung, Epson anciennes | 🟡 | brlaser, splix, Gutenprint ; certains modèles demandent le pilote du fabricant |
| Scanners réseau (eSCL, WSD) | 🟡 | sane-airscan |
| Scanners USB | 🟡 | SANE ; certains modèles Epson et Canon demandent un pilote propriétaire |
| Carte graphique Intel, AMD | 🟡 | Pilotes libres (Mesa) |
| Carte graphique NVIDIA | ⚠️ | Pilote libre uniquement ; une variante sur `kinoite-nvidia` serait nécessaire pour le pilote propriétaire |
| Secure Boot | 🟡 | Démarrage couvert par le test en VM (OVMF avec les clés Microsoft) ; modules noyau additionnels d'Universal Blue à enrôler (MOK) |
| Wi-Fi, Bluetooth, webcams | 🟡 | Selon le support du noyau Linux |
| VPN (OpenVPN, OpenConnect/AnyConnect, WireGuard) | 🟡 | Configurables dans les réglages réseau de KDE |

## Logiciels Windows

Les programmes Windows (`.exe`, `.msi`) ne s'installent pas. Pour chaque logiciel métier, chercher dans
cet ordre : une version web, une version Linux (Flathub), un équivalent libre. Wine et les machines
virtuelles Windows ne font pas partie du MVP.
