"""
Welcome to your first Halite-II bot!

This bot's name is Settler. It's purpose is simple (don't expect it to win complex games :) ):
1. Initialize game
2. If a ship is not docked and there are unowned planets
2.a. Try to Dock in the planet if close enough
2.b If not, go towards the planet

Note: Please do not place print statements here as they are used to communicate with the Halite engine. If you need
to log anything use the logging module.
"""
# Let's start by importing the Halite Starter Kit so we can interface with the Halite engine
import hlt
# Then let's import the logging module so we can print out information
import logging
import random
import time

# GAME START
# Here we define the bot's name as Settler and initialize the game, including communication with the Halite engine.
game = hlt.Game("Settler")
# Then we print our start message to the logs
logging.info("Starting my Settler bot!")

def neutral_planets(all_planets):
    """
    Are there any neutral planets to capture?
    """
    owned=0
    for planet in all_planets:
            # If the planet is owned
            if planet.is_owned():
                owned+=1
                continue
    return ( owned < len(all_planets))

def find_leader(all_planets,all_players):
    """
    Figure out which non self player is leading by ship count
    """
    x = {}
    
    for player in all_players:
        playerid=player.id
        player_ships=player.all_ships()
        player_planets=0
        for planet in all_planets:
            if planet.is_owned() and player.id == planet.owner:
                player_planets+=1
        healthy_player_ships=[s for s in player_ships if s.health > 0]
        ship_count=len(healthy_player_ships)
        if playerid != game_map.my_id:
            x[playerid]=ship_count+player_planets
    return max(x, key=x.get)

def nearby_docker(myship,all_players):
    """
    Locate a nearby ship docked or docking
    """
    for player in all_players:
        playerid=player.id
        player_ships=player.all_ships()
        if playerid != game_map.my_id:
            for ship in player_ships:
                if (ship.docking_status == ship.DockingStatus.DOCKING) and myship.calculate_distance_between(ship) <= 10:
                    return ship
                if (ship.docking_status == ship.DockingStatus.DOCKING) and myship.calculate_distance_between(ship) <= 15 and ship.health < 255:
                    return ship
                if (ship.docking_status == ship.DockingStatus.DOCKING) and myship.calculate_distance_between(ship) <= 20 and ship.health < 128:
                    return ship
                if (ship.docking_status == ship.DockingStatus.DOCKED) and myship.calculate_distance_between(ship) <= 10:
                    return ship
                if (ship.docking_status == ship.DockingStatus.DOCKED) and myship.calculate_distance_between(ship) <= 15 and ship.health < 255:
                    return ship
                if (ship.docking_status == ship.DockingStatus.DOCKED) and myship.calculate_distance_between(ship) <= 20 and ship.health < 128:
                    return ship
    return False

turn_count=0
while True:
    turn_count+=1
    start_time=time.time()
    end_time=start_time+1.6
    logging.info("TURN COUNT:")
    logging.info(turn_count)
    # TURN START
    # Update the map for the new turn and get the latest version
    game_map = game.update_map()

    # Here we define the set of commands to be sent to the Halite engine at the end of the turn
    command_queue = []
    # For every ship that I control
    my_ships=game_map.get_me().all_ships()
    #ship_count=len(my_ships)
    #logging.info("SHIP COUNT")
    #logging.info(ship_count)
    for ship in my_ships:
        all_players=game_map.all_players()
        if nearby_docker(ship,all_players):
            logging.info("NEARBY DOCKED/DOCKING SHIP")
            logging.info(ship.id)
            my_speed=int(hlt.constants.MAX_SPEED)
            navigate_command = ship.navigate(
                ship.closest_point_to(ship),
                game_map,
                speed=my_speed,
                max_corrections=18,
                angular_step=5,
                ignore_ships=False,
                ignore_planets=False)
            if navigate_command:
                command_queue.append(navigate_command)
            else:
                break 
            continue
        # If the ship is docked
        if ship.docking_status != ship.DockingStatus.UNDOCKED or time.time()>end_time :
            # Skip this ship
            continue

        # For each planet in the game (only non-destroyed planets are included)
        all_planets=game_map.all_planets()
        # all_planets.sort(key=lambda x: x.radius, reverse=True)
        all_planets.sort(key=lambda x: ship.calculate_distance_between(x))
        if neutral_planets(all_planets) and (turn_count < 100 or ship.id %10 < 5 or ship.health < 128 ):
            for planet in all_planets:
                # If the planet is owned
                if (planet.is_owned() and planet.owner.id != game_map.my_id) or (planet.is_owned() and planet.is_full() and planet.owner.id == game_map.my_id):
                    # Skip this planet
                    #logging.info("PLANET OWNER")
                    #logging.info(planet.owner.id)
                    continue

                # If we can dock, let's (try to) dock. If two ships try to dock at once, neither will be able to.
                if ship.can_dock(planet):
                    # We add the command by appending it to the command_queue
                    command_queue.append(ship.dock(planet))
                    logging.info("ATTEMPTING TO DOCK SHIP ID")
                    logging.info(ship.id)
                    logging.info("PLANET ID")
                    logging.info(planet.id)
                else:
                    # If we can't dock, we move towards the closest empty point near this planet (by using closest_point_to)
                    # with constant speed. Don't worry about pathfinding for now, as the command will do it for you.
                    # We run this navigate command each turn until we arrive to get the latest move.
                    # Here we move at half our maximum speed to better control the ships
                    # In order to execute faster we also choose to ignore ship collision calculations during navigation.
                    # This will mean that you have a higher probability of crashing into ships, but it also means you will
                    # make move decisions much quicker. As your skill progresses and your moves turn more optimal you may
                    # wish to turn that option off.
                    if turn_count <=4:
                        my_speed=int(hlt.constants.MAX_SPEED/2)
                        ignore_ship=False
                        ignore_planet=False
                    else:
                        my_speed=int(hlt.constants.MAX_SPEED)
                        ignore_ship=False
                        ignore_planet=False
                    navigate_command = ship.navigate(
                        ship.closest_point_to(planet),
                        game_map,
                        speed=my_speed,
                        max_corrections=18,
                        angular_step=5,
                        ignore_ships=ignore_ship,
                        ignore_planets=ignore_planet)
                    # If the move is possible, add it to the command_queue (if there are too many obstacles on the way
                    # or we are trapped (or we reached our destination!), navigate_command will return null;
                    # don't fret though, we can run the command again the next turn)
                    if navigate_command:
                        command_queue.append(navigate_command)
                    else:
                        break
                break
        else:
            all_players=game_map.all_players()
            leader=find_leader(all_planets,all_players)
            logging.info("LEADER")
            logging.info(leader)
            #all_planets.sort(key=lambda x: ship.calculate_distance_between(x))
            all_planets.sort(key=lambda x: x.radius)
            for planet in all_planets:
                logging.info("WAR TIME")
                if planet.is_owned() and planet.owner.id == leader:
#                    logging.info("PLANET OWNER")
#                    logging.info(planet.owner.id)
                    navigate_command = ship.navigate(
                        ship.closest_point_to(planet),
                        game_map,
                        speed=int(hlt.constants.MAX_SPEED),
                        max_corrections=18,
                        angular_step=5,
                        ignore_ships=True,
                        ignore_planets=False)
                    if navigate_command:
                        command_queue.append(navigate_command)
                    else:
                        break
                else:
                    continue
                break

    # Send our set of commands to the Halite engine for this turn
    game.send_command_queue(command_queue)
    # TURN END
# GAME END
