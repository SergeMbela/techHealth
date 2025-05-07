import pandas as pd

def generer_excel_rapport(stats, fichier_excel="rapport_grippe_2024.xlsx", titre="Rapport Statistique", sous_titre="Détails des résultats"):
    """
    Génère un fichier Excel avec des statistiques et un graphique.

    :param stats: Dictionnaire de statistiques à inclure dans le fichier Excel.
    :param fichier_excel: Nom du fichier Excel généré.
    :param titre: Titre principal du rapport.
    :param sous_titre: Sous-titre ou description du rapport.
    """
    # Créer un DataFrame à partir des statistiques
    stats_df = pd.DataFrame(list(stats.items()), columns=["Statistique", "Valeur"])

    # Créer un writer Excel avec XlsxWriter comme moteur
    with pd.ExcelWriter(fichier_excel, engine="xlsxwriter") as writer:
        # Ajouter les statistiques dans la première feuille
        stats_df.to_excel(writer, sheet_name="Statistiques", index=False)

        # Récupérer l'objet workbook et worksheet
        workbook  = writer.book
        worksheet = writer.sheets["Statistiques"]

        # Ajouter un titre et sous-titre dans la feuille
        worksheet.write("A1", titre, workbook.add_format({"bold": True, "font_size": 14}))
        worksheet.write("A2", sous_titre, workbook.add_format({"italic": True, "font_size": 12}))

        # Ajouter un graphique (bar chart) dans l'Excel
        chart = workbook.add_chart({"type": "column"})

        # Ajouter des séries de données au graphique
        chart.add_series({
            "name": "Valeurs",
            "categories": "=Statistiques!$A$3:$A$" + str(len(stats_df) + 2),  # Plage des statistiques
            "values": "=Statistiques!$B$3:$B$" + str(len(stats_df) + 2),      # Plage des valeurs
        })

        # Personnaliser le graphique
        chart.set_title({"name": "Statistiques - Taux de positivité"})
        chart.set_x_axis({"name": "Statistique"})
        chart.set_y_axis({"name": "Valeur"})

        # Insérer le graphique dans la feuille Excel
        worksheet.insert_chart("D3", chart)

    print(f"✅ Fichier Excel généré : {fichier_excel}")
