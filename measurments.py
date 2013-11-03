import random

def getDropProbability():
    dropProbability = raw_input("Enter the packet loss probability: ")
    try:
        while (float(dropProbability) > 1 or float(dropProbability) < 0):
            print 'a'
            dropProbability = raw_input("That wasn't valid, please try again: ")
    except ValueError, e:
        print "That input was invalid, exiting now."
        exit()
    return float(dropProbability)

def dropOrKeepPacket(dropProbability):
    if (random.random() < dropProbability):
        return True
    else:
        return False
