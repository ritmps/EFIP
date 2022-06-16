import UnityEngine as ue
x = 1.0
y = 3.0
z = 4.0
vector = ue.Vector3(x, y, z)
objects = ue.Object.FindObjectsOfType(ue.GameObject)
for parents in objects:
    if parents.name == 'puck2':
        parents.transform.position = vector

        ue.Debug.Log(parents.name)
        # parents.transform.position += parents.transform.position.up * 10
        ue.Debug.Log(str(parents.transform.position))
