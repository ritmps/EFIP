import random
import time
import UnityEngine as ue

count = 0
while count < 10:
    x = random.randrange(0, 5, 1)
    y = random.randrange(0, 5, 1)
    z = random.randrange(0, 5, 1)

    coord = (x, y, z)
    vector = ue.Vector3(coord[0], coord[1], coord[2])
    objects = ue.Object.FindObjectsOfType(ue.GameObject)
    for parents in objects:
        if parents.name == 'puck2':
            parents.transform.position = vector
            ue.Debug.Log(str(parents.transform.position))
            #time.sleep(1)
            count += 1
