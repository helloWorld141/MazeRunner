from arena import Arena,CellType
from Robot import Robot
from random import randint
import time, socket, logging, sys
import race
from race import dijkstra
from tcp_client import TcpClient
import json

class Explorer():
    def __init__(self, tcp_conn, robot_pos, buffer_size=1024,tBack=20,tThresh=260,pArea=0.9,alignLimit = 3):
        logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
        self.tcp_conn = tcp_conn
        self.auto_update = False
        self.status = ""
        self.arena = Arena()
        #self.robot = [1, 1, 0] # 2d position plus orientation
        ### CONSTANT ####
        self.MAX_SHORT_SENSOR = 3
        self.MAX_LONG_SENSOR = 6
        ##### exploration logics related variables ####
        self.exploredArea = 0
        self.cnt = 0 # no. of instruction executed
        self.goBackTime = tBack # seconds for it to go back Start from any position
        self.timeThreshold = tThresh # user-input time to terminate exploration
        self.timeLimit = 360
        self.areaPercentage = pArea # percentage we want the robot to explore up to
        self.reachGoal = False
        self.startTime = time.time()
        self.alignCnt = 0 # counter for robot alignment
        self.alignLimit = alignLimit
        self.alignNow = False
        self.reReadSensor = False
        self.readingConflict = False
        self.conflictCells = []
        self.alignSensor = "" # CF(front), CS(right)
        self.robot = Robot(
            'exploring', robot_pos[2]/90, robot_pos[0], robot_pos[1])
        self.checkingRight = False

        self.frontCells = {0:[[[2,-1],[3,-1],[4,-1]],[[2,0],[3,0],[4,0]],[[2,1],[3,1],[4,1]]],
                    1:[[[1,2],[1,3],[1,4]],[[0,2],[0,3],[0,4]],[[-1,2],[-1,3],[-1,4]]],
                    2:[[[-2,1],[-3,1],[-4,1]],[[-2,0],[-3,0],[-4,0]],[[-2,-1],[-3,-1],[-4,-1]]],
                    3:[[[-1,-2],[-1,-3],[-1,-4]],[[0,-2],[0,-3],[0,-4]],[[1,-2],[1,-3],[1,-4]]]
            }
        # only keep top right and bottom right lines
        self.rightCells = {0:[[[1,2],[1,3],[1,4]],[[-1,2],[-1,3],[-1,4]]],
                    1:[[[-2,1],[-3,1],[-4,1]],[[-2,-1],[-3,-1],[-4,-1]]],
                    2:[[[-1,-2],[-1,-3],[-1,-4]],[[1,-2],[1,-3],[1,-4]]],
                    3:[[[2,-1],[3,-1],[4,-1]],[[2,1],[3,1],[4,1]]]
            }
        # only keep top left lines, detect up to the 6 cells in front
        self.leftCells = {0:[[1,-2],[1,-3],[1,-4],[1,-5],[1,-6],[1,-7]],
                    1:[[2,1],[3,1],[4,1],[5,1],[6,1],[7,1]],
                    2:[[-1,2],[-1,3],[-1,4],[-1,5],[-1,6],[-1,7]],
                    3:[[-2,-1],[-3,-1],[-4,-1],[-5,-1],[-6,-1],[-7,-1]]
                }
        # positions in wallCells are for calibration
        self.wallCells = {0:[[],[]],
                    1:[[],[]],
                    2:[[],[]],
                    3:[[],[]]
                }
        for i in range(1,19):
            self.wallCells[0][0].append([i,13])
            self.wallCells[2][0].append([i,1])
            if 2 <= i <= 17:
                self.wallCells[0][1].append([i,12])
                self.wallCells[2][1].append([i,2]) 
                if 2 <= i <= 12:
                    self.wallCells[1][1].append([2,i])
                    self.wallCells[3][1].append([17,i])
            if 1 <= i <= 13:
                self.wallCells[1][0].append([1,i])
                self.wallCells[3][0].append([18,i])
        

    def run(self):
        cnt = 0
        self.tcp_conn.send_command("ES")
        self.update_status("Start exploration")
        while self.robot.robotMode != "done": 
            cnt += 1 
            sensors = self.tcp_conn.get_string()           
            self.updateMap(sensors)
            
# =============================================================================
#             print("conflict cells:",self.conflictCells)
#             
#             # conflict solving
#             if self.reReadSensor == True:
#                 self.tcp_conn.send_command("N")
# =============================================================================
                
# =============================================================================
#             else:    
#                 #update map with sensor values
#                 self.updateMap(sensors)
#                 # sensor conflict solving if conflictCells contains cells
#                 if len(self.conflictCells) != 0:
#                     self.readingConflict = True
#                     self.tcp_conn.send_command("N")
#                 else:
#                     self.readingConflict = False
# =============================================================================
                
            explorationTime = time.time() - self.startTime
            #check reachgoal
            if self.robot.robotCenterH == 18 and self.robot.robotCenterW == 13:
                self.reachGoal = True
            # if reach time limit
            if self.timeThreshold < explorationTime or self.exploredArea >= 300*self.areaPercentage:
                if self.robot.isInStartZone():
                    self.robot.robotMode = "done"
                    break
                else:
                    # find the way back to start zone using djikstra
                    startnode = (self.robot.robotCenterH, self.robot.robotCenterW, int(self.robot.robotHead))
                    endnode = (1,1,0)
                    (instructions, endOrientation,cost) = dijkstra(self.arena.get_2d_arr(), startnode, endnode, endOrientationImportant=False)
                    # give instruction
                    self.cnt += len(instructions)
                    self.tcp_conn.send_command(instructions)
                    # update robot states (position and orientation)
                    self.robot.jump(endnode)
                    continue
            else:
                if self.reachGoal:
                       # shall we delete this first condition now?
                    if explorationTime > self.timeThreshold and \
                        not self.robot.isAlmostBack() and \
                        self.robot.robotMode != 'reExplore':
                        # find way back to start zone using fastest path algo (djikstra)
                        startnode = (self.robot.robotCenterH, self.robot.robotCenterW, int(self.robot.robotHead))
                        endnode = (1,1,0)
                        (instructions, endOrientation,cost) = dijkstra(self.arena.get_2d_arr(), startnode, endnode, endOrientationImportant=False)
                        # give instruction
                        self.cnt += len(instructions)
                        self.tcp_conn.send_command(instructions)
                        # update robot states (position and orientation)
                        self.robot.jump(endnode) # already update sensors inside
                        continue
                    if self.robot.isAlmostBack() and self.exploredArea < 300*self.areaPercentage:
                        self.robot.robotMode = 'reExplore'
                    if self.robot.robotMode == 'reExplore':
                        # reexplore, find the fastest path to the nearest unexplored cell
                        (instructions, endnode) = self.reExplore()
                        # give instruction
                        self.cnt += len(instructions)
                        self.tcp_conn.send_command(instructions)
                        # update robot states
                        self.robot.jump(endnode) # already update sensors inside

                        print("comeplete a re-reploration")
                        continue

                #if havent reach any of above continue statements, just wall hugging
                instruction = self.wallHugging()
                # there's no need to update robot state because it is already done in wallHugging()
                # give instruction 
                self.tcp_conn.send_command(instruction)
                print("robot center:",self.robot.robotCenterH,self.robot.robotCenterW)
                print("robot head:",self.robot.robotHead)
                if self.reachGoal == False:
                    self.reachGoal = self.robot.isInGoal()           
        print("Exploration time:",explorationTime)
        print("Instruction count:", self.cnt)
        self.update_status("End exploration")
        self.tcp_conn.send_command(json.dumps({"event": "endExplore"}))
        self.tcp_conn.send_command("EE")

    def is_valid_point(self, point):
        x = point[0]
        y = point[1]
        return (x >= 0 and x <20 and y >= 0 and y < 15)

    def get_arena(self):
        return self.arena

    def get_robot(self):
        if self.robot.robotMode == "done":
            return None
        return self.robot.getPosition()            

    def update_status(self, status):
        self.status = status
        self.tcp_conn.send_status(status)
        if self.auto_update:
            self.tcp_conn.send_robot_pos(self.robot.getPosition())
            self.tcp_conn.send_arena(self.arena)

    def current_status(self):
        return self.status

    def set_update(self, auto):
        self.auto_update = auto

    ##### exploration logics #####

    def updateExploredArea(self):   
        count = 0
        for row in self.arena.get_2d_arr():
            for cell in row:
                if (cell != CellType.UNKNOWN):
                    count += 1
        self.exploredArea = count
    # given inputs, find corresponding cell coordinates needed to be marked as enum EMPTY or OBSTACLE
    def markCells(self, sensorIndex, value):
        w = self.robot.robotCenterW
        h = self.robot.robotCenterH
        head = self.robot.robotHead
        realTimeMap = self.arena
        # if withint the map range, then mark. Otherwise discard the reading
        if (0 <= w <= 13 and 0 <= h <= 18):
            # sensorIndex = 0..5 corresponding to F1,F2,F3,R1,R2,L1
            # only the 5th sensor (top left) is long range sensor
            sensor = self.robot.sensors[sensorIndex]
            offsets = self.robot.visible_offsets(sensor)
            if value > sensor.visible_range:
                value = sensor.visible_range
# =============================================================================
#             self.reReadSensor = False
# =============================================================================
            
            if value <= sensor.visible_range:
                for i in range(value):
                    x = h + offsets[i][0]
                    y = w + offsets[i][1]
                    if self.is_valid_point((x,y)):
# =============================================================================
#                         logging.debug("Empty coordinate " + str(x) +" " + str(y))
# =============================================================================
                        realTimeMap.set(x, y, CellType.EMPTY)
                if value < sensor.visible_range:
                    x = h + offsets[value][0]
                    y = w + offsets[value][1]
                    if self.is_valid_point((x,y)):
# =============================================================================
#                         logging.debug("Obstacle coordinate " + str(x) + " " + str(y)) 
# =============================================================================

# for conflict solving
# =============================================================================
#                         if realTimeMap.get(x,y) == CellType.EMPTY \
#                         and [x,y] not in self.conflictCells:
#                             self.reReadSensor = True
#                             self.conflictCells.append([x,y])
#                         else:
#                             realTimeMap.set(x,y,CellType.OBSTACLE)
#                             if [x,y] in self.conflictCells:
#                                 self.conflictCells.remove([x,y])
# =============================================================================
                                
                        realTimeMap.set(x,y,CellType.OBSTACLE)                       
                                
        self.updateExploredArea()
        
    def updateMap(self, sensorValues):
        for i in range(len(sensorValues)):
            self.markCells(i, int(sensorValues[i]))
        self.updateExploredArea()
    # check whether the 3 consecutive cells in front are empty
    def checkAlign(self,r):
        head = int(self.robot.robotHead)
        if head > 0:
            head1 = head- 1
        else:
            head1 = 3

        for i in range(r):
            frontCells = self.frontCells[self.robot.robotHead]
            rightCells = self.rightCells[self.robot.robotHead]
            h = self.robot.robotCenterH
            w = self.robot.robotCenterW
            if [h,w] in self.wallCells[head][i]:
                if i == 0 \
                or self.arena.get(h+rightCells[0][i-1][0],w+rightCells[0][i-1][1]) == CellType.EMPTY \
                and self.arena.get(h+rightCells[1][i-1][0],w+rightCells[1][i-1][1]) == CellType.EMPTY:
                    self.alignSensor = ''.join(["CS",str(i)])
                    self.alignNow = True
                    break
            elif [h,w] in self.wallCells[head1][i]:
                if i == 0:              
                    self.alignSensor = ''.join(["CF",str(i)])
                    self.alignNow = True
                    break
            else:                  
                if i == 0 \
                and self.arena.get(h+frontCells[0][i][0],w+frontCells[0][i][1]) == self.arena.get(h+frontCells[2][i][0],w+frontCells[2][i][1]) == CellType.OBSTACLE :
                    self.alignSensor = ''.join(["CF",str(i)])
                    self.alignNow = True
                    break
                elif self.arena.get(h+rightCells[0][i][0],w+rightCells[0][i][1]) == self.arena.get(h+rightCells[1][i][0],w+rightCells[1][i][1]) == CellType.OBSTACLE :
                    self.alignSensor = ''.join(["CS",str(i)])
                    self.alignNow = True
                    break
                elif i == 0\
                and self.arena.get(h+frontCells[0][i][0],w+frontCells[0][i][1]) == self.arena.get(h+frontCells[1][i][0],w+frontCells[1][i][0]) == CellType.OBSTACLE\
                    or self.arena.get(h+frontCells[1][i][0],w+frontCells[1][i][1]) == self.arena.get(h+frontCells[2][i][0],w+frontCells[2][i][1]) == CellType.OBSTACLE:                
                    self.alignSensor = ''.join(["CF",str(i)])
                    self.alignNow = True  
                    break
                else:
                    continue
        
    def align(self):
        self.alignCnt = 0 # after each align, reset
        self.alignNow = False
        self.alignSensor = ""
            
    def checkFront(self):
        robot = self.robot
        frontCells = robot.frontCells
        for cell in frontCells[robot.robotHead]:
            if (robot.robotCenterW+cell[1] > 14 or robot.robotCenterH+cell[0] > 19 \
                or robot.robotCenterW+cell[1] < 0 or robot.robotCenterH+cell[0] < 0 \
                or self.arena.get(robot.robotCenterH+cell[0],robot.robotCenterW+cell[1]) != CellType.EMPTY): 
                return False
        print("check front true")
        return True                   
    # check whether the 3 consecutive cells on robot right are empty
    def checkRight(self):
        robot = self.robot
        rightCells = robot.rightCells
        for cell in rightCells[robot.robotHead]:
            if (robot.robotCenterW+cell[1] > 14 or robot.robotCenterH+cell[0] > 19 \
                or robot.robotCenterW+cell[1] < 0 or robot.robotCenterH+cell[0] < 0 \
                or self.arena.get(robot.robotCenterH+cell[0],robot.robotCenterW+cell[1]) == CellType.OBSTACLE):
                return "false"
            elif (self.arena.get(robot.robotCenterH+cell[0],robot.robotCenterW+cell[1]) == CellType.UNKNOWN):
                return "unknown"
        return "true"
    def wallHugging(self): # return instruction
        # mark current body cells as empty
        # actually might not need, just put here first
        sensor = "" 
        bodyCells = self.robot.returnBodyCells()
        for cell in bodyCells:
            self.arena.set(cell[0],cell[1],CellType.EMPTY)
        self.alignCnt += 1 # increment alignment counter
        if self.alignCnt == self.alignLimit:
            # if just reach alignLimit, then use block0 to calibrate on only (more accurate)
            self.checkAlign(1)  
        elif self.alignCnt > self.alignLimit:
            # if alr exceed alignLimit and haven't found blocks to calibrate, use block1 to calibrate
            self.checkAlign(2)
        else:
            self.alignNow = False

        if (self.checkingRight == False):
            # decide turn-right condition
            if (self.checkRight() == "true"):                    
                self.robot.rotateRight()
                self.robot.forward()
                self.update_status("Turning right")
                if self.alignNow == True:
                    sensor = self.alignSensor
                    self.align()
                return (''.join([sensor,"RF"]))
            
            elif (self.checkRight() == "unknown"):
                self.robot.rotateRight()
                self.update_status("Checking right")  
                self.checkingRight = True
                if self.alignNow == True:
                    sensor = self.alignSensor
                    self.align()
                return (''.join([sensor,"R"]))
                                  
        # alr enter checkingRight now, so update status as False again
        self.checkingRight = False
        # decide front condition
        if (self.checkFront()):
            self.robot.forward()
            self.update_status("Moving forward")
            if self.alignNow == True:
                sensor = self.alignSensor
                self.align()
            return (''.join([sensor,"F"]))
        else:
            self.robot.rotateLeft()
            self.update_status("Turning left") 
            if self.alignNow == True:
                sensor = self.alignSensor
                self.align()
            return (''.join([sensor,"L"]))
        
    def allEmpty(self,h,w):
        for i in range(h-1,h+2):
            for j in range(w-1,w+2):
                if self.arena.get(i,j) != CellType.EMPTY:
                    return False
        return True
    
    def searchBoundaryCells(self,cells):
        boundaryCells = []
        for cell in cells:
            h = cell[0]
            w = cell[1]
            for side in range(4):
                if side == 0 or side == 2:
                    x = h+(side-1)
                    if self.arena.get(x,w) == CellType.EMPTY:
                        if self.arena.get(x,w-1) == CellType.EMPTY:
                            if self.arena.get(x,w-2) == CellType.EMPTY:
                                boundaryCells.append(cell)
                                break
                        elif self.arena.get(x,w+1) == CellType.EMPTY:
                            if self.arena.get(x,w+2) == CellType.EMPTY:
                                boundaryCells.append(cell)
                                break
                        else:
                            continue                            
                    # if middle cell not empty, break current direction and search next direction
                    else:
                        continue
                else: # side == 1 or 3
                    y = w+(side-2)
                    if self.arena.get(h,y) == CellType.EMPTY:
                        if self.arena.get(h-1,y) == CellType.EMPTY:
                            if self.arena.get(h-2,y) == CellType.EMPTY:
                                boundaryCells.append(cell)
                                break
                        elif self.arena.get(h+1,y) == CellType.EMPTY:
                            if self.arena.get(h+2,y) == CellType.EMPTY:
                                boundaryCells.append(cell)
                                break
                        else:
                            continue                            
                    # if middle cell not empty, break current direction and search next direction
                    else:
                        continue

        return boundaryCells
            
            
        
    def reExplore(self):
            
        # detect all unexplored cells
        reExploreCells = []
        boundaryCellsDist = []
        cellEuclidean = []
        targetCells = []
        robot = self.robot
        noOfPicks = 3
        startnode = (robot.robotCenterH, robot.robotCenterW, int(robot.robotHead)) #change to int(robothead) because somehow the robotHead is a float
     
        for x in range(len(self.arena.arena_map)):
            for y in range(len(self.arena.arena_map[x])):
                if (self.arena.get(x,y) == CellType.UNKNOWN):
                    reExploreCells.append([x,y])
        
        # only move to explore one of the boundary cells - cell that has at least one side has 3 consecutive empty blocks            
        boundaryCells = self.searchBoundaryCells(reExploreCells)
        logging.debug("boundary cells:" + str(boundaryCells))
                    
        # calculate Euclidean distance for each
        for cell in boundaryCells:
            euclideanDist =euclidean([robot.robotCenterH,robot.robotCenterW],cell)
            cellEuclidean.append(euclideanDist)
            boundaryCellsDist.append((cell,euclideanDist))
        
        # sort cellEuclidean distance and remove all duplicates
        cellEuclidean.sort()
        cellEuclidean = list(set(cellEuclidean))
        
        # pick k number of eucliean nearest cell candidates
        itemNo = 0
        noMore = False
        for dist in cellEuclidean:
            for cellTup in boundaryCellsDist:
                if cellTup[1] == dist:
                    if itemNo < noOfPicks:
                        targetCells.append(cellTup[0])
                        itemNo += 1
                if itemNo > noOfPicks:
                    noMore = True
                    break
            if noMore == True:
                break
            
        logging.debug("targetCells" + str(targetCells))
        
        potentialPos = []
        for cell in targetCells:
            # find its nearest observing point
            offsets = [[-2,1],[-2,0],[-2,-1],[-1,-2],[0,-2],[1,-2],[2,-1],[2,0],[2,1],[1,2],[0,2],[-1,2]]
            for offset in offsets:
                if self.allEmpty(cell[0]+offset[0],cell[1]+offset[1]):
                    # potentialPos: [observingCoords,cellToObserveCoords]
                    potentialPos.append([[cell[0]+offset[0],cell[1]+offset[1]],cell,0,0]) #default head is 0, cost = 0            
        # update all potentialPos values with dijkstra cost
        updatedNodes = []          
        for node in potentialPos:
#        for [cellToGo,cellToOb,head,cost] in potentialPos:
            indexOff = 0
            for offset in offsets:
                if [node[0][0]-node[1][0],node[0][1]-node[1][1]] == offset:
                    if 0 <= indexOff < 3:
                        if indexOff == 1:
                            node[2] = [0]
                            break
                        elif indexOff == 2:
                            node[2] = [0,1]
                            break
                        else:
                            node[2] = [0,3]
                            break
                    elif 3 <= indexOff < 6:
                        if indexOff == 4:
                            node[2] = [1]
                            break
                        elif indexOff == 5:
                            node[2] = [1,2]
                            break
                        else:
                            node[2] = [1,0]
                            break
                    elif 6 <= indexOff < 9:
                        if indexOff == 7:
                            node[2] = [2]
                            break
                        elif indexOff == 8:
                            node[2] = [2,3]
                            break
                        else:
                            node[2] = [2,1]
                            break
                    else:
                        if indexOff == 10:
                            node[2] = [3]
                            break
                        elif indexOff == 11:
                            node[2] = [3,0]
                            break
                        else:
                            node[2] = [3,2]
                            break
                else:
                    indexOff += 1
            cellsToMove = []
            costs = []
            # find the path of less cost considring both front ahd right direction for same point
            for direction in node[2]:
                cellsToMove.append((node[0][0],node[0][1],direction))
            for cellToMove in cellsToMove:
                (instr, endNode,cost) = dijkstra(self.arena.get_2d_arr(), startnode, cellToMove, endOrientationImportant=True) 
# =============================================================================
#             print("dijkstra startnode:",startnode)
#             print("dijkstra cellToMove:",cellToMove)
#             print("dijkstra instr:",instr)
#             print("dijkstra cost:",cost)
# =============================================================================
                costs.append(cost)
                minCost = costs[0]
                index = 0
                for cost in costs:
                    if cost < minCost:
                        minCost = cost
                        index += 1
            node[1] = cellsToMove[index] 
            node[2] = node[2][index]                  
            node[3] = minCost
            updatedNodes.append(node)
        logging.debug("potentialPos: " + str(updatedNodes))
        
        # find the minimum cost in potentialPos 
        # this algo can be optimized later
        minCost = 1000
        index = 0
        for choice in updatedNodes:
            if choice[3] < minCost and choice[3] != 0:
                minCost = choice[3]       
        for choice in updatedNodes:
            if choice[3] != minCost:
                index += 1
            else:
                break
        cellToMove = (updatedNodes[index][0][0], updatedNodes[index][0][1], updatedNodes[index][2])
# =============================================================================
#         print("cell to move:",cellToMove)
#         print("start cell:",startnode)
# =============================================================================
        (instr, endNode,cost) = dijkstra(self.arena.get_2d_arr(), startnode, cellToMove, endOrientationImportant=True) 
        logging.debug("Instruction for going to observing cell" + instr)
        logging.debug("Observing point " + str(endNode))       
        return (instr, endNode)

###### helper functions #####    
def findArrayIndexMin(arr):
    return arr.index(min(arr))
            
def euclidean(pos1,pos2):
    return abs(pos1[1]-pos2[1])+abs(pos1[0]-pos2[0])

