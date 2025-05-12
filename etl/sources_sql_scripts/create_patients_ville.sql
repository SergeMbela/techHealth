CREATE TABLE patients_cities (
    id_patient_city INT IDENTITY(1,1),
    id_patient INT NOT NULL,
    Ville NVARCHAR(100),
    PRIMARY KEY (id_patient, Ville),
);
