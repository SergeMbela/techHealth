USE [health]
GO

/****** Object:  Table [dbo].[Patients]    Script Date: 11-05-25 13:49:54 ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

CREATE TABLE [dbo].[Patients](
    PatientID INT IDENTITY(1,1),
    FirstName NVARCHAR(100),
    LastName NVARCHAR(100),
    DateOfBirth DATE,
    Gender NVARCHAR(10),
    PhoneNumber NVARCHAR(100),
    Email NVARCHAR(100),
    Address NVARCHAR(255),
    EmergencyContactName NVARCHAR(100),
    EmergencyContactPhone NVARCHAR(100),
    BloodType NVARCHAR(3),
    Allergies NVARCHAR(MAX),
    MedicalHistory NVARCHAR(MAX),
    RegistrationDate DATETIME DEFAULT GETDATE(),
    analyse_id INT,
    CONSTRAINT [PK_Patients] PRIMARY KEY CLUSTERED 
    (
        [PatientID] ASC
    )WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO

-- Remove self-referencing foreign key as it's not needed
-- ALTER TABLE [dbo].[Patients]  WITH CHECK ADD FOREIGN KEY([patient_id])
-- REFERENCES [dbo].[Patients] ([PatientID])
-- GO