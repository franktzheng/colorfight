def attack_score(cell, game):
    if cell.owner == game.uid:
        prox_enemy = len(
            filter(lambda c: c.owner != 0 and c.owner != game.uid, surrounding)
        )
        if prox_enemy > 0:
            return 10000
        return -10000

    surrounding = cell.position.get_surrounding_cardinals()
    turn = game.turn

    prox_self = len(filter(lambda c: c.owner == game.uid, surrounding))
    nat_gold = cell.natural_gold
    nat_energy = cell.natural_energy
    enemy_ownership = int(cell.owner != game.uid and cell.owner != 0)
    att_cost = cell.attack_cost
    
    ps = turn / (500 * 3)
    eo = (500 - turn) / 500
    ng = turn / (500 * 10)
    ne = turn / (500 * 10)
    ac = 1 / 400

    value = (nat_gold * ng + nat_energy * ne) / (att_cost * ac)

    return ps * prox_self + enemy_ownership * eo + value