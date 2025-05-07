ALTER TABLE [dbo].[Villes]
ADD CONSTRAINT UQ_Ville_Latitude_Longitude UNIQUE ([Ville], [Latitude], [Longitude]);
