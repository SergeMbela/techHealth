-- Table Analyse
CREATE TABLE Analyse (
    id INT IDENTITY(1,1) PRIMARY KEY,
    PatientID INT NOT NULL,
    date_analyse DATE NOT NULL,
    type_analyse NVARCHAR(100),
    commentaires NVARCHAR(MAX),
    FOREIGN KEY (PatientID) REFERENCES Patients(PatientID)
);

-- Table ParametreBiologique
CREATE TABLE ParametreBiologique (
    id INT IDENTITY(1,1) PRIMARY KEY,
    nom NVARCHAR(100) NOT NULL,
    unite NVARCHAR(20),
    valeur_reference NVARCHAR(50)
);

-- Table ResultatAnalyse
CREATE TABLE ResultatAnalyse (
    id INT IDENTITY(1,1) PRIMARY KEY,
    analyse_id INT NOT NULL,
    parametre_id INT NOT NULL,
    valeur FLOAT,
    interpretation NVARCHAR(100),
    FOREIGN KEY (analyse_id) REFERENCES Analyse(id),
    FOREIGN KEY (parametre_id) REFERENCES ParametreBiologique(id)
);


INSERT INTO ParametreBiologique (nom, unite, valeur_reference) VALUES
(N'Globules blancs', N'x10^3/mm³', N'4.0 – 10.0'),
(N'Neutrophiles', N'%', N'40 – 75'),
(N'Lymphocytes', N'%', N'20 – 45'),
(N'CRP', N'mg/L', N'< 5'),
(N'VS', N'mm/h', N'< 20'),
(N'Plaquettes', N'/mm³', N'150000 – 400000'),
(N'Urée', N'mmol/L', N'2.5 – 7.5'),
(N'Créatinine', N'µmol/L', N'60 – 110'),
(N'ALAT', N'UI/L', N'< 45'),
(N'ASAT', N'UI/L', N'< 45');
