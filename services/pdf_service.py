from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors

def generer_pdf_rapport(stats, fichier_pdf="rapport.pdf", titre="Rapport Statistique", sous_titre="Détails des résultats"):
    """
    Génère un PDF avec des statistiques et des titres.

    :param stats: Dictionnaire de statistiques à inclure dans le PDF.
    :param fichier_pdf: Nom du fichier PDF généré.
    :param titre: Titre principal du PDF.
    :param sous_titre: Sous-titre ou description du PDF.
    """
    # Créer un objet canvas pour générer le PDF
    c = canvas.Canvas(fichier_pdf, pagesize=letter)
    width, height = letter

    # Titre du document
    c.setFont("Helvetica-Bold", 18)
    c.drawString(100, height - 100, titre)

    # Sous-titre
    c.setFont("Helvetica", 12)
    c.drawString(100, height - 130, sous_titre)

    # Espacement pour les statistiques
    y_position = height - 160
    c.setFont("Helvetica", 10)

    # Ajouter les statistiques sous forme de texte
    for key, value in stats.items():
        c.setFont("Helvetica-Bold", 10)
        c.drawString(100, y_position, f"{key}:")
        
        c.setFont("Helvetica", 10)
        c.drawString(200, y_position, str(value))

        y_position -= 20  # Déplacer la position verticale pour le prochain item

        if y_position < 100:  # Si la position est trop basse, on ajoute une nouvelle page
            c.showPage()
            y_position = height - 100

    # Sauvegarder le PDF
    c.save()
    print(f"✅ PDF généré : {fichier_pdf}")

