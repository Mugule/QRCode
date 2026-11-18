import io

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

taille_case = st.sidebar.slider("Taille des cases (pixels)", 2, 20, 10)
bordure = st.sidebar.slider("Marge autour du QR (cases)", 0, 10, 4)

st.sidebar.subheader("Logo")
logo_fichier = st.sidebar.file_uploader("Logo au centre (optionnel)", type=["png", "jpg", "jpeg"])
taille_logo = st.sidebar.slider("Taille du logo (% du QR)", 10, 35, 25)
fond_logo = st.sidebar.checkbox("Fond derrière le logo", value=True)

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
            cote = int(img.size[0] * taille_logo / 100)
            logo.thumbnail((cote, cote))

            # Position au centre
            x = (img.size[0] - logo.size[0]) // 2
            y = (img.size[1] - logo.size[1]) // 2

            if fond_logo:
                marge = taille_case
                img.paste(
                    Image.new("RGB", (logo.size[0] + 2 * marge, logo.size[1] + 2 * marge), couleur_fond),
                    (x - marge, y - marge),
                )

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
