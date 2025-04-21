import threading
from socket import *
import os
import json

SERVER_PORT = 10001
DATA_FILE = "tournament_data.json"

lock = threading.Lock()

def load_data():
    if not os.path.exists(DATA_FILE):
        # Example initial data
        data = {
            "teams": {
                "Alpha": {"games": [], "scores": [], "average": 0.0},
                "Beta": {"games": [], "scores": [], "average": 0.0},
                "Gamma": {"games": [], "scores": [], "average": 0.0},
                "Delta": {"games": [], "scores": [], "average": 0.0}
            },
            "games": [
                {"id": 1, "teams": ["Alpha", "Beta"], "score": None},
                {"id": 2, "teams": ["Gamma", "Delta"], "score": None},
                {"id": 3, "teams": ["Alpha", "Gamma"], "score": None},
                {"id": 4, "teams": ["Beta", "Delta"], "score": None}
            ]
        }
        for game in data["games"]:
            for team in game["teams"]:
                data["teams"][team]["games"].append(game["id"])
        save_data(data)
    else:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
    return data

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def recalc_averages(data):
    for team, info in data["teams"].items():
        if info["scores"]:
            info["average"] = sum(info["scores"]) / len(info["scores"])
        else:
            info["average"] = 0.0

def get_rankings(data):
    teams = list(data["teams"].items())
    teams.sort(key=lambda x: x[1]["average"], reverse=True)
    return [(i+1, t[0], t[1]["average"]) for i, t in enumerate(teams)]

def handle_client(conn):
    try:
        while True:
            msg = conn.recv(1024).decode("utf-8")
            if not msg:
                break
            parts = msg.strip().split("|")
            cmd = parts[0].upper()
            with lock:
                data = load_data()
                if cmd == "GET_SCHEDULE":
                    if len(parts) != 2:
                        conn.send(b"400|Usage: GET_SCHEDULE|team_name\n")
                        continue
                    team = parts[1]
                    if team not in data["teams"]:
                        conn.send(f"400|Team '{team}' not found\n".encode())
                        continue
                    schedule = []
                    for gid in data["teams"][team]["games"]:
                        game = next(g for g in data["games"] if g["id"] == gid)
                        score = game["score"] if game["score"] is not None else "Pending"
                        schedule.append(f"Game {gid}: vs {', '.join(game['teams'])} | Score: {score}")
                    msg = f"200|Schedule for {team}:\n" + "\n".join(schedule) + "\n"
                    conn.send(msg.encode())
                elif cmd == "GET_RANK":
                    if len(parts) != 2:
                        conn.send(b"400|Usage: GET_RANK|team_name\n")
                        continue
                    team = parts[1]
                    rankings = get_rankings(data)
                    found = False
                    for rank, t, avg in rankings:
                        if t == team:
                            conn.send(f"200|{team} is ranked #{rank} with average score {avg:.2f}\n".encode())
                            found = True
                            break
                    if not found:
                        conn.send(f"400|Team '{team}' not found\n".encode())
                elif cmd == "GET_RANKINGS":
                    rankings = get_rankings(data)
                    msg = "200|Team Rankings:\n"
                    for rank, t, avg in rankings:
                        msg += f"{rank}. {t} - {avg:.2f}\n"
                    conn.send(msg.encode())
                elif cmd == "SUBMIT_SCORE":
                    if len(parts) != 3:
                        conn.send(b"400|Usage: SUBMIT_SCORE|game_id|score\n")
                        continue
                    try:
                        gid = int(parts[1])
                        score = float(parts[2])
                    except:
                        conn.send(b"400|Invalid game_id or score\n")
                        continue
                    game = next((g for g in data["games"] if g["id"] == gid), None)
                    if not game:
                        conn.send(b"400|Game not found\n")
                        continue
                    if game["score"] is not None:
                        conn.send(b"400|Score already submitted for this game\n")
                        continue
                    game["score"] = score
                    for team in game["teams"]:
                        data["teams"][team]["scores"].append(score)
                    recalc_averages(data)
                    save_data(data)
                    conn.send(b"200|Score submitted and rankings updated\n")
                elif cmd == "HELP":
                    helpmsg = (
                        "200|Commands:\n"
                        "GET_SCHEDULE|team_name\n"
                        "GET_RANK|team_name\n"
                        "GET_RANKINGS\n"
                        "SUBMIT_SCORE|game_id|score\n"
                        "HELP\n"
                        "EXIT\n"
                    )
                    conn.send(helpmsg.encode())
                elif cmd == "EXIT":
                    conn.send(b"200|Goodbye!\n")
                    break
                else:
                    conn.send(b"400|Unknown command. Type HELP for options.\n")
    except Exception as e:
        conn.send(f"500|Server Error: {e}\n".encode())
    finally:
        conn.close()

def main():
    serverSocket = socket(AF_INET, SOCK_STREAM)
    serverSocket.bind(("", SERVER_PORT))
    serverSocket.listen(5)
    print(f"Server ready on port {SERVER_PORT}")
    while True:
        conn, addr = serverSocket.accept()
        threading.Thread(target=handle_client, args=(conn,), daemon=True).start()

if __name__ == "__main__":
    main()