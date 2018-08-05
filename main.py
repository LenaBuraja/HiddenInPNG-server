import math
import random as random
import hashlib
import struct

from operator import xor

import numpy as np
from PIL import Image


def noise(img_data):
    shape = img_data.shape
    for y in range(shape[0]):
        for x in range(shape[1]):
            for channel in range(shape[2]):
                img_data[y][x][channel] = \
                    img_data[y][x][channel] // 2 * 2 + random.randint(0, 1)
    return img_data


def shuffle(length, key):
    def get_h(x):
        return int(hashlib.sha256(x.encode('utf8')).hexdigest(), base=16)

    result = list(range(length))
    hash_iter = 0
    hash_s = 2 ** 256
    h = get_h(str(hash_iter) + key)
    for i in range(length - 1):
        while h >= (length - i) * (hash_s // (length - 1)):
            hash_iter += 1
            hash_s = 2 ** 256
            h = get_h(str(hash_iter) + key)
        n = i + h % (length - i)
        hash_s //= (length - 1)
        h //= (length - 1)
        (result[i], result[n]) = (result[n], result[i])
    return result


def encrypt(source_data, key):
    salt = []
    salt_len = 0
    source_data_len = len(source_data)
    hash_iter = 0
    while salt_len < source_data_len:
        salt += list(hashlib.sha256((key + str(hash_iter)).encode('utf8')).digest())
        hash_iter += 1
        salt_len += 32
    return list(map(xor, source_data, salt[:source_data_len]))


def get_optimal_significant_bits_count(bytes_count):
    result = 1
    power_of_two = 2
    while power_of_two < bytes_count - result:
        result, power_of_two = result + 1, power_of_two * 2
    return result


def set_bit(img_data, ind, new_bit):
    y, x, c = ind // img_data.shape[1] // 4, (ind // 4) % img_data.shape[1], ind % 4
    img_data[y][x][c] = img_data[y][x][c] // 2 * 2 + new_bit


def get_bit(img_data, ind):
    y, x, c = ind // img_data.shape[1] // 4, (ind // 4) % img_data.shape[1], ind % 4
    return img_data[y][x][c] % 2


def get_signification_length(bits_count): return int(math.ceil(bits_count / 8))


def get_signification(message_length, bytes_count):
    message_len = message_length
    significant_bits_count = get_optimal_significant_bits_count(bytes_count)
    signification_length = get_signification_length(significant_bits_count)
    signification = list(message_len.to_bytes(signification_length, 'little'))
    return significant_bits_count, signification


def encode(img_data, message, key):
    shape = img_data.shape
    print('noise')
    noise(img_data)
    print('encryption')
    encrypted_message = encrypt(message.encode('utf8'), key)
    print('shuffling')
    bytes_count = shape[0] * shape[1] * shape[2]
    order = shuffle(bytes_count, key)
    print('signification')
    significant_bits_count, signification = get_signification(len(encrypted_message), shape[0] * shape[1] * shape[2])
    if len(message) * 8 > bytes_count - significant_bits_count:
        raise Exception('message too long')
    print('significant bytes: ', signification)
    print('concretion signification')
    for i in range(significant_bits_count):
        j = i // 8
        set_bit(
            img_data,
            order[8 * j + (7 - i % 8 if j < significant_bits_count // 8 else significant_bits_count - i - 1)],
            signification[j] % 2
        )
        signification[j] //= 2
    print('message concretion')
    for i in range(len(encrypted_message)):
        for j in range(8):
            set_bit(img_data, order[i * 8 + j + significant_bits_count], encrypted_message[i] % 2)
            encrypted_message[i] //= 2
    return img_data


def decode(img_data, key):
    shape = img_data.shape
    w = shape[1]
    print('shuffling')
    bytes_count = shape[0] * shape[1] * shape[2]
    order = shuffle(bytes_count, key)
    print('de-signification')
    significant_bits_count = get_optimal_significant_bits_count(bytes_count)
    signification_length = get_signification_length(significant_bits_count)
    signification = [0 for _ in range(signification_length)]
    for i in range(significant_bits_count):
        j = i // 8
        signification[j] = signification[j] * 2 + get_bit(img_data, order[i])
    print('significant bytes: ', signification)
    signification = struct.pack(('B' * signification_length).format(signification_length), *signification)
    print('message retrieval')
    message_length = int.from_bytes(signification, 'little')
    result = [0 for _ in range(message_length)]
    for i in range(message_length):
        for j in range(8):
            ind = order[i * 8 + 7 - j + significant_bits_count]
            y = ind // w // 4
            x = (ind // 4) % w
            c = ind % 4
            bit = img_data[y][x][c] % 2
            result[i] = result[i] * 2 + bit
    result = encrypt(result, key)
    return bytearray(result).decode('utf8')


def demo():
    print('ENCRYPTION')
    img_data = np.array(Image.open('orig.png').convert('RGBA'))
    message =\
        'The byteorder argument determines the byte order used to represent the integer. If byteorder is "big",' \
        ' the most significant byte is at the beginning of the byte array. If byteorder is "little", the most ' \
        'significant byte is at the end of the byte array. To request the native byte order of the host system,' \
        ' use sys.byteorder as the byte order value.'
    encode(img_data, message, 'strongKey')
    encoded_img = Image.fromarray(img_data, 'RGBA')
    # encoded_img.show()
    encoded_img.save('result.png', 'PNG')

    print('DECRYPTION')
    img_data = np.array(Image.open('result.png').convert('RGBA'))
    print(decode(img_data, 'strongKey'))


# demo()
