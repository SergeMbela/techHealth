USE [health]
GO

/****** Object:  Table [dbo].[Villes]    Script Date: 07-05-25 15:45:29 ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

CREATE TABLE [dbo].[Villes](
	[Ville] [nvarchar](100) NULL,
	[Latitude] [float] NULL,
	[Longitude] [float] NULL,
	[Population] [int] NULL,
	[PM25] [float] NULL,
	[NO2] [float] NULL,
	[O3] [float] NULL,
	[Grippe_Cas_100k] [int] NULL,
	[Hospitalisations_Grippe_Pourcentage] [float] NULL,
 CONSTRAINT [UQ_Ville_Latitude_Longitude] UNIQUE NONCLUSTERED 
(
	[Ville] ASC,
	[Latitude] ASC,
	[Longitude] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO

