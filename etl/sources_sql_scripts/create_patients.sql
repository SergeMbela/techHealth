USE [health]
GO

/****** Object:  Table [dbo].[prises_sang]    Script Date: 11-05-25 13:49:54 ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

CREATE TABLE [dbo].[prises_sang](
	[analyse_id] [int] IDENTITY(1,1) NOT NULL,
	[patient_id] [int] NULL,
	[date_analyse] [date] NOT NULL,
	[crp] [float] NULL,
	[leucocytes] [float] NULL,
	[lymphocytes] [float] NULL,
	[neutrophiles] [float] NULL,
	[remarque] [nvarchar](255) NULL,
	[positif_grippe] [bit] NULL,
PRIMARY KEY CLUSTERED 
(
	[analyse_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO

ALTER TABLE [dbo].[prises_sang]  WITH CHECK ADD FOREIGN KEY([patient_id])
REFERENCES [dbo].[PatientsbKP] ([PatientID])
GO