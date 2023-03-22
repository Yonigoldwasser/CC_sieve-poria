
import logging
import os
from glob import glob
from rasterio.features import sieve
import rasterio
import numpy as np
import argparse
from rasterio.warp import reproject, Resampling

def main():
    # define arg
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-dir', '--directory', required=True, help='Specify directory that contains raster files')
    parser.add_argument('-dir2', '--directory2', required=True, help='Specify directory that contains poria files')
    parser.add_argument('-s', '--size', required=False, type=int, default=15, help='minimum size of sieve kernel')
    parser.add_argument('-conn', '--connectivity', required=False, type=int, default=4,
                        help='set connectivity to 4 or 8')
    parser.add_argument('-dt', '--dtype', required=False, type=str, default='uint16', help='raster data type')
    parser.add_argument('-f', '--from_values', required=False, nargs='+', type=int, default=[0, 1, 2, 3, 4, 5, 6, 8],
                        help='set from values to reclassify')
    parser.add_argument('-t', '--to_values', required=False, nargs='+', type=int,
                        default=[998, 41, 21, 81, 11, 81, 11, 998],
                        help='set to values to reclassify')
    args = parser.parse_args()
    saveDir = args.directory
    saveDir2 = args.directory2
    # Get a list of all the files in the input folders
    files1 = os.listdir(saveDir)
    files2 = os.listdir(saveDir2)
    output_folder = saveDir
    # Loop through each file in the first folder - CC rasters folders
    for file1 in files1:
        try:
            # Check if the file is a raster tiff
            if file1.endswith(".tif"):
                #print(file1)
                # Extract the split parts of the raster name from the file name
                raster_parts1 = os.path.splitext(file1)[0].split("_")
                raster_parts1 = raster_parts1[1]
                #print(raster_parts1)
                # Loop through each file in the second folder - Poria rasters
                for file2 in files2:
                    # Check if the file is a raster and its split parts match the first raster split parts - match CC rasters and poria ratsers names.
                    if file2.endswith(".tif"):
                        raster_parts2 = os.path.splitext(file2)[0].split("_")
                        #print(raster_parts2)
                        raster_parts2 = raster_parts2[1]
                        if len(raster_parts1) == len(raster_parts2) and all(
                                raster_parts1 == raster_parts2 for raster_parts1, raster_parts2 in
                                zip(raster_parts1, raster_parts2)):
                                # Open the two rasters using rasterio
                                with rasterio.open(os.path.join(saveDir, file1)) as src1, rasterio.open(os.path.join(saveDir2, file2)) as src2:
                                    # Reproject the input raster to match the multiplying raster
                                    #print(src1.profile, 'src1.profile')
                                    reprojected_input_arr = np.empty_like(src1.read(1).astype(args.dtype))
                                    reproject(
                                        src2.read(1).astype(args.dtype),
                                        reprojected_input_arr,
                                        src_transform=src2.transform,
                                        src_crs=src2.crs,
                                        dst_transform=src1.transform,
                                        dst_crs=src1.crs,
                                        resampling=Resampling.nearest)
                                    #print(reprojected_input_arr.shape,'reprojected_input_arr.shape')
                                    #print(reprojected_input_arr,'reprojected_input_arr')
                                    #print(src1.shape,'src1.shape')
                                    #print(src1,'src1')
                                    #print(src1.profile, 'src1.profile')
                                    #print(src1.read(1).astype(args.dtype), 'src1read')

                                    # Multiply the reprojected input numpy array by the multiplying raster numpy array
                                    output_arr = reprojected_input_arr * src1.read(1).astype(args.dtype)
                                    #print(output_arr.shape, 'output_arr.shap')
                                    output_arr = output_arr.astype(np.int16)
                                    #print(output_arr, 'output_arr')
                                    #print(output_arr.shape, 'output_arr.shap')

                                    array = sieve(output_arr, size=args.size, connectivity=args.connectivity)
                                    #print(array, 'arraybeforeseive')
                          # match CC args value to the new ones based on the USDA values.
                                    for fv, tv in zip(args.from_values, args.to_values):
                                        array = np.where(array == fv, tv, array)
                                        # Create a new output raster file using the metadata from the multiplying raster file
                                    #print(array.shape,'array.shape')
                                    #print(array,'array')
                                    output_profile = src1.profile
                                    output_profile.update({"dtype": args.dtype})
                                    #print(output_profile,'output_profil')
                                    # Write the output numpy array to the output raster file
                                    with rasterio.open(os.path.join(output_folder, 'new_' + os.path.basename(file1)[:-4] + '_seive+poria.tif'), 'w',
                                                       **output_profile) as output_dst:
                                        #print(output_dst.shape, 'output_dst.shape')
                                        output_dst.write(array, 1)
                                        print(f"Finished sieving & poria & reclassifying: \n{file1} \nto: {output_folder}")
        except Exception as e:
            print(f"Failed to sieve & reclassify: \n{file1} \n{e}")
            logging.exception(f'exception in {file1} \n{e}')
            continue

if __name__ == '__main__':
    main()
