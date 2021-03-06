from cryptography.fernet import Fernet
from os import remove, scandir, path as p, listdir
from shutil import rmtree
from zipfile import ZipFile


def write_key(key_name):
    """
    Generates a key and save it into a file
    """
    key = Fernet.generate_key()
    with open(key_name, "wb") as key_file:
        key_file.write(key)


def load_key(key_name):
    """
    Given a key_name (str), system will generate or use that key
    """
    if not p.exists(key_name):
        write_key(key_name)

    return open(key_name, "rb").read()


def encrypt(path, key, compress):
    """
    Given a path (str) and key (str), it check if path is a file or a dir
    """
    key = load_key(key)

    # check is it a directory
    if p.isdir(path):
        # encrypt a directory
        encrypt_dir(path, key, compress)
        # check if user want to compress the director
        if compress:
            # compress directory
            compress_dir(path)
            # encrypt compressed file
            encrypt_file(path + "-encrypted.zip", key)
        return
    return encrypt_file(path, key)


def decrypt(path, key):
    """
    Given a path (str) and key (str), it check if path is a file or a dir
    """
    key = load_key(key)

    if p.isdir(path):
        # encrypt a directory
        return decrypt_dir(path, key)
    # decrypt a file
    path = decrypt_file(path, key)
    # check if file contains suffix
    if "-encrypted.zip" in path:
        return decrypt_dir(path, key)
    return


def generate_new_filename(path, key, encrypt):
    """
    Given a path (str) and key (bytes), it encrypt filename
    """
    # init fermet
    f = Fernet(key)
    # split path and filename
    filename = path
    fullpath = ""
    if "/" in path:
        fullpaths = path.split("/")
        filename = fullpaths[-1]
        fullpath = ""
        for x in fullpaths:
            if x != filename:
                fullpath += x + "/"

    if encrypt:
        # encode filename
        filename = f.encrypt(filename.encode("utf-8")).decode("utf-8")
    else:
        # decode filename
        filename = f.decrypt(filename.encode("utf-8")).decode("utf-8")

    return fullpath + filename


def encrypt_file(filename, key):
    """
    Given a filename (str) and key (bytes), it encrypts the file and write it
    """
    # init fermet
    f = Fernet(key)
    with open(filename, "rb") as file:
        # read all file data
        file_data = file.read()
    # encrypt data
    encrypted_data = f.encrypt(file_data)
    # delete file
    remove(filename)
    # generate new filename
    new_filename = generate_new_filename(filename, key, True)
    # write the encrypted file
    with open(new_filename, "wb") as file:
        print("Encrypted: " + new_filename)
        file.write(encrypted_data)

    return new_filename


def decrypt_file(filename, key):
    """
    Given a filename (str) and key (bytes), it decrypts the file and write it
    """
    f = Fernet(key)
    with open(filename, "rb") as file:
        # read the encrypted data
        encrypted_data = file.read()
    # decrypt data
    decrypted_data = f.decrypt(encrypted_data)
    # delete file
    remove(filename)
    # generate new filename
    new_filename = generate_new_filename(filename, key, False)
    # write the encrypted file
    with open(new_filename, "wb") as file:
        print("Decrypted: " + new_filename)
        file.write(decrypted_data)

    return new_filename


def encrypt_dir(path, key, compress):
    """
    Given path (str) and key (bytes), It encrypts files on a directory and
    write with encoded name
    """
    # scan directory
    for file in scandir(path):
        # if file is a directory
        if p.isdir(file):
            # define root
            root = p.join(path, file.name)
            # return this function
            encrypt_dir(root, key, compress)
            # check if user want to compress the folder
            if compress:
                # define filepath
                filepath = p.join(root, path)
                # compress directory
                compress_dir(filepath)
                # encrypt compressed file
                encrypt_file(filepath + "-encrypted.zip", key)
        else:
            # define fullpath
            fullpath = p.join(path, file.name)
            # encrypt a file
            encrypt_file(fullpath, key)
    return


def decrypt_dir(path, key):
    """
    Given path (str) and key (bytes), It encrypts files on a directory and
    write with encoded name
    """
    # get ext
    ext = p.splitext(path)[-1]
    # check is it a dir or a file
    if p.isdir(path):
        for file in scandir(path):
            # if file is a directory
            if p.isdir(file):
                # define root
                root = p.join(path, file.name)
                # return this function
                decrypt_dir(root, key)
            else:
                # define fullpath
                fullpath = p.join(path, file.name)
                # decrypt file
                decrypt_file(fullpath, key)

    if p.isfile(path) and ext == ".zip":
        # check is it a normal zip file or is it a encrypted zip file
        if "-encrypted.zip" in path:
            # extracr zip
            extract_dir(path)
            # get dirname
            dirname = path[0:-14]
            return decrypt_dir(dirname, key)


def get_all_files(dirname):
    filepaths = []
    for file in listdir(dirname):
        filepath = p.join(dirname, file)
        filepaths.append(filepath)

    return filepaths


def compress_dir(dirname):
    # print information
    print("compressing " + dirname)
    # get all files in the directory
    filepaths = get_all_files(dirname)

    # open a zip file in write mode
    with ZipFile(dirname + "-encrypted.zip", "w") as zip:
        # looping all files in the directory
        for file in filepaths:
            # print all files
            print("Compressing " + file)
            # store file in zip
            zip.write(file)

    # remove directory
    rmtree(dirname)
    return


def extract_dir(filename):
    # print information
    print("extracting " + filename)
    # open filw with zipfile in read mode
    with ZipFile(filename, "r") as zip:
        # print all contents of zip file
        zip.printdir()
        # extract all contents of zip file
        zip.extractall()

    # remove zip file
    remove(filename)
    return


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="Simple File Encryptor Script")
    parser.add_argument("path", help="Path to encrypt/decrypt")
    parser.add_argument("-k", "--key-path", dest="key",
                        help="Whether to generate a new key or use existing")
    parser.add_argument("-e", "--encrypt", action="store_true",
                        help="Whether to encrypt the file, "
                        + "only -e or -d can be specified.")
    parser.add_argument("-d", "--decrypt", action="store_true",
                        help="Whether to decrypt the file, "
                        + "only -e or -d can be specified.")
    parser.add_argument("-c", "--compress", action="store_true",
                        help="If you encrypt a directory, you can compress"
                        + " it with set this flag")

    args = parser.parse_args()
    compress = args.compress
    key = args.key
    path = args.path

    if key:
        # split keyname
        key_name, ext = p.splitext(key)
        if ext != ".key":
            raise TypeError("Only .key file are allow")
    else:
        raise TypeError("Please specify path to key file.")

    encrypt_ = args.encrypt
    decrypt_ = args.decrypt

    if encrypt_ and decrypt_:
        raise TypeError("Please specify whether you want "
                        + "to encrypt the path or decrypt it.")
    elif encrypt_:
        if path:
            print("encrypting " + path)
            encrypt(path, key, compress)
        else:
            raise TypeError("Please specify path")
    elif decrypt_:
        if path:
            print("decrypting " + path)
            decrypt(path, key)
        else:
            raise TypeError("Please specify path")
    else:
        raise TypeError("Please specify whether you want "
                        + "to encrypt the path or decrypt it.")
