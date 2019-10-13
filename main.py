from colorfight import Colorfight
import time
import random
from colorfight.constants import BLD_GOLD_MINE, BLD_ENERGY_WELL, BLD_FORTRESS, BUILDING_COST, HOME_COST, BLD_HOME, BUILDING_UPGRADE_COST, HOME_UPGRADE_COST

def play_game(
        game, \
        room     = 'public', \
        username = 'default', \
        password = str(int(time.time()))):
    game.connect(room = room)
    
    if game.register(username = username, \
            password = password):
        # This is the game loop
        while True:
            cmd_list = []
            attack_list = []
            if not game.update_turn():
                break
    
            if game.me == None:
                continue
    
            start_time = time.time()
            me = game.me
            turn = game.turn

            tax_amount = me.tax_amount

            gold = me.gold - tax_amount
            
            attack_energy = me.energy
            if turn < 100:
                gold_willing = gold
            elif turn < 200:
                gold_willing = gold * 0.9
            elif turn < 300:
                gold_willing = gold * 0.6
            elif turn < 400:
                gold_willing = gold * 0.4
            else:
                gold_willing = 0
            
            if turn < 450:
                # Ranking cells by resource value
                building_scores = list(filter(lambda c: c[1] is not None, list(map(lambda c: (c, building_score_and_cmd(c, game)), game.me.cells.values()))))
                building_scores.sort(key=lambda t: t[1][0], reverse=True)
                
                for c, (_, cmds, cost) in building_scores:
                    gcost, ecost = cost
                    if gold_willing > gcost and attack_energy > ecost:
                        if not c.is_empty:
                            pass
                            # print('upgrading!')
                        cmd_list += cmds
                        gold_willing -= gcost
                        attack_energy -= ecost
            
            cells_to_attack = []
            for cell in game.me.cells.values():
                # Check the surrounding position
                score = attack_score(cell, game)
                cells_to_attack.append((cell, score))
                for pos in cell.position.get_surrounding_cardinals():                    
                    c = game.game_map[pos]
                    if c.owner != me.uid and pos not in attack_list:
                        score = attack_score(c, game)
                        cells_to_attack.append((c, score))

            cells_to_attack.sort(key=lambda t: t[1], reverse=True)
            attack_count = 0
            # Attacks cells until we run out of energy
            for c, _ in cells_to_attack:
                if attack_energy > c.attack_cost and c.position not in attack_list:
                    if c.owner == me.uid:
                        r = random.uniform(0, 1)
                        if r > 0.9:
                            cmd_list.append(game.build(c.position, BLD_FORTRESS))
                        else:
                            cmd_list.append(game.attack(c.position, 1))
                            attack_energy -= 1
                            print('defending position', c.position)
                    else:
                        attack_count += 1
                        cmd_list.append(game.attack(c.position, c.attack_cost))
                        attack_energy -= c.attack_cost
                    attack_list.append(c.position)

            print(f"we took {time.time() - start_time} seconds")
                    
            # Send the command list to the server
            result = game.send_cmd(cmd_list)
            print("Turn {}, {}, cmds: {}, energy: {}, gold: {}".format(turn, result, cmd_list, me.energy, me.gold))                
            print("ATTACK ", attack_count)

    # Do this to release all the allocated resources. 
    game.disconnect()
    
def attack_score(cell, game):
    filter_self = lambda pos: game.game_map[pos].owner == game.uid

    surrounding = cell.position.get_surrounding_cardinals()
    turn = game.turn

    if cell.owner == game.uid:
        prox_enemy = len(list(filter(filter_enemy, surrounding)))
        if prox_enemy > 0:
            return 10000
        return -10000

    prox_self = len(list(filter(filter_self, surrounding)))
    nat_gold = cell.natural_gold
    nat_energy = cell.natural_energy
    enemy_ownership = int(cell.owner != game.uid and cell.owner != 0)
    att_cost = cell.attack_cost
    
    ps = turn / (500 * 3)
    eo = 0.1 * ((500 - turn) / 500)
    ng = turn / (500 * 10)
    ne = turn / (500 * 10)
    ac = 1 / 400

    value = (nat_gold * ng + nat_energy * ne) / (att_cost * ac)
    score = ps * prox_self + eo * enemy_ownership + value
    # print(nat_gold * ng + nat_energy * ne)
    return score

def filter_enemy(pos):
    c = game.game_map[pos]
    return c.owner != 0 and c.owner != game.uid

def get_home(game):
    home_filter = list(filter(lambda c: c.building.is_home, game.me.cells.values()))
    return home_filter[0] if home_filter else None

def building_score_and_cmd(cell, game):
    home = get_home(game)
    if home is None:
        return (100000000000000, [game.upgrade(random.choice(list(game.me.cells.values())))], (1000, 0))

    level = 0 if cell.is_empty else cell.building.level
    if level == 3:
        return None
    cost = ({ 0: 200, 1: 400, 2: 600 }[level], 0)
    turn = game.turn
    
    nat_gold = cell.natural_gold
    nat_energy = cell.natural_energy
    
    gold_eff = (turn / 1000 + 0.6) * 20 * nat_gold / cost[0]
    energy_eff = (1 - turn / 750) * 20 * nat_energy / cost[0]
    prox = 1 / 4 * len(list(filter(filter_enemy, cell.position.get_surrounding_cardinals())))

    if level == 0:
        building = BLD_GOLD_MINE if gold_eff > energy_eff else BLD_ENERGY_WELL
        cmd = [game.build(cell.position, building)]
    else:
        home = get_home(game)
        if home is not None and home.building.level == level:
            cmd = [game.upgrade(home.position), game.upgrade(cell.position)]
            home_cost = { 1: 1000, 2: 2000, 3: 0 }[home.building.level]
            cost = (cost[0] + home_cost, home_cost)
        else:
            cmd = [game.upgrade(cell.position)]
    
    return (gold_eff + energy_eff + prox, cmd, cost)

if __name__ == '__main__':
    game = Colorfight()

    room = 'official_final'
    play_game(
        game     = game, \
        room     = room, \
        username = 'GROUP108', \
        password = str(int(time.time()))
    )

        
    # ======================================================================

    # ========================= Run my bot forever =========================
    #while True:
    #    try:
    #        play_game(
    #            game     = game, \
    #            room     = room, \
    #            username = 'ExampleAI' + str(random.randint(1, 100)), \
    #            password = str(int(time.time()))
    #        )
    #    except Exception as e:
    #        print(e)
    #        time.sleep(2)