
import os
from rasterio.features import sieve
import argparse
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio.mask import mask
import numpy as np
import geopandas as gpd

# define arg
parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('-dir', '--directory', required=True, help='Specify directory that contains raster files')
parser.add_argument('-dir2', '--directory2', required=False, help='Specify directory that contains poria files', default=r'C:\Users\User\Documents\ProAg_2023_CC\PoriaNGridApr18Res30Vals0to4')
parser.add_argument('-s', '--size', required=False, type=int, default=15, help='minimum size of sieve kernel')
parser.add_argument('-conn', '--connectivity', required=False, type=int, default=4,
                    help='set connectivity to 4 or 8')
parser.add_argument('-dt', '--dtype', required=False, type=str, default='uint16', help='raster data type')
parser.add_argument('-f', '--from_values', required=False, nargs='+', type=int, default=[0, 1, 2, 3, 4, 5, 7],
                    help='set from values to reclassify')
parser.add_argument('-t', '--to_values', required=False, nargs='+', type=int,
                    default=[9100, 41, 21, 81, 11, 81, 9100],
                    help='set to values to reclassify')
parser.add_argument('-crops22', '--cropscape22', required=False, help='Specify directory that contains cropscape 2022', default=r"C:\Users\User\Documents\CropScape\CropScape2022_4326.tif")
parser.add_argument('-crops20', '--cropscape20', required=False, help='Specify directory that contains cropscape 2020', default=r"C:\Users\User\Documents\CropScape\CropScape2020_4326.tif")
parser.add_argument('-crops21', '--cropscape21', required=False, help='Specify directory that contains cropscape 2021', default=r"C:\Users\User\Documents\CropScape\CropScape2021_4326.tif")

parser.add_argument('-output_folder2', '--output_folder2', required=False, help='Specify directory that will contain cropscape masked tiles',
                    default=r'C:\Users\User\Desktop\test1')#r"C:\Users\User\Documents\ProAg_2023_CC\reduced_crops_test\cropscape_tiles")
parser.add_argument('-shapefile_path', '--shapefile_path', required=False, help='Specify directory that contains us_grid shapefile',
                    default=r"C:\Users\User\Documents\ProAg_2023_CC\us_grid_PAclus2023\us_grid_PAclus2023.shp")
args = parser.parse_args()
saveDir = args.directory
saveDir2 = args.directory2
output_folder2 = args.output_folder2
shapefile_path = args.shapefile_path
# cropscape rasters
cropscape22 = args.cropscape22
cropscape20 = args.cropscape20
cropscape21 = args.cropscape21

# us_grid tiles shapefile for clipping the cropscape raster to the CC relevant tile.
shapefile = gpd.read_file(shapefile_path)

# # Get a list of all the files in the input folders
files1 = os.listdir(saveDir)
files2 = os.listdir(saveDir2)
output_folder = saveDir # change to destination by CC date

# the list of tiles that are in areas that need post-classification masks
NorthArkansas_List = ['ILT0', 'MOT4', 'MOT7', 'MOT6', 'MOT5', 'TNT4', 'TNT3', 'ART20']
SouthArkansas_List = ['ART19', 'TNT0', 'MST23', 'ART15', 'MST20', 'MST19', 'ART11', 'MST16', 'MST15', 'ART7', 'MST13'
                        , 'MST12', 'ART3', 'MST8', 'MST4']
NorthTexas_area = ['TXT125', 'TXT130', 'TXT134', 'OKT34', 'TXT124', 'TXT129', 'TXT133', 'OKT33', 'TXT123', 'TXT128'
                        , 'TXT132', 'OKT32', 'TXT122', 'TXT127', 'TXT131', 'OKT31']
#######################################################################################################################
# match tile name in us_grid and CC tile - convert to polygon from multipolygon
def cropscapeToTile(raster_parts1, file1, output_folder2):
    for shape in shapefile['Name']:
        if shape == raster_parts1:

            name = shape
            polygon = shapefile.loc[shapefile['Name'] == shape]['geometry']

            # clip cropscape to the specific tile
            with rasterio.open(cropscape22) as crops22:
                out_image, out_transform = rasterio.mask.mask(crops22, polygon, crop=True)
                out_meta = crops22.meta
                out_meta.update({"driver": "GTiff",
                                 "height": out_image.shape[1],
                                 "width": out_image.shape[2],
                                 "transform": out_transform})

            with rasterio.open(os.path.join(output_folder2, name +"_2022_masked_tile.tif"), "w", **out_meta) as dst1:
                dst1.write(out_image)

            with rasterio.open(cropscape20) as crops20:
                out_image2, out_transform2 = rasterio.mask.mask(crops20, polygon, crop=True)
                out_meta2 = crops20.meta
                out_meta2.update({"driver": "GTiff",
                                 "height": out_image2.shape[1],
                                 "width": out_image2.shape[2],
                                 "transform": out_transform2})
            with rasterio.open(os.path.join(output_folder2, name + "_2020_masked_tile.tif"), "w",
                               **out_meta2) as dst2:
                dst2.write(out_image2)
            with rasterio.open(cropscape21) as crops21:
                out_image3, out_transform3 = rasterio.mask.mask(crops21, polygon, crop=True)
                out_meta3 = crops21.meta
                out_meta3.update({"driver": "GTiff",
                                 "height": out_image3.shape[1],
                                 "width": out_image3.shape[2],
                                 "transform": out_transform3})
            with rasterio.open(os.path.join(output_folder2, name + "_2021_masked_tile.tif"), "w",
                               **out_meta3) as dst3:
                dst3.write(out_image3)

            # transforms the masked tiles to the same crs and size of the CC raster
            with rasterio.open(os.path.join(saveDir, file1)) as src1, rasterio.open(os.path.join(output_folder2,name +"_2022_masked_tile.tif")) as tile22,\
                    rasterio.open(os.path.join(output_folder2, name +"_2020_masked_tile.tif")) as tile20, rasterio.open(os.path.join(output_folder2, name +"_2021_masked_tile.tif")) as tile21:
                # Reproject the input raster to match the multiplying raster

                tile22r = np.empty_like(src1.read(1).astype(args.dtype))
                reproject(
                    tile22.read(1).astype(args.dtype),
                    tile22r,
                    src_transform=tile22.transform,
                    src_crs=tile22.crs,
                    dst_transform=src1.transform,
                    dst_crs=src1.crs,
                    resampling=Resampling.nearest)
                tile20r = np.empty_like(src1.read(1).astype(args.dtype))
                reproject(
                    tile20.read(1).astype(args.dtype),
                    tile20r,
                    src_transform=tile20.transform,
                    src_crs=tile20.crs,
                    dst_transform=src1.transform,
                    dst_crs=src1.crs,
                    resampling=Resampling.nearest)
                tile21r = np.empty_like(src1.read(1).astype(args.dtype))
                reproject(
                    tile21.read(1).astype(args.dtype),
                    tile21r,
                    src_transform=tile21.transform,
                    src_crs=tile21.crs,
                    dst_transform=src1.transform,
                    dst_crs=src1.crs,
                    resampling=Resampling.nearest)
                print('Done Resampling')
            return tile22r, tile20r, tile21r
#######################################################################################################################
# loop over all files in the CC rasters folder
for file1 in files1:
    # Check if the file is a raster tiff
    if file1.endswith(".tif"):
        print(file1, 'file1-first')
        raster_name = str(file1[:-4])
        # Extract the split parts of the raster name from the file name
        raster_parts = os.path.splitext(file1)[0].split("_")
        raster_parts1 = raster_parts[1]
        print(raster_parts1, 'raster_part-first')
        # define the from and to values
        from_values = args.from_values
        to_values = args.to_values
        if raster_parts1 in SouthArkansas_List:

            tile22r, tile20r, tile21r = cropscapeToTile(raster_parts1, file1, output_folder2)
            with rasterio.open(os.path.join(saveDir, file1)) as src1:

                # apply masks by statements for south arkansas area tiles.
                raster = src1.read(1)
                raster_profile = src1.profile
                raster2 = raster  # for taking the corn fields classification last
                raster = np.where((tile21r == 5) & (tile22r == 5), 3, raster)
                raster = np.where((tile21r == 5) & (tile22r == 3), 3, raster)
                raster = np.where((tile21r == 2) & (tile22r == 2), 2, raster)
                raster = np.where((tile21r == 3) & (tile22r == 3), 0, raster)
                raster = np.where((tile21r == 3) & (tile22r == 3) & (tile22r == 3), 0, raster)
                raster = np.where((raster == 0) & (tile21r == 5), 5, raster)
                raster = np.where((tile21r == 0) & (tile22r == 0), 0, raster)
                raster = np.where(raster2 == 1, 1, raster)

                # Open the output raster file for writing\n",
            with rasterio.open(os.path.join(saveDir, raster_name + "_masked.tif"), "w",
                               **raster_profile) as dst2:
                # define the new values needed for second part of the code
                dst_name = dst2.name
                file1 = os.path.basename(dst_name)
                raster_parts = file1.split("_")
                raster_parts1 = raster_parts[1]
                dst2.write(raster.astype(rasterio.int16), 1)

        elif raster_parts1 in NorthArkansas_List:\

            tile22r, tile20r, tile21r = cropscapeToTile(raster_parts1, file1, output_folder2)

            with rasterio.open(os.path.join(saveDir, file1)) as src1:
            # apply masks by statements for north arkansas area tiles.
                raster = src1.read(1)
                raster2 = raster # for taking the corn fields classification last
                raster_profile = src1.profile
                raster = np.where((tile21r == 2) & (tile22r == 2), 2, raster)
                raster = np.where((tile21r == 2) & (tile22r == 1), 2, raster)
                raster = np.where((tile21r == 3) & (tile22r == 3), 0, raster)
                raster = np.where((tile21r == 0) & (tile22r == 0), 0, raster)
                raster = np.where(raster2 == 1, 1, raster)

            with rasterio.open(os.path.join(saveDir, raster_name + "_masked.tif"), "w", **raster_profile) as dst2:
                # Write the reclassified data to the output raster file
                # define the new values needed for second part of the code

                dst_name = dst2.name
                file1 = os.path.basename(dst_name)
                raster_parts = file1.split("_")
                raster_parts1 = raster_parts[1]
                dst2.write(raster.astype(rasterio.int16), 1)

        # Loop through each file in the second folder - Poria rasters
        for file2 in files2:
            # Check if the file is a raster and if its split parts match the first raster split parts - match CC rasters (regular or masked) and poria raster names.
            if file2.endswith(".tif"):
                raster_parts2 = os.path.splitext(file2)[0].split("_")
                raster_parts2 = raster_parts2[1]

                if len(raster_parts1) == len(raster_parts2) and all(
                        raster_parts1 == raster_parts2 for raster_parts1, raster_parts2 in
                        zip(raster_parts1, raster_parts2)):
                        # Open the two rasters using rasterio - CC and poria
                        with rasterio.open(os.path.join(saveDir, file1)) as src1, rasterio.open(os.path.join(saveDir2, file2)) as src2:
                            # Reproject the input raster to match the multiplying raster
                            reprojected_input_arr = np.empty_like(src1.read(1).astype(args.dtype))
                            reproject(
                                src2.read(1).astype(args.dtype),
                                reprojected_input_arr,
                                src_transform=src2.transform,
                                src_crs=src2.crs,
                                dst_transform=src1.transform,
                                dst_crs=src1.crs,
                                resampling=Resampling.nearest)

                            # Multiply the reprojected input numpy array by the multiplying raster numpy array - apply poria
                            reprojected_input_arr = np.where(reprojected_input_arr > 0, 1, 9102) #reprojected_input_arr = np.where(reprojected_input_arr > 0, 1, 0)
                            output_arr = reprojected_input_arr * src1.read(1).astype(args.dtype)
                            output_arr = np.where(output_arr >= 9102, 9102, output_arr)
                            output_arr = output_arr.astype(np.int16)
                            # apply sieve
                            array = sieve(output_arr, size=args.size, connectivity=args.connectivity)
                            # match CC args value to the new ones based on the USDA values.
                            for fv, tv in zip(from_values, to_values):
                                array = np.where(array == fv, tv, array)
                                # Create a new output raster file using the metadata from the multiplying raster file
                            output_profile = src1.profile
                            output_profile.update({"dtype": args.dtype})
                            # Write the output numpy array to the output raster file
                            with rasterio.open(os.path.join(output_folder, 'new_' + os.path.basename(file1)[:-4] + '_sieve+poria+masks.tif'), 'w',
                                               **output_profile) as output_dst:
                                print(output_dst.shape, 'output_dst.shape')
                                output_dst.write(array, 1)
                                print(f"Finished sieving & poria & masks & reclassifying: \n{file1} \nto: {output_folder}")


