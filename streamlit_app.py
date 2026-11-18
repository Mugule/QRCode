import io
import math

import streamlit as st
import qrcode
from PIL import Image

st.title("Générateur de QR code")

texte = st.text_input("Texte ou lien à encoder")

# --- Paramètres dans la barre latérale ---
st.sidebar.header("Paramètres")

col1, col2 = st.sidebar.columns(2)
couleur_qr = col1.color_picker("Couleur du QR", "#000000")
couleur_fond = col2.color_picker("Couleur du fond", "#FFFFFF")

niveaux = {
    "L (7 %)": qrcode.constants.ERROR_CORRECT_L,
    "M (15 %)": qrcode.constants.ERROR_CORRECT_M,
    "Q (25 %)": qrcode.constants.ERROR_CORRECT_Q,
    "H (30 %)": qrcode.constants.ERROR_CORRECT_H,
}
niveau = st.sidebar.selectbox(
    "Correction d'erreur",
    list(niveaux.keys()),
    index=1,
    help="Plus le niveau est élevé, plus le QR reste lisible s'il est abîmé ou masqué (par un logo par exemple).",
)

taille_case = st.sidebar.number_input("Taille des cases (pixels)", min_value=1, value=10, step=1)
bordure = st.sidebar.number_input("Marge autour du QR (cases)", min_value=0, value=4, step=1)

st.sidebar.subheader("Logo")
logo_fichier = st.sidebar.file_uploader("Logo au centre (optionnel)", type=["png", "jpg", "jpeg"])
taille_logo = st.sidebar.number_input("Taille du logo (pixels)", min_value=1, value=80, step=1)
fond_logo = st.sidebar.checkbox("Fond derrière le logo", value=True)
marge_logo = st.sidebar.number_input(
    "Marge minimale autour du logo (pixels)",
    min_value=0,
    value=10,
    step=1,
    disabled=not fond_logo,
    help="Le fond est ensuite agrandi pour tomber pile sur les cases du QR code.",
)


def cases_impaires(pixels, taille_case):
    """Nombre de cases nécessaires pour couvrir `pixels`, arrondi au nombre impair supérieur.

    Un QR code a toujours un nombre impair de cases de côté (21, 25, 29...).
    Un fond avec un nombre impair de cases peut donc être centré exactement sur la grille.
    """
    n = math.ceil(pixels / taille_case)
    return n if n % 2 == 1 else n + 1


# --- Génération ---
if st.button("Envoyer"):
    if not texte:
        st.warning("Veuillez saisir un texte.")
    else:
        correction = niveaux[niveau]
        if logo_fichier:
            # Le logo masque une partie du QR : on force la correction maximale
            correction = qrcode.constants.ERROR_CORRECT_H

        qr = qrcode.QRCode(
            error_correction=correction,
            box_size=taille_case,
            border=bordure,
        )
        qr.add_data(texte)
        qr.make(fit=True)

        img = qr.make_image(fill_color=couleur_qr, back_color=couleur_fond).convert("RGB")

        if logo_fichier:
            logo = Image.open(logo_fichier).convert("RGBA")

            # Redimensionnement du logo en gardant ses proportions
            # (le côté le plus long du logo fera taille_logo pixels)
            ratio = taille_logo / max(logo.size)
            logo = logo.resize(
                (max(1, round(logo.size[0] * ratio)), max(1, round(logo.size[1] * ratio))),
                Image.LANCZOS,
            )

            nb_cases = qr.modules_count            # cases de côté du QR (sans la marge)
            largeur_qr = nb_cases * taille_case    # largeur du QR en pixels (sans la marge)

            if fond_logo:
                # Taille du fond en cases (impaire), puis en pixels
                cases_l = cases_impaires(logo.size[0] + 2 * marge_logo, taille_case)
                cases_h = cases_impaires(logo.size[1] + 2 * marge_logo, taille_case)

                # Position du fond alignée sur la grille des cases
                fx = (bordure + (nb_cases - cases_l) // 2) * taille_case
                fy = (bordure + (nb_cases - cases_h) // 2) * taille_case

                img.paste(
                    Image.new("RGB", (cases_l * taille_case, cases_h * taille_case), couleur_fond),
                    (fx, fy),
                )
                zone_masquee = max(cases_l, cases_h) * taille_case
            else:
                zone_masquee = max(logo.size)

            if zone_masquee > largeur_qr * 0.3:
                st.warning(
                    f"Le logo et son fond ({zone_masquee} px) dépassent 30 % de la largeur du QR code "
                    f"({largeur_qr} px) : il risque de ne plus se scanner."
                )

            # Logo au centre exact de l'image
            x = (img.size[0] - logo.size[0]) // 2
            y = (img.size[1] - logo.size[1]) // 2
            img.paste(logo, (x, y), mask=logo)

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")

        st.image(buffer.getvalue(), caption="Votre QR code")
        st.download_button(
            "Télécharger le QR code",
            data=buffer.getvalue(),
            file_name="qrcode.png",
            mime="image/png",
        )

        if logo_fichier:
            st.info("Correction d'erreur passée à H automatiquement à cause du logo. Pensez à tester le scan avec votre téléphone.")
