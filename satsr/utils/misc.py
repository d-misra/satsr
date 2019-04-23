import os
from distutils.dir_util import copy_tree
import io
import tarfile
import zipfile

import numpy as np
import imageio
from keras import callbacks

from satsr import paths


def create_dir_tree():
    """
    Create directory tree structure
    """
    dirs = paths.get_dirs()
    for d in dirs.values():
        if not os.path.isdir(d):
            print('creating {}'.format(d))
            os.makedirs(d)


# The percentile_data argument is used to plot superresolved and original data
# with a comparable black/white scale
def save_band(data, name, percentile_data=None):
    if percentile_data is None:
        percentile_data = data
    mi, ma = np.percentile(percentile_data, (1, 99))
    band_data = np.clip(data, mi, ma)
    band_data = (band_data - mi) / (ma - mi)
    imageio.imsave(name + ".png", band_data)  # img_as_uint(band_data))


def backup_splits():
    """
    Save the data splits used during training to the timestamped dir.
    """
    src = paths.get_splits_dir()
    dst = paths.get_ts_splits_dir()
    copy_tree(src, dst)


def get_callbacks():
    callback_list = []

    # filepath = out_path + model_nr + 'lr_{:.0e}.hdf5'.format(lr)
    # callback_list.append(callbacks.ModelCheckpoint(filepath,
    #                                                monitor='val_loss',
    #                                                verbose=1,
    #                                                save_best_only=True,
    #                                                save_weights_only=False,
    #                                                mode='auto'))

    callback_list.append(callbacks.ReduceLROnPlateau(monitor='val_loss',
                                                     factor=0.5,
                                                     patience=5,
                                                     verbose=1,
                                                     epsilon=1e-6,
                                                     cooldown=20,
                                                     min_lr=1e-5))

    return callback_list


def open_compressed(byte_stream, file_format, output_folder):
    """
    Extract and save a stream of bytes of a compressed file from memory.

    Parameters
    ----------
    byte_stream : bytes
    file_format : str
        Compatible file formats: tarballs, zip files
    output_folder : str
        Folder to extract the stream

    Returns
    -------
    Folder name of the extracted files.
    """

    tar_extensions = ['tar', 'bz2', 'tb2', 'tbz', 'tbz2', 'gz', 'tgz', 'lz', 'lzma', 'tlz', 'xz', 'txz', 'Z', 'tZ']
    if file_format in tar_extensions:
        tar = tarfile.open(mode="r:{}".format(file_format), fileobj=io.BytesIO(byte_stream))
        tar.extractall(output_folder)
        folder_name = tar.getnames()[0]
        return os.path.join(output_folder, folder_name)

    elif file_format == 'zip':
        zf = zipfile.ZipFile(io.BytesIO(byte_stream))
        zf.extractall(output_folder)
        folder_name = zf.namelist()[0].split('/')[0]
        return os.path.join(output_folder, folder_name)

    else:
        raise ValueError('Invalid file format for the compressed byte_stream')