USE [health]
GO

/****** Object:  Table [dbo].[vaccinations_grippe]    Script Date: 11-05-25 14:40:11 ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

CREATE TABLE [dbo].[vaccinations_grippe](
	[vaccination_id] [int] IDENTITY(1,1) NOT NULL,
	[patient_id] [int] NULL,
	[date_vaccination] [date] NOT NULL,
	[lot_vaccin] [nvarchar](50) NULL,
PRIMARY KEY CLUSTERED 
(
	[vaccination_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO

ALTER TABLE [dbo].[vaccinations_grippe]  WITH CHECK ADD FOREIGN KEY([patient_id])
REFERENCES [dbo].[Patients] ([PatientID])
GO