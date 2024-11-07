import random

def get_follower_count(platform):
    if platform == 'Twitter':
        return random.randint(1000, 10000)
    elif platform == 'Instagram':
        return random.randint(5000, 20000)
    elif platform == 'Youtube':
        return random.randint(10000, 50000)
    return 0