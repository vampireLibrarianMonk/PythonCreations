# This is a test task for the multiprocessing menu
# Change all taskThree instances to the next number for seperate menu tab creation

# Modules for test
import os, random, time

# Define preproces variable
def pre_ProcessVariable():
    return False

# Define preprocess keys
def resultsKey():
    return 'Random Task Number | Random Decimal One | Random Decimal Two | Random Decimal Three'

# Define preprocess keys
def errorsKey():
    return 'Random Task Number | Error Message'

# Task One Fix Function
def taskThreeFix(variableList, destinationFolder, preProcessVariable, logOnly, queue):
    for variable in variableList:
        number = random.randint(0, 1000)

        # Random sleep time for simulating processing of different types of objects
        time.sleep(random.randint(1, 10))

        # Create random decimal to 3 places
        randomDecimalOne = str(random.randint(2, 6) * random.randint(1, 7) * float(str(random.randint(1, 9)) + "."\
                                                                         + str(random.randint(1, 9))\
                                                                         + str(random.randint(1, 9))\
                                                                         + str(random.randint(1, 9))))

        # Create random decimal to 3 places
        randomDecimalTwo = str(random.randint(2, 6) * random.randint(1, 7) * float(str(random.randint(1, 9)) + "."\
                                                                         + str(random.randint(1, 9))\
                                                                         + str(random.randint(1, 9))\
                                                                         + str(random.randint(1, 9))))

        # Create random decimal to 3 places
        randomDecimalThree = str(random.randint(2, 6) * random.randint(1, 7) * float(str(random.randint(1, 9)) + "."\
                                                                         + str(random.randint(1, 9))\
                                                                         + str(random.randint(1, 9))\
                                                                         + str(random.randint(1, 9))))
        # Simulate a 20 percent error rate
        if number > 200:
            queue.put('taskThreeFix' + 'randTask-' + str(number) + '\t' + randomDecimalOne + '\t' + randomDecimalTwo\
                   + '\t' + randomDecimalThree + '\t' + 'This was a random task that multi menu is processing.')
        else:
            queue.put('taskThreeFix' + 'Error: ' + 'randTask-' + str(number) + ' experienced an error.')
