import random
import typing
import copy
from collections import deque

# === INFO ===
def info() -> typing.Dict:
    return {
        "apiversion": "1",
        "author": "Püppchens_Unsterbliche_Schlange",
        "color": "#FF00FF",      # grelles Magenta
        "head": "mystery",       # merkwürdiger Kopf
        "tail": "coffee"         # merkwürdiger Schwanz
    }

# === GAME START / END ===
def start(game_state: typing.Dict):
    print("LET THE CHAOS BEGIN")

def end(game_state: typing.Dict):
    print("THE LAST SNAKE STANDS")

# ---------------- Utillities ----------------

# Globale Bewegungs-Map
delta = {"up": (0,1), "down": (0,-1), "left": (-1,0), "right": (1,0)}

def simulate_state(state, moves):
    # Wie gehabt: deepcopy + Kopf vor, Schwanz weg
    new = copy.deepcopy(state)
    # Bewege alle Schlangen
    for s in new['board']['snakes']:
        dx, dy = delta[moves[s['id']]]
        head = s['body'][0]
        s['body'].insert(0, {"x": head['x']+dx, "y": head['y']+dy})
    # Fressen vs. schwänze kürzen
    food = {(f['x'],f['y']) for f in new['board']['food']}
    for s in new['board']['snakes']:
        pos = (s['body'][0]['x'], s['body'][0]['y'])
        if pos in food:
            new['board']['food'] = [f for f in new['board']['food'] if (f['x'],f['y'])!=pos]
        else:
            s['body'].pop()
    return new

def flood_fill(head, occupied, w, h, limit=121):
    from collections import deque
    q = deque([head])
    seen = {head}
    area = 0
    while q and area<limit:
        x,y = q.popleft()
        area += 1
        for dx,dy in delta.values():
            nx,ny = x+dx, y+dy
            if 0<=nx<w and 0<=ny<h and (nx,ny) not in occupied and (nx,ny) not in seen:
                seen.add((nx,ny)); q.append((nx,ny))
    return area

# Paranoid-Max-N-Search für 4-Schlangen-Free-For-All
def paranoid_search(state, you_id, depth, alpha, beta):
    board = state['board']
    w,h = board['width'], board['height']
    you = next(s for s in board['snakes'] if s['id']==you_id)
    occupied = {(seg['x'],seg['y']) for s in board['snakes'] for seg in s['body']}
    # Basis: depth 0 → schätze deine Freifläche
    if depth==0:
        return flood_fill((you['body'][0]['x'],you['body'][0]['y']), occupied, w, h)
    # Maximizer (du)
    best = -float('inf')
    for move_you in delta:
        # Safety-Check
        x,y = you['body'][0]['x']+delta[move_you][0], you['body'][0]['y']+delta[move_you][1]
        if (x,y) in occupied or not (0<=x<w and 0<=y<h): continue
        # Gegner (paranoid: alle gegen dich) wählen worst-case
        worst = float('inf')
        # Simuliere alle kombinierten Züge der drei anderen (4^3 ≈ 64)
        others = [s for s in board['snakes'] if s['id']!=you_id]
        for m1 in delta:
            for m2 in delta:
                for m3 in delta:
                    moves = {you_id: move_you,
                             others[0]['id']: m1,
                             others[1]['id']: m2,
                             others[2]['id']: m3}
                    nxt = simulate_state(state, moves)
                    val = paranoid_search(nxt, you_id, depth-1, alpha, beta)
                    worst = min(worst, val)
                    # Beta-Cut
                    if worst <= alpha:
                        break
                if worst <= alpha: break
            if worst <= alpha: break
        best = max(best, worst)
        alpha = max(alpha, best)
        if best >= beta:
            break
    return best

# === MOVE-LOGIK ===
def move(game_state: typing.Dict) -> typing.Dict:
    you_id = game_state['you']['id']
    # Free-Fall Höhepunkt: 3-Ply deep
    best_move, best_val = None, -float('inf')
    alpha, beta = -float('inf'), float('inf')
    for m in delta:
        val = paranoid_search(game_state, you_id, depth=3, alpha=alpha, beta=beta)
        if val > best_val:
            best_val, best_move = val, m
            alpha = max(alpha, val)
    if not best_move:
        best_move = random.choice(list(delta))
    return {"move": best_move}

# === SERVER-START ===
if __name__=="__main__":
    from server import run_server
    run_server({"info":info, "start":start, "move":move, "end":end})
