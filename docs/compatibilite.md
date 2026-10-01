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
| Exchange sur site (EWS) | Thunderbird | ⚠️ | Selon la version de Thunderbird et la configuration du serveur |
| Microsoft Teams | Web app (Chromium) | 🟡 | Version web de Teams : quelques fonctions du client Windows manquent |
| Zoom | Web app (Chromium) | 🟡 | Client web Zoom : fonctions avancées (arrière-plans virtuels…) limitées |
| Slack | Web app (Chromium) | 🟡 | |
| Partage d'écran (Wayland) | PipeWire + portail KDE | 🟡 | Une fenêtre KDE demande quel écran ou quelle fenêtre partager |
| Stockage Nextcloud | Client Nextcloud | 🟡 | |
| OneDrive | Client libre `onedrive` (assistant « OneDrive » du menu) | 🟡 | Synchronisation complète dans ~/OneDrive : pas de « fichiers à la demande » |
| SharePoint, bibliothèques d'équipe | Navigateur, ou client `onedrive` configuré à la main | ⚠️ | L'assistant ne connecte que le OneDrive personnel du compte |
| Bureau à distance vers Windows (RDP) | Remmina | 🟡 | Équivalent de « Connexion Bureau à distance » (mstsc) |
| Prise en main à distance du PC par le support | KRdp (Plasma) | 🟡 | À activer dans Configuration du système → Bureau à distance ; se pilote depuis mstsc |

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
| VPN intégrés à Windows (L2TP/IPsec, IKEv2, SSTP) | 🟡 | Mêmes réglages ; à vérifier avec chaque type de serveur |

## Système et entreprise

| Usage | Logiciel | État | Remarques |
| --- | --- | --- | --- |
| Domaine Active Directory (session avec le compte Windows) | realmd, SSSD, adcli | 🟡 | `sudo realm join` ; dossier personnel créé à la première connexion (voir [migration-windows.md](migration-windows.md)) |
| Sauvegarde des fichiers | Déjà Dup | 🟡 | Disque externe ou service cloud |
| Lecture vidéo et audio (MP4, AVI, WMV, MKV…) | Haruna | 🟡 | Codecs inclus dans l'image |
| Correcteur orthographique français | Dictionnaires Hunspell (`langpacks-fr`) | 🟡 | OnlyOffice, Firefox et Thunderbird ont aussi le leur |

## Logiciels Windows

Les programmes Windows (`.exe`, `.msi`) ne s'installent pas. Pour chaque logiciel métier, chercher dans
cet ordre : une version web, une version Linux (Flathub), un équivalent libre. Wine et les machines
virtuelles Windows ne font pas partie du MVP.
