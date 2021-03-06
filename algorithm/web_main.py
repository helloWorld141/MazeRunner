from arena import Arena, CellType
from flask import Flask, session, request, flash, jsonify, url_for, redirect, render_template, g, stream_with_context
from flask_sqlalchemy import SQLAlchemy
from werkzeug.datastructures import Headers
from werkzeug.wrappers import Response
import json
from race import getInstructions
from simulation_server import SimulatorServer
from tcp_client import TcpClient
from threading import Thread
from enum import Enum
from exploration import Explorer
app = Flask(__name__)
app.config["SECRET_KEY"] = "nHDG3Zi4HVtyc1fPBcrUEi0oACzUPRkI"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
global explore_algo
global fp_instructions
global sim_server
explore_algo = Explorer(None, [0, 0, 0])
sim_server = SimulatorServer(
    "127.0.0.1", 77, None, [0, 0, 0], 0, 0)
fp_instructions = None


class Mode(Enum):
    NONE = 0
    SIM_SERVER = 1
    PI_CONNECTED = 2
    PI_CONNECTING = 3
    EXPLORE_RUNNING = 4


class MdfStrings(db.Model):
    part1 = db.Column(db.String(100))
    part2 = db.Column(db.String(100), primary_key=True)

    def __init__(self, part1, part2):
        self.part1 = part1
        self.part2 = part2

    def __repr__(self):
        return '<OrgUnit %r>' % self.part1 + " | " + self.part2


mode = Mode.NONE


@app.route('/', methods=['GET'])
def index():
    return render_template('main.html', mdf_strings=MdfStrings.query.all())


@app.route('/save_arena', methods=['POST'])
def save_arena():
    new_mdf = MdfStrings(request.form['part1'], request.form['part2'])
    db.session.add(new_mdf)
    db.session.commit()
    return "Saved."


@app.route('/delete_arena', methods=['POST'])
def delete_arena():
    new_mdf = MdfStrings(request.form['part1'], request.form['part2'])
    MdfStrings.query.filter_by(
        part1=new_mdf.part1, part2=new_mdf.part2).delete()
    db.session.commit()
    return "Deleted."


@app.route('/array_to_mdf', methods=['POST'])
def array_to_mdf():
    arena_2d = json.loads(request.data)
    arena_obj = array_to_arena(arena_2d)
    return json.dumps({"part1": arena_obj.to_mdf_part1(), "part2": arena_obj.to_mdf_part2()})


@app.route('/mdf_to_array', methods=['POST'])
def mdf_to_array():
    part1 = request.form['part1']
    part2 = request.form['part2']

    arena_obj = Arena()
    arena_obj.from_mdf_strings(part1, part2)
    arena_2d = arena_to_array(arena_obj)

    return json.dumps(arena_2d)


@app.route('/fastest_path_sim', methods=['POST'])
def fastest_path():
    data = json.loads(request.data)
    arena_2d = data[0]
    try:
        waypoint = (int(data[1]), int(data[2]))
    except ValueError:
        return json.dumps({"Bad input": "please enter numerical values"})
    instructions = getInstructions(array_to_arena(arena_2d), waypoint)
    return json.dumps({"instructions": instructions})


@app.route('/exploration_sim', methods=['POST'])
def exploration_sim():
    data = json.loads(request.data)
    arena_2d = data[0]
    robot_pos = [int(data[1]), int(data[2]), int(data[3])]
    speed = float(data[4])
    error_rate = int(data[7])
    global explore_time_limit
    explore_time_limit = int(data[5])
    global explore_coverage
    explore_coverage = int(data[6])
    arena_obj = array_to_arena(arena_2d)
    sim_server_thread = Thread(target=start_simulation_server,
                               args=[arena_obj, robot_pos, speed, error_rate])
    sim_server_thread.start()
    tcp_client_thread = Thread(
        target=connect_tcp_client, args=["127.0.0.1", 77])
    tcp_client_thread.start()
    global mode
    mode = Mode.SIM_SERVER
    return "Simulation server started."


@app.route('/exploration_start', methods=['GET'])
def exploration_start():
    global tcp_conn
    global explore_algo
    global mode
    explore_algo = Explorer(tcp_conn, [1, 1, 0])
    mode = Mode.EXPLORE_RUNNING
    explore_thread = Thread(target=start_exploration_algo)
    explore_thread.start()
    return "Exploration started."


@app.route('/fastestpath_start', methods=['GET'])
def fastestpath_start():
    global explore_algo
    global fp_instructions
    fp_arena = explore_algo.get_arena()
    tcp_conn.send_command(getInstructions(fp_arena, [1, 1]))
    fp_instructions = getInstructions(fp_arena, [1, 1])
    return "Fastest path started."


@app.route('/connect_to_pi', methods=['GET'])
def connect_to_pi():
    tcp_client_thread = Thread(
        target=connect_tcp_client, args=["192.168.7.1", 77])
    # target=connect_tcp_client, args=["127.0.0.1", 77])
    tcp_client_thread.start()
    global mode
    mode = Mode.PI_CONNECTING
    return "OK"


@app.route('/disconnect_tcp', methods=['GET'])
def disconnect_from_pi():
    global tcp_conn
    tcp_conn.close_conn()
    global mode
    mode = Mode.NONE
    return "OK"


@app.route('/current_mode', methods=['GET'])
def current_mode():
    global mode
    return str(mode.value)


@app.route('/get_explore_status', methods=['GET'])
def get_explore_status():
    global mode
    global explore_algo
    global sim_server
    if mode == Mode.NONE:
        print("Exploration not running.")
        return "N"
    elif mode == Mode.SIM_SERVER:
        if sim_server.get_robot() == None:
            print("Exploration not running.")
            return "N"
    elif mode == Mode.EXPLORE_RUNNING:
        if explore_algo.get_robot() == None:
            print("Exploration not running.")
            return "N"
    arena_2d = arena_to_array(explore_algo.get_arena())
    if mode == Mode.SIM_SERVER:
        result = [arena_2d, explore_algo.get_inner_map(), sim_server.get_robot(
        ), explore_algo.current_status()]
    elif mode == Mode.EXPLORE_RUNNING:
        result = [arena_2d, explore_algo.get_inner_map(), explore_algo.get_robot(),
                  explore_algo.current_status()]
    return json.dumps(result)


@app.route('/get_fastest_path_status', methods=['GET'])
def get_fastest_path_status():
    global fp_instructions
    if fp_instructions == None:
        return "N"
    json_inst = json.dumps({"instructions": fp_instructions})
    fp_instructions = None
    return json_inst


@app.route('/get_original_arena', methods=['GET'])
def get_original_arena():
    return json.dumps(arena_to_array(sim_server.get_arena()))


def arena_to_array(arena):
    arena_2d = [[-1 for y in range(15)] for x in range(20)]
    for x in range(20):
        for y in range(15):
            arena_2d[19-x][y] = arena.get(x, y).value
    return arena_2d


def array_to_arena(arena_2d):
    arena_obj = Arena()
    for x in range(20):
        for y in range(15):
            arena_obj.set(19-x, y, CellType(arena_2d[x][y]))
    return arena_obj


def start_simulation_server(arena_obj, robot_pos, speed, error_rate):
    global mode
    global sim_server
    sim_server = SimulatorServer(
        "127.0.0.1", 77, arena_obj, robot_pos, speed, error_rate)
    sim_server.run()
    mode = Mode.NONE


def start_exploration_algo():
    global explore_algo
    explore_algo.run()


def connect_tcp_client(ip, port):
    global tcp_conn
    global mode
    tcp_conn = TcpClient(ip, port)
    try:
        tcp_conn.run()
        if mode == Mode.PI_CONNECTING:
            mode = Mode.PI_CONNECTED
        while True:
            data = tcp_conn.get_json()
            if data is None:
                break
            handle_request(data)
    except:
        mode = Mode.NONE
    mode = Mode.NONE


def handle_request(data):
    global tcp_conn
    global explore_algo
    global mode
    global explore_time_limit
    global explore_coverage
    global fp_instructions

    request = json.loads(data)
    if request["command"] == "beginExplore":

        if mode == Mode.SIM_SERVER:
            explore_algo = Explorer(
                tcp_conn, request["robotPos"], tThresh=explore_time_limit, pArea=(explore_coverage/100))

        elif mode == Mode.PI_CONNECTED:
            explore_algo = Explorer(tcp_conn, request["robotPos"])
            mode = Mode.EXPLORE_RUNNING

        explore_thread = Thread(target=start_exploration_algo)
        explore_thread.start()

    elif request["command"] == "beginFastest":
        fp_arena = explore_algo.get_arena()
        tcp_conn.send_command(getInstructions(fp_arena,  request["wayPoint"]))
        fp_instructions = getInstructions(fp_arena,  request["wayPoint"])

    elif request["command"] == "autoStart":
        explore_algo.set_update(True)
    elif request["command"] == "autoStop":
        explore_algo.set_update(False)
    elif request["command"] == "sendArena":
        tcp_conn.send_arena(explore_algo.get_arena)
        tcp_conn.send_arena(explore_algo.get_robot)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
