import random
from pathlib import Path
from matplotlib.image import imread, imsave
import numpy as np

def rgb2gray(rgb):
    r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
    gray = 0.2989 * r + 0.5870 * g + 0.1140 * b
    return gray


class Img:

    def __init__(self, path):
        """
        Do not change the constructor implementation
        """
        self.path = Path(path)
        self.data = rgb2gray(imread(path)).tolist()

    def save_img(self):
        """
        Do not change the below implementation
        """
        new_path = self.path.with_name(self.path.stem + '_filtered' + self.path.suffix)
        imsave(new_path, self.data, cmap='gray')
        return new_path

    def blur(self, blur_level=16):

        height = len(self.data)
        width = len(self.data[0])
        filter_sum = blur_level ** 2

        result = []
        for i in range(height - blur_level + 1):
            row_result = []
            for j in range(width - blur_level + 1):
                sub_matrix = [row[j:j + blur_level] for row in self.data[i:i + blur_level]]
                average = sum(sum(sub_row) for sub_row in sub_matrix) // filter_sum
                row_result.append(average)
            result.append(row_result)

        self.data = result

    def contour(self):
        for i, row in enumerate(self.data):
            res = []
            for j in range(1, len(row)):
                res.append(abs(row[j-1] - row[j]))

            self.data[i] = res

    def rotate(self):
        self.data =np.rot90(self.data, k = -1)
        self.data = self.data.tolist()
        return self

    def salt_n_pepper(self):

        amount = 0.02
        noisy_img = [row[:]for row in self.data]
        height = len(noisy_img)
        width = len(noisy_img[0])

        num_pixels = height*width
        num_salt = int(amount * num_pixels /2)
        num_pepper = int( amount * num_pixels /2)

        for i in range(num_salt):
            j = random.randint(0, height - 1)
            k = random.randint(0, width - 1)
            noisy_img[j][k] = 255

        for i in range(num_salt):
            j = random.randint(0, height - 1)
            k = random.randint(0, width - 1)
            noisy_img[j][k] = 0

        self.data = noisy_img
        return self


    def concat(self, other_img, direction='horizontal'):
        if direction == 'horizontal':
            # Make sure both images have the same height
            if len(self.data) != len(other_img.data):
                raise ValueError("Images must have the same height for horizontal concatenation")
            self.data = [row1 + row2 for row1, row2 in zip(self.data, other_img.data)]

        elif direction == 'vertical':
            # Make sure both images have the same width
            if len(self.data[0]) != len(other_img.data[0]):
                raise ValueError("Images must have the same width for vertical concatenation")
            self.data = self.data + other_img.data

        else:
            raise ValueError("Invalid direction: choose 'horizontal' or 'vertical'")

        return self

    def segment(self):
        self.data = [
            [255 if pixel >= 128 else 0 for pixel in row]
            for row in self.data
        ]
        return self
