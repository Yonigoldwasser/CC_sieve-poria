# CC_sieve-poria
Takes the CC ratsers and the poria rasters based on their tile name and computes a masked based on poria raster and a sieve command.
outputs a new raster sieved and masked.

# sieve+poria_regularCC
Takes the CC ratsers and the poria rasters based on their tile name and computes a masked based on poria raster and a sieve command.
outputs a new raster sieved and masked - works on regular CC outputs

# sieve+poria_CropMask_regularCC
Code clips the cropscape years rasters by the polygon of the tile, then computes crop masks by area based on cropscape history.
Takes the CC ratsers and the poria rasters based on their tile name and computes a masked based on poria raster and a sieve command.
outputs a new raster seived and masked - works on regular CC outputs but adds crop masks by area. Apply only on early CC.
