from socket import *

SERVER = "localhost"
SERVER_PORT = 10001

def print_menu():
    print("\nRobotic Tournament Team Score Management")
    print("Commands:")
    print("  get_schedule_all")
    print("  get_schedule|team_name")
    print("  get_rank|team_name")
    print("  get_rankings")
    print("  submit_score|game_id|score")
    print("  help")
    print("  exit")

def main():
    clientSocket = socket(AF_INET, SOCK_STREAM)
    clientSocket.connect((SERVER, SERVER_PORT))
    print_menu()
    while True:
        cmd = input("\nEnter command: ").strip()
        if not cmd:
            continue
        clientSocket.send(cmd.encode())
        resp = clientSocket.recv(4096).decode()
        if resp.startswith("200|"):
            print(resp[4:].strip())
        elif resp.startswith("400|"):
            print("Error:", resp[4:].strip())
        elif resp.startswith("500|"):
            print("Server Error:", resp[4:].strip())
        if cmd.strip().upper() == "EXIT":
            break
    clientSocket.close()

if __name__ == "__main__":
    main()