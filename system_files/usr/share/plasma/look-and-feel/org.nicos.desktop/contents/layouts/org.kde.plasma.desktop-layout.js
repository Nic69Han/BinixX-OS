// Disposition par défaut du bureau NicOS, appliquée à la première ouverture de session.
// Une barre des tâches fixée en haut de l'écran, sur toute la largeur, avec de gauche
// à droite le menu de démarrage, les applications épinglées et ouvertes, la zone de
// notification, l'horloge et le bouton « Afficher le bureau ».
//
// Adapté du modèle upstream org.kde.plasma.desktop.defaultPanel (plasma-desktop, GPL-2.0-or-later).
// API de script : https://develop.kde.org/docs/plasma/scripting/

var panel = new Panel
panel.location = "top"
// Barre fixe, pas « flottante » comme le veut le réglage par défaut de Plasma 6
panel.floating = false

// Même hauteur que le panneau Plasma par défaut (≈ 46 px à l'échelle 100 %),
// arrondie à un nombre pair car le réglage de taille n'affiche que des valeurs paires
panel.height = 2 * Math.ceil(gridUnit * 2.5 / 2)

// Menu de démarrage (Kickoff), ouvert aussi par la touche Windows, avec le logo NicOS
var kickoff = panel.addWidget("org.kde.plasma.kickoff")
kickoff.currentConfigGroup = ["General"]
kickoff.writeConfig("icon", "nicos")

// Barre des tâches à icônes, avec les applications épinglées.
// Pas de sélecteur de bureaux virtuels : il déroute les utilisateurs venant de Windows.
var tasks = panel.addWidget("org.kde.plasma.icontasks")
tasks.currentConfigGroup = ["General"]
tasks.writeConfig("launchers", [
    "preferred://browser",
    "applications:org.kde.dolphin.desktop",
    "applications:org.mozilla.thunderbird_esr.desktop",
    "applications:org.onlyoffice.desktopeditors.desktop"
])

panel.addWidget("org.kde.plasma.marginsseparator")

// Méthode de saisie pour les langues qui en ont besoin (liste reprise du modèle upstream)
var langIds = ["as", "bn", "bo", "brx", "doi", "gu", "hi", "ja", "kn", "ko", "kok", "ks",
               "lep", "mai", "ml", "mni", "mr", "ne", "or", "pa", "sa", "sat", "sd", "si",
               "ta", "te", "th", "ur", "vi", "zh_CN", "zh_TW"]
if (langIds.indexOf(languageId) != -1) {
    panel.addWidget("org.kde.plasma.kimpanel")
}

panel.addWidget("org.kde.plasma.systemtray")
panel.addWidget("org.kde.plasma.digitalclock")
panel.addWidget("org.kde.plasma.showdesktop")

// Fond d'écran NicOS (version sombre choisie automatiquement avec un thème sombre)
var desktopsArray = desktopsForActivity(currentActivity())
for (var j = 0; j < desktopsArray.length; j++) {
    desktopsArray[j].wallpaperPlugin = "org.kde.image"
    desktopsArray[j].currentConfigGroup = ["Wallpaper", "org.kde.image", "General"]
    desktopsArray[j].writeConfig("Image", "file:///usr/share/wallpapers/NicOS/")
}
