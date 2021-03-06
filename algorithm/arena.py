import logging
from enum import Enum

# if __name__ == "__main__":
#    logging.basicConfig(filename=__file__+".log", level=logging.DEBUG)


class Arena():
    # already have a internal map
    def __init__(self, height=20, width=15):
        self.arena_map = [[CellType.UNKNOWN
                           for y in range(width)]
                          for x in range(height)]

    def from_mdf_strings(self, part1, part2):
        if part1 is None or part1 == "" or part2 is None or part2 == "":
            return

        b1Size = len(part1) * 4
        bitStr1 = str(bin(int(part1, 16)))[4:b1Size]

        b2Size = len(part2) * 4
        bitStr2 = (str(bin(int(part2, 16)))[2:b2Size+2]).zfill(b2Size)

        for x in range(len(self.arena_map)):
            for y in range(len(self.arena_map[x])):
                if bitStr1[(x*len(self.arena_map[x]))+y] == "0":
                    self.arena_map[x][y] = CellType.UNKNOWN
                else:
                    self.arena_map[x][y] = CellType.EMPTY

        bitCount = 0

        for x in range(len(self.arena_map)):
            for y in range(len(self.arena_map[x])):
                if self.arena_map[x][y] == CellType.EMPTY:
                    self.arena_map[x][y] = CellType(int(bitStr2[bitCount]))
                    bitCount += 1

        return

    def to_mdf_part1(self, withPadding=True):
        map = self.arena_map

        bitStr = ""

        for x in range(len(map)):
            for y in range(len(map[x])):
                if map[x][y] == CellType.UNKNOWN or map[x][y] == CellType.CONFLICT:
                    bitStr += "0"
                else:
                    bitStr += "1"

        if withPadding:
            bitStr = "11" + bitStr + "11"

        return '{:0{}X}'.format(int(bitStr, 2), len(bitStr) // 4)

    def to_mdf_part2(self, withPadding=True):
        map = self.arena_map

        bitStr = ""

        for x in range(len(map)):
            for y in range(len(map[x])):
                if map[x][y] == CellType.EMPTY:
                    bitStr += "0"
                elif map[x][y] == CellType.OBSTACLE:
                    bitStr += "1"

        if withPadding:
            toPad = 8 - len(bitStr) % 8
            for i in range(toPad):
                bitStr += "0"

        return '{:0{}X}'.format(int(bitStr, 2), len(bitStr) // 4)

    def get_2d_arr(self):
        return self.arena_map

    def print(self):
        print(self.display_str())

    def display_str(self, robot=None):
        map_str = ""
        for x in range(len(self.arena_map)):
            for y in range(len(self.arena_map[x])):
                cell_value = self.arena_map[len(self.arena_map)-1-x][y].value
                cell_str = ""
                if cell_value < 0:
                    cell_str = str(cell_value) + " "
                else:
                    cell_str = " " + str(cell_value) + " "
                if robot != None:
                    if robot[0] == len(self.arena_map)-1-x and robot[1] == y:
                        cell_str = " X "
                map_str += cell_str + " "
            map_str += "\n"
        return map_str

    def get(self, h, w):
        return self.arena_map[h][w]

    def set(self, h, w, value):
        self.arena_map[h][w] = value


class CellType(Enum):
    UNKNOWN = -1
    EMPTY = 0
    OBSTACLE = 1
    CONFLICT = 2
