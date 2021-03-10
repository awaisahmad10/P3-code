'''
ENGINEER 1P13 - Project 3 - Mon 15
Authors: Boran Seckin, Awais Ahmad
'''

import time
import random
import sys
sys.path.append('../')

from Common_Libraries.p3b_lib import *

import os
from Common_Libraries.repeating_timer_lib import repeating_timer

def update_sim():
    try:
        my_table.ping()
    except Exception as error_update_sim:
        print (error_update_sim)

### Constants
speed = 0.2 #Qbot's speed

### Initialize the QuanserSim Environment
my_table = servo_table()
arm = qarm()
arm.home()
bot = qbot(speed)

##---------------------------------------------------------------------------------------
## STUDENT CODE BEGINS
##---------------------------------------------------------------------------------------

# Global variable to offset the dropoff locations on QBot
dropoff_counter = 0

def dispense_container():
    '''
    Dipsenses a random container onto the sorting table.
    Returns the properties of the container as a tuple in the form of (material, weight, binID).
    Author: Awais Ahmad
    '''
    # Pick a random container to dispense
    props = my_table.container_properties(random.randint(1,6))
    # Dispense the container
    my_table.dispense_container()
    print(f'Container has been dispensed!')

    return props


def load_container():
    '''
    Pickups the container from the sorting table and loads it onto QBot using QArm.
    For each run, it will load the containers (if there are more than one) to
    a specific spot on QBot starting from right and ending on the left.
    Author: Boran Seckin
    '''
    # Global variable to offset the dropoff locations on QBot
    global dropoff_counter

    PICKUP_POS = (0.6915, 0.0, 0.2604)
    
    # 3 different positions on QBot for placing the containers
    MID_POS = (0.0, -0.3972, 0.4051)
    RIGHT_POS = (-0.1359, -0.3733, 0.4051)
    LEFT_POS = (0.1028, -0.3837, 0.4051)
    DROPOFF_POS = [RIGHT_POS, MID_POS, LEFT_POS]

    # Move arm to the pickup postition
    arm.move_arm(*PICKUP_POS)
    time.sleep(0.5)
    # Close the gripper to pick up the container
    arm.control_gripper(45)
    # Move arm to the dropoff postition
    arm.move_arm(*DROPOFF_POS[dropoff_counter])
    time.sleep(0.5)
    # Open the gripper to drop off the container
    arm.control_gripper(-25)
    time.sleep(0.5)
    # Move QArm back so it doesn't hit the container(s)
    arm.rotate_shoulder(-40)
    arm.control_gripper(-20)
    # Return back to home position
    arm.home()

    # Increase the counter by one to offset the next container
    dropoff_counter += 1

    print('Container has been loaded to QBot!')
    return None


def transfer_container(binID):
    '''
    Transfers the container(s) to the bin supplied as the argument.
    It uses the ultrasonic sensor to align QBot with the target bin.
    Accepts a string representing the target bin ID in the form of
    "Bin0X" where "X" is the bin ID.
    Author: Boran Seckin
    '''
    # Turn on the ultrasonic sensor
    bot.activate_ultrasonic_sensor()

    # Rotate Qbot 180 degrees to face the bins
    # Do it in two steps to reduce the speed
    bot.rotate(-90)
    bot.rotate(-90)
    time.sleep(0.5)

    # Keeps track off the lost lines
    lost_line = 0

    # While QBot still sees a line to follow
    while lost_line < 2:
        # Run the image processing algorithm to follow the line with 0.5 speed
        lost_line, velocity = bot.follow_line(0.5)
        
        # Get the distance from the target bin using the ultrasonic sensor
        distance = bot.read_ultrasonic_sensor(binID)
        print(f'Distance: {distance}')
        
        # If the distance is less than or equal to 0.03, break of the loop
        # 0.03 is not perfect but it is the closest value Qbot can read from the bins
        if distance <= 0.03:
            print('break', distance)
            break

        # Move QBot using the values from the follow_line
        bot.forward_velocity(velocity)

    # Stop QBot and disable the ultrasonic sensor
    bot.stop()
    bot.deactivate_ultrasonic_sensor()

    # Move Qbot for 0.1 seconds to better align with the bin
    bot.forward_time(0.1)

    print(f'QBot has reached the {binID}!')
    return None


def deposit_container():
    '''
    Deposits the container using the actuator on QBot.
    Author: Awais Ahmad
    '''
    # Dump the containers
    bot.activate_actuator()
    bot.dump()
    bot.deactivate_actuator()

    print('Qbot deposited the container(s)!')
    return None


def return_home():
    '''
    Using the line following algorithm, completes the course and goes to home position.
    Author: Awais Ahmad
    '''
    # Keeps track off the lost lines
    lost_line = 0

    # While QBot still sees a line to follow
    while lost_line < 2:
        # Run the image processing algorithm to follow the line with 0.5 speed
        lost_line, velocity = bot.follow_line(0.5)
        # Move QBot using the values from the follow_line
        bot.forward_velocity(velocity)

    # Stop QBot
    bot.stop()

    # Because QBot loses the line when it gets close to the end,
    # use the depth sensor to go as close as possible to the wall
    # From experiment, we found that the depth sensor cannot
    # accurately measure values less than 0.14
    bot.travel_forward(0.14)

    print('Qbot returned home!')
    return None


def main():
    '''
    Authors: Boran Seckin, Awais Ahmad
    '''
    # Keeps track of the dispensed but not loaded containers
    is_table_empty = True
    # Keeps track of the recently dispensed container 
    props = None

    # Global variable to offset the dropoff locations on QBot
    global dropoff_counter

    # Infinite loop to repeat the objective forever
    while True:
        # List of containers that are loaded on QBot 
        on_Qbot = []
        # Total weight loaded on QBot
        total_weight = 0

        # While there are less than 3 containers
        while len(on_Qbot) < 3:
            # If the table is not empty, do not dispense a new container
            if is_table_empty:
                # Dispense a new container and save its properties
                props = dispense_container()
                # Mark the table as occupied
                is_table_empty = False
                print(props)

            # If this is the first container, just load it
            # and continue with the next iteration
            if (len(on_Qbot) == 0):
                print('First container, loading!')
                load_container()
                # Mark the table as empty
                is_table_empty = True

                # Add the recently loaded container on the list 
                on_Qbot.append(props)
                # Increase the total weight
                total_weight += props[1]

                time.sleep(1)
                # Continue with the next iteration
                continue
            
            # If the new container has the same binID as the first container
            # and the total weight with the new container is less than 90, load the new container
            if (props[2] == on_Qbot[0][2] and (total_weight + props[1]) < 90):
                print('Same bin detected, loading!')
                load_container()
                # Mark the table as empty
                is_table_empty = True

                # Add the recently loaded container on the list 
                on_Qbot.append(props)
                # Increase the total weight
                total_weight += props[1]

                time.sleep(1)
            else:
                print('Different bin/too much weight detected, not loading!')
                # If one of the conditions above is not met, break the loop
                break

        # Reset the counter to 0, so the next dropoff is on the right side
        dropoff_counter = 0

        # Transfer container(s) to the first container's bin
        transfer_container(on_Qbot[0][2])
        time.sleep(1)
        deposit_container()
        time.sleep(1)
        return_home()


main()

##---------------------------------------------------------------------------------------
## STUDENT CODE ENDS
##---------------------------------------------------------------------------------------
update_thread = repeating_timer(2,update_sim)
