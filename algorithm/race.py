from arena import Arena, CellType
import utils

        
def detectCollision(mymap, pos, robotsize=(3,3)): #take care of robot size in here, outside of this function the robot is treated as a 1x1 object
    # pos is the middle cell (for 3x3) that the robot takes
    # treat the system as the collecitons of all the point that the robot covers
    (x,y) = pos
    system = [pos, (x+1, y), (x+1, y+1), (x, y+1), (x-1, y+1), (x-1, y), (x-1, y-1), (x, y-1), (x+1, y-1)]
    for p in system:
        # collide with walls
        if p[0] < 0 or p[0] >= len(mymap) or p[1] < 0 or p[1] >= len(mymap[0]):
            return True
        # there is obstacle at p
        if mymap[p[0]][p[1]] != CellType.EMPTY:
            return True
    return False

def neighbors(mymap, cur): # cur is (x,y,d)
    '''
    return a list of neightbor
    each neighbor have the data structure: (neighborPos, moveCost, move)
    '''
    def elementWiseAdd(a, b):
        return tuple([sum(x) for x in zip(a, b)])
    x, y, d = cur
    offsets_n = [(1,0), (0,1), (-1,0), (0,-1)]
    offsets_e = [(0,1), (-1,0), (0,-1), (1,0)]
    offsets_s = [(-1,0), (0,-1), (1,0), (0,1)]
    offsets_w = [(0,-1), (1,0), (0,1), (-1,0)]
    offsets = {
        0: offsets_n,
        1: offsets_e,
        2: offsets_s,
        3: offsets_w
    }[d]

    neighbors = []
    for i in range(1,4): # add states can achieved by stand still and turn
        neighbor_pos = (x,y, (d+i)%4)
        if i == 2:
            moveCost = 4
        else:
            moveCost = 2
        move = {
            1: "R",
            2: "RR",
            3: "L"
        }[i]
        neighbors.append((neighbor_pos, moveCost, move))
    ##############
    for i in range(len(offsets)):
        (neighborX, neighborY) = elementWiseAdd((x,y), offsets[i])
        if i != 2:
            neighborD = (d+i)%4
        else:
            neighborD = d
        neighborPos = (neighborX, neighborY, neighborD)
        (moveCost, move) = {
            0: (1, "F"),
            1: (2, "RF"),
            2: (1, "B"),
            3: (2, "LF")
        }[i]
        
        # AQ added

        wallCells = {0:[],
                    1:[],
                    2:[],
                    3:[]
                }
        for j in range(1,19):
            wallCells[0].append([j,13])
            wallCells[2].append([j,1])
            if 1 <= j <= 13:
                wallCells[1].append([1,j])
                wallCells[3].append([18,j])
        if (cur[0],cur[1]) in wallCells[cur[2]] :
            print("in wall cells")
            moveCost -= 1
            
            
        if i == 0:# or i == 2: #only allow forward # only allow moving forward or backward
            neighbors.append((neighborPos, moveCost, move))
    return neighbors

def popMin(costs):
    k = min(costs, key=costs.get)
    cur = k
    curCost = costs[k]
    del costs[k]
    return (cur, curCost)
def dijkstra(mymap, start, end, endOrientationImportant = False, isExploring = False, Hcounter = 0, Vcounter = 0):
    ''' 
    return: tuple of instruction string with the final orientation of the robot after executing these instructions,
    and the total cost to reach that state
    param:
        mymap: 2d array of CellType representing the map
        start: triple of the start position including x,y coordinates and the orientation
        end: end position, same data structure as start
    '''
    calibratedWall = False
    wallCells = {0:[],
                1:[],
                2:[],
                3:[]
            }
    for i in range(1,19):
        wallCells[0].append([i,13])
        wallCells[2].append([i,1])
        if 1 <= i <= 13:
            wallCells[1].append([1,i])
            wallCells[3].append([18,i])
            
    costs = {}  # a dict storing with key is the state and value is the cost of the path that leads to it
                # structure of each element is: (x,y,d):cost
    prev = {}   # k:v == (x,y,d): ((xx, yy, dd), move_to_go_next),
                # where from (xx, yy, dd) the robot takes move_to_go_next and end up in (x, y, d)
    # initialise(costs, start)  # set all the costs to infinity, except for the start state
    for x in range(len(mymap)):
        for y in range(len(mymap[0])):
            for d in range(4):
                costs[(x,y,d)] = 1000
    costs[start] = 0
    if endOrientationImportant:
        compareEndUntil = None
    else:
        compareEndUntil = -1
    while True:
        cur, curCost = popMin(costs)    # get the item with min cost and remove it from the dict
        #if end == (18, 13, 0):
            #print("in djikstra: cur ", cur, curCost)
        if cur[:compareEndUntil] == end[:compareEndUntil]:
            # store the final minimal cost if needed
            # trace back the path here
            temp = cur
            path = [(cur, "")]
            # print("In djikstra: on end: prev", prev)
            while prev.get(temp) != None:
                p = prev[temp]
                path.insert(0, p)
                temp = p[0]
            ins = ""
            ins_noCali = "" #AQ added
            count = Hcounter + Vcounter
            for item in path:
                sensor = checkAlign(1,item[0],mymap)
                print("dijkstra counter:",count)
                if count <= 1:
                    sensor = ''
                ins += ''.join([sensor,item[1]])
                if [item[0][0],item[0][1]] in wallCells[0] and item[0][2] == 1 and calibratedWall == False:  # at wallCells[0], do one front calibration to avoid bumper hit wall
                    ins_noCali += ''.join(['CF000',item[1]])
                    calibratedWall = True  # a flag only, because should only do one calibration
                else:
                    ins_noCali += item[1]
                if len(sensor) != 0:
                    count = 0
                else:
                    if "R" in item[1] or "L" in item[1] or "B" in item[1]:
                        print("count add 1")
                        count += 1
                    if "F" in item[1]:
                        count += 0.5
                        print("count add 0.5")
            if isExploring == True:
                return (ins, cur, curCost, ins_noCali)
            # check all calibration possibilities
            return (ins, cur, curCost)
        for neighbor in neighbors(mymap, cur):
            neighborPos, moveCost, move = neighbor
            if not detectCollision(mymap, neighborPos[:-1]):
                if costs.get(neighborPos) != None: # has not been popped out (cost fixed)
                    if costs[neighborPos] > curCost + moveCost:
                        costs[neighborPos] = curCost + moveCost
                        prev[neighborPos] = (cur, move)

def getInstructions(map, waypoint, robotsize=(3,3), direction='north'):
    map.print()
    dir = 0
    if direction[0] == "n":
        dir = 0
    if direction[0] == "e":
        dir = 1
    if direction[0] == "s":
        dir = 2
    if direction[0] == "w":
        dir = 3
    instruction = ""
    mymap = map.get_2d_arr()
    waypoint = (waypoint[0], waypoint[1], 0) # padding 0 at the 3rd position to make it work with djikstra
    mymap[waypoint[0]][waypoint[1]] = CellType.EMPTY # cuz waypoint is marked as -1
    (instruction1, endpoint1, totalCost, instr1_noCalibration) = dijkstra(mymap, (1, 1, dir), waypoint, endOrientationImportant = False, isExploring = True)  #isExploring is set to True because the fastest path now wants to take off calibration
    print("In getInstruction: reached waypoint", endpoint1)
    (instruction2, endpoint2, totalCost, instr2_noCalibration) = dijkstra(mymap, endpoint1, (18,13, 0), endOrientationImportant = False, isExploring = True)
    print("nothing in your eyes", instruction2, endpoint2)
    print("In getInstruction: reached goal")
    print(instr1_noCalibration+instr2_noCalibration)
    return instr1_noCalibration+instr2_noCalibration

def checkAlign(r,position,mymap):
    
    frontCells = {0:[[[2,-1],[3,-1],[4,-1]],[[2,0],[3,0],[4,0]],[[2,1],[3,1],[4,1]]],
                    1:[[[1,2],[1,3],[1,4]],[[0,2],[0,3],[0,4]],[[-1,2],[-1,3],[-1,4]]],
                    2:[[[-2,1],[-3,1],[-4,1]],[[-2,0],[-3,0],[-4,0]],[[-2,-1],[-3,-1],[-4,-1]]],
                    3:[[[-1,-2],[-1,-3],[-1,-4]],[[0,-2],[0,-3],[0,-4]],[[1,-2],[1,-3],[1,-4]]]
            }
        # only keep top right and bottom right lines
    rightCells = {0:[[[1,2],[1,3],[1,4]],[[-1,2],[-1,3],[-1,4]],[[0,2],[0,3],[0,4]]],
                    1:[[[-2,1],[-3,1],[-4,1]],[[-2,-1],[-3,-1],[-4,-1]],[[-2,0],[-3,0],[-4,0]]],
                    2:[[[-1,-2],[-1,-3],[-1,-4]],[[1,-2],[1,-3],[1,-4]],[[0,-2],[0,-3],[0,-4]]],
                    3:[[[2,-1],[3,-1],[4,-1]],[[2,1],[3,1],[4,1]],[[2,0],[3,0],[4,0]]]
            }
    leftAllCells = {0:[[1,-2],[1,-3],[1,-4],[0,-2],[0,-3],[0,-4],[-1,-2],[-1,-3],[-1,-4]],
                             1:[[2,1],[3,1],[4,1],[2,0],[3,0],[4,0],[2,-1],[3,-1],[4,-1]],
                             2:[[-1,2],[-1,3],[-1,4],[0,2],[0,3],[0,4],[1,2],[1,3],[1,4]],
                             3:[[-2,-1],[-3,-1],[-4,-1],[-2,0],[-3,0],[-4,0],[-2,1],[-3,1],[-4,1]]
                }
        # positions in wallCells are for calibration
    wallCells = {0:[],
                1:[],
                2:[],
                3:[]
            }
    for i in range(1,19):
        wallCells[0].append([i,13])
        wallCells[2].append([i,1])
        if 1 <= i <= 13:
            wallCells[1].append([1,i])
            wallCells[3].append([18,i])

    alignSensor = ''
    head = int(position[2])
    if head > 0:
        head1 = head- 1
    else:
        head1 = 3
    i = 0    
    frontCells = frontCells[head]
    rightCells = rightCells[head]
    h = position[0]
    w = position[1]
    
    if [h,w] == [18,13]:
        return ''
    # check curner cell conditoin, if corner cell, just do two 
    if [h,w] in wallCells[head1] \
    and [h,w] in wallCells[head]:
        alignSensor = ''.join(["CF000","CS000"])
        return alignSensor
        
    # check front condition
    if [h,w] in wallCells[head1] \
    or ( is_valid_point((h+frontCells[0][0][0],w+frontCells[0][0][1])) and mymap[h+frontCells[0][0][0]][w+frontCells[0][0][1]] == mymap[h+frontCells[2][0][0]][w+frontCells[2][0][1]] == mymap[h+frontCells[1][0][0]][w+frontCells[1][0][1]] == CellType.OBSTACLE) :
       return "CF000"

    elif ( is_valid_point((h+frontCells[0][0][0],w+frontCells[0][0][1])) and mymap[h+frontCells[0][0][0]][w+frontCells[0][0][1]] == mymap[h+frontCells[2][0][0]][w+frontCells[2][0][1]] == CellType.OBSTACLE) :
       return "CF090"

    elif ( is_valid_point((h+frontCells[0][0][0],w+frontCells[0][0][1])) and mymap[h+frontCells[0][0][0]][w+frontCells[0][0][1]] == mymap[h+frontCells[1][0][0]][w+frontCells[1][0][1]] == CellType.OBSTACLE) :
       return "CF009"

    elif ( is_valid_point((h+frontCells[0][0][0],w+frontCells[0][0][1])) and mymap[h+frontCells[2][0][0]][w+frontCells[2][0][1]] == mymap[h+frontCells[1][0][0]][w+frontCells[1][0][1]] == CellType.OBSTACLE) :
       return "CF900"

    # check right condition
    if [h,w] in wallCells[head] \
    or( is_valid_point((h+rightCells[0][0][0],w+rightCells[0][0][1])) and mymap[h+rightCells[0][0][0]][w+rightCells[0][0][1]] == mymap[h+rightCells[1][0][0]][w+rightCells[1][0][1]] == CellType.OBSTACLE):
        if [h,w] in wallCells[head] or mymap[h+rightCells[2][0][0]][w+rightCells[2][0][1]] == CellType.OBSTACLE:
            alignSensor = "CS000"
        else:
            alignSensor = "CS090"
        return alignSensor

    elif ( is_valid_point((h+rightCells[0][0][0],w+rightCells[0][0][1])) and mymap[h+rightCells[0][0][0]][w+rightCells[0][0][1]] == mymap[h+rightCells[2][0][0]][w+rightCells[2][0][1]] == CellType.OBSTACLE):
        alignSensor = "RCF009L"
        return alignSensor

    elif ( is_valid_point((h+rightCells[0][0][0],w+rightCells[0][0][1])) and mymap[h+rightCells[2][0][0]][w+rightCells[2][0][1]] == mymap[h+rightCells[1][0][0]][w+rightCells[1][0][1]] == CellType.OBSTACLE):
        alignSensor = "RCF900L"
        return alignSensor
            
    if len(alignSensor) == 0:
        # check left wall, do possible calibration
        index = 0
        count = 0
        for leftCell in leftAllCells[head]:
            if index == 0 or index == 3 or index ==6:
                if is_valid_point([leftCell[0]+h,leftCell[1]+w]) and mymap[leftCell[0]+h][leftCell[1]+w] == CellType.OBSTACLE:
                    count += 1
            index += 1
        if count >= 3: # 3 block on left for calibration
            alignSensor = ''.join(["LCF000","R"])
            return alignSensor

    return alignSensor

def is_valid_point(point):
    x = point[0]
    y = point[1]
    return (x >= 0 and x <20 and y >= 0 and y < 15)
            

if __name__ == "__main__":
    #map = readInput()
    map = utils.createMapTest() # map is a Map object
    instruction = getInstructions(map, (5,6))
    print(instruction)